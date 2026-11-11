# MEK90M 全部产物运行命令参考

运行前准备（Anaconda Prompt）：

```
conda activate wrfh_gis
cd F:\mekong\wrf_hydro_wps\wrf_hydro_gis_preprocessor-master\wrfhydro_gis
```

公共参数：`-i` geogrid | `--CSV` 预报点 | `-b True` CHANNELGRID 掩膜到预报流域 | `-R 10` 5km→500m | `-t 200` 河道阈值 | `-O/-T` 1.0
`-r True` = reach-based（RouteLink）；`-r False` = gridded。`--lake-join` 仅 reach 模式有效（point=河段起点判定 / line=河段折线相交）。

## Grid 族（-r False）

```
:: 无水库
python Build_Routing_Stack.py -i mekong_wps_gis\geo_em.d01.nc --CSV mekong_wps_gis\mekong_frxst_pts_rf10_nr100_csv.csv -b True -r False -d mekong_wps_gis\Mekong_hydroshed_DEM90m.tif -R 10 -t 200 -O 1.0 -T 1.0 -o Outputs\MEK90M_grid_rf10_nf200_fcst.zip

:: 2000 年水库（原始数据；gridded 模式无串联合并问题，用完整库面）
python Build_Routing_Stack.py -i mekong_wps_gis\geo_em.d01.nc --CSV mekong_wps_gis\mekong_frxst_pts_rf10_nr100_csv.csv -b True -r False -l mekong_wps_gis\before2000\GRanD_reservoirs_v1_3_Mekong_2000.shp -d mekong_wps_gis\Mekong_hydroshed_DEM90m.tif -R 10 -t 200 -O 1.0 -T 1.0 -o Outputs\MEK90M_grid_rf10_nf200_fcst_lakes_2000.zip

:: 2016 年水库（原始数据；gridded 模式无串联合并问题，用完整库面）
python Build_Routing_Stack.py -i mekong_wps_gis\geo_em.d01.nc --CSV mekong_wps_gis\mekong_frxst_pts_rf10_nr100_csv.csv -b True -r False -l mekong_wps_gis\before2016\GRanD_reservoirs_v1_3_Mekong.shp -d mekong_wps_gis\Mekong_hydroshed_DEM90m.tif -R 10 -t 200 -O 1.0 -T 1.0 -o Outputs\MEK90M_grid_rf10_nf200_fcst_lakes_2016.zip
```

## Reach 族（-r True，当前保留 3 份）

```
:: 无水库
python Build_Routing_Stack.py -i mekong_wps_gis\geo_em.d01.nc --CSV mekong_wps_gis\mekong_frxst_pts_rf10_nr100_csv.csv -b True -r True -d mekong_wps_gis\Mekong_hydroshed_DEM90m.tif -R 10 -t 200 -O 1.0 -T 1.0 -o Outputs\MEK90M_reach_rf10_nf200_fcst.zip

:: 2000 年水库拆分版（line 判定，split 数据）
python Build_Routing_Stack.py -i mekong_wps_gis\geo_em.d01.nc --CSV mekong_wps_gis\mekong_frxst_pts_rf10_nr100_csv.csv -b True -r True -l mekong_wps_gis\before2000\GRanD_reservoirs_v1_3_Mekong_2000_split.shp -d mekong_wps_gis\Mekong_hydroshed_DEM90m.tif -R 10 -t 200 -O 1.0 -T 1.0 --lake-join line -o Outputs\MEK90M_reach_rf10_nf200_fcst_lakes_2000_split.zip

:: 2016 年水库拆分版（line 判定，split 数据）
python Build_Routing_Stack.py -i mekong_wps_gis\geo_em.d01.nc --CSV mekong_wps_gis\mekong_frxst_pts_rf10_nr100_csv.csv -b True -r True -l mekong_wps_gis\before2016\GRanD_reservoirs_v1_3_Mekong_split.shp -d mekong_wps_gis\Mekong_hydroshed_DEM90m.tif -R 10 -t 200 -O 1.0 -T 1.0 --lake-join line -o Outputs\MEK90M_reach_rf10_nf200_fcst_lakes_2016_split.zip
```

## 注意事项

- 必须先 `conda activate wrfh_gis` 再运行：直接调 envs 里的 python.exe 会因缺少 GDAL_DRIVER_PATH/PATH 加载不了 netCDF 插件。
- 重跑 reach 拆分版后检查 `Old_New_LakeComIDs.csv` 是否为空：WhiteboxTools 河网有运行间漂移，若出现合并，用 `F:\mekong\wrf_hydro_wps\split_lakes.py`（2016）/ `split_lakes_2000.py`（2000）以最新河网重新校验裁剪后再跑。
- 每次运行会删除并重建 `Outputs\scratchdir\`；同名 zip 会被覆盖，改名请改 `-o`。
