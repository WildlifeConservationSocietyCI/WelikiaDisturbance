# WelikiaDisturbance
Integrated fire and horticulture disturbance modeling
## Requirements ##

ESRI python distribution which contains arcpy library ([license information](https://docs.google.com/document/d/1Mene0tUbbVP063KYKkhCV-sOWz3elkcMEq0bak3vxtE/edit#))

64-bit Background Geoprocessing Python 2.7.10 [MSC v.1500 64 bit (AMD64)]

####GDAL

*Download GDAL*
[GDAL 2.0.2 x64 bindings](http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)

save this file in the folder that contains the version of python you are using

*Install Directions*

1. Using the command line navigate to the directory containg both the GDAL.whl and python.exe
2. use the following command:

 ```
 python.exe -m pip intall GDAL-2.0.2-cp27-none-win_amd64.whl
 ```

3. If pip installation is successful, open IDE or console and test gdal import

#### pywinauto
pywinauto is dependent on pywin32 pip install did not work for me but this did
[pywin32-214.win-amd64-py3.0.exe](https://sourceforge.net/projects/pywin32/files/pywin32/Build%20214/)

#### FARSITE
[FARSITE 4.1.055](http://www.firelab.org/document/farsite-software)



## Fire ##
The fire class uses [FARSITE]() to simulate the historical burning regime. Fire spread is modeled by FARSITE and the outputs of burning events are used to update time_since_disturbance, forest age and canopy rasters. Changes to these rasters are then used to modify ecosystem type.

### Inputs ###
 - elevation.asc
 - slope.asc
 - aspect.asc
 - canopy.asc
 - fuel.asc

## Ponds 
The pond class adds ponds to the ecosystem raster by flooding the DEM at randomly created dam points. Pond shape is determined by topography (flow direction -> watershed) and dam hieght (flooding depth). Location of ponds is random along the paths of mapped streams. Density is determined by a minimum territory distance parameter (1000 m).  

### Inputs
 - Hydrologically conditioned DEM with burned streams
 - flow direction
 - suitable streams
 
## Gardens
This class uses a cellular growing method to add gardens to the ecosystem raster. Garden placement at the landscape scale is determined by the location of sites (ethnohistorical, cartagraphic, archaological records). At the local scale gardens are postioned based on horticultural suitability (slope, ecosystem, proximity to habitation site).

### Inputs

## Successional Model ##
### Inputs ###
