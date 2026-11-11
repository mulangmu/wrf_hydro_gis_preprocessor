# 湄公河 MEK90M 湖泊拆分版产物说明文档

**适用产物**：`MEK90M_reach_rf10_nf200_fcst_lakes_2016_split.zip` 与 `MEK90M_reach_rf10_nf200_fcst_lakes_2000_split.zip`
**生成日期**：2026-10-24　|　**生成环境**：conda 环境 `wrfh_gis`（Python 3.10.22 / GDAL 3.11.4）
**工具版本**：`mulangmu/wrf_hydro_gis_preprocessor` master 分支 commit `77c6c7e3`（含 `--lake-join` 补丁）

---

## 1. 这两份产物是什么

两套 WRF-Hydro reach-based 汇流输入堆栈（routing stack），基于 GRanD v1.3 湄公河流域水库数据，分别代表 **2000 年前建成（19 座）** 与 **2016 年前建成（37 座）** 的水库情景。与早期产物（`_2000_v2`、`_2016`）的本质区别：**串联湖（梯级水库）不再被自动合并，每座水库作为独立湖泊保留各自的演算参数**。

| | lakes_2000_split | lakes_2016_split |
|---|---|---|
| 输入水库数 | 19（GRanD before2000） | 37（GRanD before2016） |
| 栅格阶段存活 | 17（丢 2 座，见 §6.2） | 34（丢 3 座） |
| 矢量阶段连接 | 17/17 全连接 | 34/34 全连接 |
| **串联湖合并** | **0 组** | **0 组** |
| **最终 LAKEPARM / lakes.shp** | **17 座** | **34 座** |
| Route_Link 关联河段 | 135 条（覆盖全部 17 湖） | 346 条（覆盖全部 34 湖） |
| 河段总数 | 7,019 | 7,017 |

---

## 2. 背景：为什么需要"拆分"

### 2.1 工具的串联湖合并行为

WRF-Hydro GIS Preprocessor 的 `Lake_Link_Type`（wrfhydro_functions.py:3928-3969）在处理湖泊时，若发现 **B 湖的入流河段已属于 A 湖**（A、B 多边形沿河相接、中间无自由河段），会递归把整条链的湖全部改标为最下游湖的 ID。其根源是 RouteLink 数据模型约束：**每条河段的 `NHDWaterbodyComID` 只能属于一个湖**，且回水相接的梯级库会争抢同一条连接河段。

### 2.2 合并的代价（拆分动机）

- 上游水库从 lakes.shp / LAKEPARM 中消失；
- 合并湖**只保留最下游库自己的参数**：合并版中糯扎渡（246 km²）+ 大朝山（21 km²）被景洪（24.5 km²）的参数代表，小湾（152 km²）+ 功果桥（10 km²）被漫湾（36 km²）代表——大库的调蓄库容被严重低估。
- 不能简单用开关关闭合并：冲突河段只归一湖后，另一湖因"无 type 1 出流河段"会被**整个剔除**，结果更糟。

### 2.3 拆分方案（数据层面）

对上游库多边形的下游端做裁退，在两库之间留出一段**自由河道**（不属于任何湖、也不与两湖的河段直接拓扑相邻）。判定标准（对照实际派生河网逐项验证）：

1. **无共享河段**：没有任何一条河段折线同时穿过两个湖多边形；
2. **无拓扑相邻**：不存在 A 的河段经 `to` 关系直接流向 B 的河段（这是合并的真正触发条件——即使两湖相距 20 km，一条 15 km 的无节点长河段也可能桥接两湖触发合并）。

裁剪距离 3→30 km 渐进加大，先单侧（只裁上游库），失败则双侧对称裁；用**最近一轮运行的实际 streams.shp** 做校验（WhiteboxTools 每轮重推河网有微小漂移，旧网络验证过的空隙可能被新一轮桥接，需迭代）。

---

## 3. 拆分明细

### 3.1 lakes_2016_split（7 组冲突对）

| 被裁库（上游） | 下游库 | 空隙 | 面积变化 (km²) | 方式 |
|---|---|---|---|---|
| 功果桥 Gongguoqiao (id28) | 小湾 Xiaowan (id37) | 22 km | 9.5 → 4.2 | 双侧（小湾尾端 151.9→146.6） |
| 大朝山 Dachaoshan (id27) | 糯扎渡 Nuozhadu (id36) | 14 km | 20.1 → 16.6 | 单侧 |
| 糯扎渡 Nuozhadu (id36) | 景洪 Jinghong (id32) | 18 km | 241.9 → 238.4 | 单侧 |
| Plei Krong (id34) | Yali (id20) | 11 km | 44.0 → 15.4 | 双侧（Yali 45.5→32.1） |
| Sirindhorn (id18) | Pak Mun (id17) | 26 km | 235.5 → 82.9 | 单侧 |
| Nam Ngum 2 (id23) | Nam Ngum (id4) | 14 km | 92.5 → 64.9 | 单侧 |
| 小湾 Xiaowan (id37) | 漫湾 Manwan (id3) | 22 km | 151.9 → 60.2 | 单侧 |

### 3.2 lakes_2000_split（仅 1 组冲突对）

| 被裁库（上游） | 下游库 | 空隙 | 面积变化 (km²) | 方式 |
|---|---|---|---|---|
| Sirindhorn (id18) | Pak Mun (id17) | 22 km | 235.5 → 122.1 | 单侧 |

> 注：Sirindhorn 在 2016 版需 26 km、2000 版 22 km——两版用不同轮次的河网验证，所需的临界空隙略有差异；两版最终均在实际运行中零合并。

**物理含义**：被裁掉的库尾水面（如 Sirindhorn 的 Mun 河连接段、小湾的库尾）在模型中改按**天然河道**演算（Muskingum），两坝之间不再是连续水面。这是把回水相接的梯级库拆成独立水库的固有代价，换来的是每座库用自己的面积/高程/泄流参数参与演算。

---

## 4. 生成命令

```
# 2016 拆分版
python Build_Routing_Stack.py -i mekong_wps_gis\geo_em.d01.nc ^
    --CSV mekong_wps_gis\mekong_frxst_pts_rf10_nr100_csv.csv ^
    -b True -r True -l mekong_wps_gis\before2016\GRanD_reservoirs_v1_3_Mekong_split.shp ^
    -d mekong_wps_gis\Mekong_hydroshed_DEM90m.tif ^
    -R 10 -t 200 -O 1.0 -T 1.0 --lake-join line ^
    -o Outputs\MEK90M_reach_rf10_nf200_fcst_lakes_2016_split.zip

# 2000 拆分版（仅 -l 与 -o 不同）
python Build_Routing_Stack.py -i mekong_wps_gis\geo_em.d01.nc ^
    --CSV mekong_wps_gis\mekong_frxst_pts_rf10_nr100_csv.csv ^
    -b True -r True -l mekong_wps_gis\before2000\GRanD_reservoirs_v1_3_Mekong_2000_split.shp ^
    -d mekong_wps_gis\Mekong_hydroshed_DEM90m.tif ^
    -R 10 -t 200 -O 1.0 -T 1.0 --lake-join line ^
    -o Outputs\MEK90M_reach_rf10_nf200_fcst_lakes_2000_split.zip
```

关键参数含义：`-b True` CHANNELGRID 掩膜到 6 个预报断面流域；`-r True` 生成 RouteLink（reach-based）；`-R 10` 由 5 km geogrid 加密 10 倍到 500 m 汇流网格；`-t 200` 河道起始阈值（200 格点 = 50 km²）；`--lake-join line` 用河段折线与湖相交建立连接（能救回湖位于河段中部的库，`point` 模式只认河段起点节点落在湖内）。

---

## 5. 产物内容与核验结果

### 5.1 zip 内容清单（两版结构相同）

| 文件 | 说明 |
|---|---|
| Fulldom_hires.nc | 500 m 高分辨率全域文件（TOPOGRAPHY/FLOWDIRECTION/FLOWACC/CHANNELGRID/STREAMORDER/LATITUDE/LONGITUDE/LINKID 等）。**reach 模式下 LAKEGRID 全为 -9999（工具设计行为，非错误）**；CHANNELGRID 约定 **0=河道格点、-9999=非河道** |
| Route_Link.nc | 河段参数表；`NHDWaterbodyComID` 为河段-湖泊关联（135/346 条非空） |
| LAKEPARM.nc | **17 / 34 座湖**的独立参数（LkArea、LkMxE、OrificeE/C、WeirE/C/L 等） |
| lakes.shp | 最终保留的湖泊多边形（模型投影 LCC 球面），`newID` = lake_id |
| streams.shp | 河段折线（含 link、LakeID 字段） |
| GWBASINS.nc / GWBUCKPARM.nc | 地下水.bucket 输入 |
| GEOGRID_LDASOUT_Spatial_Metadata.nc | 网格空间元数据 |
| Gage_Crosswalk.csv | 预报点-河段对应 |
| Lake_Problems.csv | 湖泊问题记录（均为提示性：headwater 无入流、多出口警示等，**无合并类记录**） |
| Old_New_LakeComIDs.csv | **空文件 = 零合并**（合并版这里会有 34→20 之类的映射） |
| Lake_Link_Types.csv / Tossed_Lake_Link_Types.csv | 河段-湖泊角色（1=出流、2=库内、3=入流） |

### 5.2 与早期版本对比

**2000 年情景**

| 版本 | LAKEPARM 湖数 | 特征 |
|---|---|---|
| `_2000.zip`（原始） | 0 | GDAL netCDF 矢量驱动坐标系 bug，lakes.shp 为空（已修复，留档对照） |
| `_2000_v1.zip`（point） | 12 | 起点节点判定，13 湖连接，18 并入 17 |
| `_2000_v2.zip`（line） | 16 | 17 湖全连接，但 18 并入 17 |
| **`_2000_split.zip`** | **17** | **全连接、零合并，Sirindhorn 以 122.1 km² 独立演算** |

**2016 年情景**

| 版本 | LAKEPARM 湖数 | 特征 |
|---|---|---|
| `_2016.zip`（line 合并版） | 27 | 7 座并入 5 座；糯扎渡被景洪 24.5 km² 参数代表 |
| **`_2016_split.zip`** | **34** | **零合并；糯扎渡 238.4、小湾 60.2、Sirindhorn 82.9 km² 各自独立** |

拆分版保留湖 id：2000 版 [3–19]；2016 版 [3–37]（缺 1、2、33，见 §6.2）。

---

## 6. 已知限制与使用注意

### 6.1 模型配置
- 在 hydro.namelist 中启用湖泊模块（`LAKES = 1`），湖泊经 Route_Link.nc 的 `NHDWaterbodyComID` 关联河段参与汇流；reach-based 湖泊演算还需要按所用 WRF-Hydro 版本配置相关选项（如 `UDMP_OPT`，以官方手册为准）。
- 两版 Lake_Problems.csv 中的 "Headwater lake, no inflows"（2000 版 5 座、2016 版 7 座）是提示性记录，湖仍保留并参与演算。

### 6.2 栅格阶段被剔除的库（两版共同行为，非拆分引起）
判定标准：湖多边形栅格化后必须覆盖至少一个 CHANNELGRID 河道格点。被剔除者：

| 库 | 面积 | 原因 |
|---|---|---|
| Haixihai | 4.0 km² | 派生河道偏了约 250 m，未穿过库区；流经它的水流 FACmax=149 < 200 阈值 |
| Zibihe | 7.9 km² | 河道只擦到库边界；湖内 FACmax=176 < 200 |
| Krong Buk Ha（仅 2016 版） | 10.2 km² | 完全不在派生河网上（距最近河段 22.5 km，湖内 FAC=0） |

若需纳入前两座，可将 `-t` 降到 ≤149（如 100）重跑——代价是全域河网显著加密。Krong Buk Ha 无法通过降阈值纳入。

### 6.3 重生成时的注意（WhiteboxTools 漂移）
每次重跑都会重新推导地形/河网（河段数有 ±0.5% 的运行间波动）。若重跑后 `Old_New_LakeComIDs.csv` 不再为空（个别长河段重新桥接了两库间隙），用 `F:\mekong\wrf_hydro_wps\split_lakes.py`（2016）/ `split_lakes_2000.py`（2000）以**最新一轮**的 streams.shp 重新校验/加大空隙后再跑，一般 1–2 轮收敛。脚本输出目录：`mekong_wps_gis\before20XX\GRanD_reservoirs_v1_3_Mekong[_2000]_split.shp` 与 `GRanD_split_report[_2000].csv`。

### 6.4 Route_Link.nc 坐标使用提示
文件中的 `lat/lon`（start node）来自 5 km geogrid 双线性插值，与投影坐标 `x/y` 中位偏差 3.4 km（最大 30 km）。任何后处理空间分析请用 `x/y`（精确网格坐标），不要用 `lat/lon`。

---

## 7. 文件位置总览

| 类别 | 路径 |
|---|---|
| 产物 zip + 运行日志 | `wrfhydro_gis\Outputs\MEK90M_reach_rf10_nf200_fcst_lakes_2016_split.zip / .log` |
| | `wrfhydro_gis\Outputs\MEK90M_reach_rf10_nf200_fcst_lakes_2000_split.zip / .log` |
| 拆分后湖泊数据 | `wrfhydro_gis\mekong_wps_gis\before2016\GRanD_reservoirs_v1_3_Mekong_split.shp`（+ `GRanD_split_report.csv`） |
| | `wrfhydro_gis\mekong_wps_gis\before2000\GRanD_reservoirs_v1_3_Mekong_2000_split.shp`（+ `GRanD_split_report_2000.csv`） |
| 原始 GRanD 数据（未改动） | `mekong_wps_gis\before2016\GRanD_reservoirs_v1_3_Mekong.shp`、`before2000\GRanD_reservoirs_v1_3_Mekong_2000.shp` |
| 拆分脚本 | `F:\mekong\wrf_hydro_wps\split_lakes.py`（2016）、`split_lakes_2000.py`（2000） |
| 本文档 | `wrfhydro_gis\Outputs\Lakes_Split_Documentation.md` |

（所有路径相对 `F:\mekong\wrf_hydro_wps\wrf_hydro_gis_preprocessor-master\`）
