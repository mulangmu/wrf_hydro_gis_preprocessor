# -*- coding: utf-8 -*-
# 串联湖拆分 —— 2000年版（GRanD_reservoirs_v1_3_Mekong_2000.shp, 19 个库）
# 判据：无共享河段 + 无 to 拓扑相邻；单侧裁失败回退双侧；校验网络用最新运行河网
import os, csv
import netCDF4
from osgeo import ogr, osr
from shapely.wkt import loads as wkt_loads
from shapely.strtree import STRtree

base = r'F:\mekong\wrf_hydro_wps\wrf_hydro_gis_preprocessor-master\wrfhydro_gis'
grand_wgs = base + r'\mekong_wps_gis\before2000\GRanD_reservoirs_v1_3_Mekong_2000.shp'
out_shp = base + r'\mekong_wps_gis\before2000\GRanD_reservoirs_v1_3_Mekong_2000_split.shp'
out_csv = base + r'\mekong_wps_gis\before2000\GRanD_split_report_2000.csv'
tmp = os.path.join(os.environ['TEMP'], 'mek_verify_split')  # 最新一轮(2016_split)的实际河网

lcc = osr.SpatialReference()
lcc.ImportFromProj4('+proj=lcc +lat_0=20.0000305175781 +lon_0=102 +lat_1=30 +lat_2=15 +x_0=0 +y_0=0 +R=6370000 +units=m +no_defs')
wgs = osr.SpatialReference(); wgs.ImportFromEPSG(4326)
for s in (wgs, lcc): s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
fwd = osr.CoordinateTransformation(wgs, lcc)
inv = osr.CoordinateTransformation(lcc, wgs)

ds = ogr.Open(grand_wgs, 0)
lyr = ds.GetLayer(0)
polys, names, areas0 = {}, {}, {}
for f in lyr:
    lid = f.GetFID() + 1
    g = f.GetGeometryRef().Clone(); g.Transform(fwd)
    polys[lid] = wkt_loads(g.ExportToWkt())
    names[lid] = str(f.GetField('DAM_NAME'))
    areas0[lid] = polys[lid].area / 1e6
ds = None
print('读入 {0} 个湖'.format(len(polys)))

st = ogr.Open(os.path.join(tmp, 'streams.shp'), 0)
stl = st.GetLayer(0)
lines, link_ids = [], []
for f in stl:
    lines.append(wkt_loads(f.GetGeometryRef().ExportToWkt()))
    link_ids.append(int(f.GetField('link')))
st = None
tree = STRtree(lines)
rl = netCDF4.Dataset(os.path.join(tmp, 'Route_Link.nc'))
to_map = {int(a): int(b) for a, b in zip(rl.variables['link'][:], rl.variables['to'][:])}
rl.close()

def links_of(poly):
    cand = tree.query(poly)
    return set(link_ids[int(i)] for i in cand if lines[int(i)].intersects(poly))

lake_links = {lid: links_of(p) for lid, p in polys.items()}
had_links = {lid: len(v) > 0 for lid, v in lake_links.items()}
print('有河段穿过的湖:', sorted(l for l in lake_links if lake_links[l]))

def conflict(a, b):
    la, lb = lake_links[a], lake_links[b]
    if la & lb:
        return '共享河段'
    if {to_map.get(x, 0) for x in la} & lb:
        return 'A河段直接流向B河段'
    if {to_map.get(x, 0) for x in lb} & la:
        return 'B河段直接流向A河段'
    return None

all_ids = sorted(polys)
conflict_pairs = []
for i in range(len(all_ids)):
    for j in range(i + 1, len(all_ids)):
        if not (had_links[all_ids[i]] and had_links[all_ids[j]]):
            continue
        c = conflict(all_ids[i], all_ids[j])
        if c:
            conflict_pairs.append((all_ids[i], all_ids[j], c))
print('冲突湖对:')
for a, b, c in conflict_pairs:
    print('  id{0} {1} <-> id{2} {3}: {4}'.format(a, names[a], b, names[b], c))

def is_upstream(A, B):
    la, lb = lake_links[A], lake_links[B]
    frontier, seen = set(la), set(la)
    for _ in range(300):
        nxt = {to_map.get(x, 0) for x in frontier}
        nxt = {x for x in nxt if x and x not in seen}
        if nxt & lb:
            return True
        if not nxt:
            return False
        frontier, seen = nxt, seen | nxt
    return False

pairs = []
for a, b, c in conflict_pairs:
    if is_upstream(a, b):
        pairs.append((a, b))
    elif is_upstream(b, a):
        pairs.append((b, a))
    else:
        pairs.append((a, b)); print('  ! 未判定上下游, 默认裁 {0}'.format(a))

report = []
modified = set()
GAPS = [3000, 5000, 8000, 11000, 14000, 18000, 22000, 26000, 30000]

def try_trim_geometry(a, b, g):
    new = polys[a].difference(polys[b].buffer(g))
    if new.geom_type == 'MultiPolygon':
        new = max(new.geoms, key=lambda x: x.area)
    return new

for up, dn in pairs:
    done = False
    for g in GAPS:
        new = try_trim_geometry(up, dn, g)
        if new.is_empty or new.area < 1e6:
            continue
        keep = lake_links[up]
        lake_links[up] = links_of(new)
        if conflict(up, dn) is None and lake_links[up]:
            polys[up] = new
            modified.add(up)
            report.append((up, names[up], dn, names[dn], g, areas0[up], new.area / 1e6, len(lake_links[up]), '单侧'))
            print('  裁 id{0} {1}: 距 id{2} {3} 空隙{4}km, 面积 {5:.1f}->{6:.1f} km2 (单侧)'.format(
                up, names[up], dn, names[dn], g / 1000, areas0[up], new.area / 1e6))
            done = True
            break
        lake_links[up] = keep
    if done:
        continue
    for g in GAPS:
        new_up = try_trim_geometry(up, dn, g)
        new_dn = try_trim_geometry(dn, up, g)
        if new_up.is_empty or new_up.area < 1e6 or new_dn.is_empty or new_dn.area < 1e6:
            continue
        keep_u, keep_d = lake_links[up], lake_links[dn]
        lake_links[up] = links_of(new_up)
        lake_links[dn] = links_of(new_dn)
        if conflict(up, dn) is None and lake_links[up] and lake_links[dn]:
            polys[up] = new_up
            polys[dn] = new_dn
            modified.add(up)
            modified.add(dn)
            report.append((up, names[up], dn, names[dn], g, areas0[up], new_up.area / 1e6, len(lake_links[up]), '双侧'))
            print('  裁 id{0} {1}: 距 id{2} {3} 空隙{4}km, 面积 {5:.1f}->{6:.1f} km2 (双侧, 下游湖 {7:.1f}->{8:.1f})'.format(
                up, names[up], dn, names[dn], g / 1000, areas0[up], new_up.area / 1e6, areas0[dn], new_dn.area / 1e6))
            done = True
            break
        lake_links[up], lake_links[dn] = keep_u, keep_d
    if not done:
        print('  !! id{0} {1} 裁剪失败'.format(up, names[up]))

bad = 0
for i in range(len(all_ids)):
    for j in range(i + 1, len(all_ids)):
        if had_links[all_ids[i]] and had_links[all_ids[j]]:
            c = conflict(all_ids[i], all_ids[j])
            if c:
                print('!! 仍冲突: {0} <-> {1} ({2})'.format(all_ids[i], all_ids[j], c)); bad += 1
for lid in all_ids:
    if had_links[lid] and not lake_links[lid]:
        print('!! 湖 {0} {1} 裁后无河段'.format(lid, names[lid])); bad += 1
print('全局校验:', '通过' if bad == 0 else '未通过({0})'.format(bad))
if bad:
    raise SystemExit('校验未通过，不写输出')

drv = ogr.GetDriverByName('ESRI Shapefile')
if os.path.exists(out_shp):
    drv.DeleteDataSource(out_shp)
src = ogr.Open(grand_wgs, 0)
slyr = src.GetLayer(0)
out = drv.CreateDataSource(out_shp)
ol = out.CreateLayer('lakes_split', slyr.GetSpatialRef(), ogr.wkbPolygon)
sdef = slyr.GetLayerDefn()
for i in range(sdef.GetFieldCount()):
    ol.CreateField(sdef.GetFieldDefn(i))
for f in slyr:
    lid = f.GetFID() + 1
    nf = ogr.Feature(ol.GetLayerDefn())
    for i in range(sdef.GetFieldCount()):
        nf.SetField(sdef.GetFieldDefn(i).GetName(), f.GetField(i))
    if lid in modified:
        g = ogr.CreateGeometryFromWkt(polys[lid].wkt); g.Transform(inv); nf.SetGeometry(g)
    else:
        nf.SetGeometry(f.GetGeometryRef().Clone())
    ol.CreateFeature(nf)
src = out = None
print('已写出:', out_shp)
with open(out_csv, 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh)
    w.writerow(['被裁湖id', '坝名', '下游湖id', '下游坝名', '空隙m', '原面积km2', '新面积km2', '剩余河段数', '方式'])
    w.writerows(report)
print('已写出:', out_csv)
