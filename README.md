# WRF-Hydro GIS Preprocessor

## Description:
The WRF-Hydro GIS Pre-processor provides various scripts and tools for building the geospatial input files for running a WRF-Hydro simulation.

## Necessary Python Packages and Installation Tips

The scripts for the WRF-Hydro GIS Pre-processor rely on several python modules a user will need to install such as numpy, gdal, netCDF4, and Whitebox-Tools. It is highly recommended to use a python distribution such as Miniconda (https://docs.conda.io/en/latest/miniconda.html). The packages and versions tested with this fork (Windows 64-bit, conda-forge channel, environment name `wrfh_gis`, verified 2026-10) are listed below:

| Package        | Version tested                 |
| -------------- | -----------------------------: |
| python         | 3.10.22                        |
| gdal           | 3.11.4                         |
| libgdal-netcdf | 3.11.4                         |
| netcdf4        | 1.7.4                          |
| numpy          | 1.26.4                         |
| pandas         | 2.3.3                          |
| pyproj         | 3.7.1                          |
| shapely        | 2.1.2                          |
| whitebox       | 2.3.6 (bundles WhiteboxTools v2.4.0) |
| xarray         | 2024.3.0                       |

Creating a new, clean `wrfh_gis` environment with these packages can be done easily using the conda package manager:

* In your conda shell, download the component libraries from the conda-forge channel:
  + `conda create -n wrfh_gis -c conda-forge python=3.10 "gdal=3.11" "libgdal-netcdf=3.11" netcdf4 numpy pandas pyproj shapely whitebox xarray packaging`

* To activate this new environment, type the following at the conda prompt
  + `conda activate wrfh_gis`

### Installation tips

* **Always run the scripts from an activated environment** (`conda activate wrfh_gis`). Invoking `...\envs\wrfh_gis\python.exe` directly (without activation) leaves `PATH` and `GDAL_DRIVER_PATH` unset, so the GDAL netCDF plugin does not load and netCDF operations through GDAL will fail.
* The `libgdal-netcdf` package provides the GDAL netCDF driver. Since commit 77c6c7e3, the lake module (`--lake-join`) reads the Route_Link.nc coordinates through the netCDF4 library directly, so this plugin is no longer strictly required for lake processing, but keeping it installed is recommended for general netCDF/GDAL interoperability.
* The conda package `whitebox` bundles the WhiteboxTools command-line binary that the terrain-processing step (depression filling, flow directions/accumulation) drives automatically.

## How to Run Scripts 

### The scripts make use of a function script '\wrfhydro_gis\wrfhydro_functions.py' to pass all functions and selected global parameters parameters to the primary script: 

+ [Build_Routing_Stack.py](https://github.com/NCAR/wrf_hydro_gis_preprocessor/blob/master/wrfhydro_gis/Build_Routing_Stack.py).

In turn, these scripts rely on a set of functions in [wrfhydro_functions.py](https://github.com/NCAR/wrf_hydro_gis_preprocessor/blob/master/wrfhydro_gis/wrfhydro_functions.py). 

### Running Build_Routing_Stack.py to generate the routing grids for a new WRF-Hydro simulation domain

Use `-h` when calling any of the scripts on the command-line, for help information. Provide the required and any optional parameters as arguments. The following steps will excecute a process to generate a minimal set of routing grids for the desired domain. This example assumes use of a Bash shell.

`python Build_Routing_Stack.py -i geo_em.d01.nc -d NED_30m_Croton.tif -R 4 -t 20 -o croton_test.zip`

## NCAR Disclaimer

The National Center for Atmospheric Research (NCAR) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use.  NCAR has relinquished control of the information and no longer has responsibility to protect the integrity , confidentiality, or availability of the information.  Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by NCAR.  The NCAR seal and logo shall not be used in any manner to imply endorsement of any commercial product or activity by NCAR or the National Science Foundation (NSF).
