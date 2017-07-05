# WelikiaDisturbance
Integrated fire and horticulture disturbance modeling
## Requirements ##

#### Welikia Inputs

[Welikia Inputs](https://drive.google.com/open?id=0ByGEknMOH_xMQWhMR04wUEZ2bjQ)

  - DEM
  - Ecological Communities First Draft
  - NYC Borough Boundaries
  - Lenape Trails
  - Lenape Garden Sites

#### arcpy
ESRI python distribution which contains arcpy library ([WCS license information](https://docs.google.com/document/d/1Mene0tUbbVP063KYKkhCV-sOWz3elkcMEq0bak3vxtE/edit#))

64-bit Background Geoprocessing Python 2.7.10 [MSC v.1500 64 bit (AMD64)]

#### GDAL
[GDAL 2.0.2 x64 bindings](http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)

#### pywinauto
[pywin32-214.win-amd64-py3.0.exe](https://sourceforge.net/projects/pywin32/files/pywin32/Build%20214/)

#### FARSITE
[FARSITE 4.1.055](http://www.firelab.org/document/farsite-software)

## Disturbances

### Fire
This class uses [FARSITE](https://www.firelab.org/project/farsite) to simulate the historical burning regime. Fire spread is modeled by FARSITE and the outputs of burning events are used to calculate tree mortality, update forest age and canopy rasters. Changes to these rasters are then used to modify ecosystem type.

#### Inputs ####
 - elevation.asc
 - slope.asc
 - aspect.asc
 - canopy.asc
 - fuel.asc
 - fire_trails.asc
 - custom_fuel.fmd
 - custom_fuel_test.fmd
 - fuel_adjustment.adj
 - fuel_moisture.fms
 - mannahatta-psdi.txt
 - psdi-years.txt
 - weather.wtr
 - wind.wnd

### Beaver Ponds
This class allows the addition of beaver ponds to the ecosystem raster by flooding the DEM at randomly created dam points. Pond shape is determined by topography (flow direction -> watershed) and dam height (flooding depth). Location of ponds is random along the paths of mapped streams. Density is determined by a minimum territory distance parameter (1000 m).

#### Inputs
 - Hydrologically conditioned DEM with burned streams
 - flow direction
 - suitable streams
 
### Horticulture
This class uses a cell based growing method to add gardens to the ecosystem raster. Garden placement at the landscape scale is determined by the location of sites (identified in the ethnohistorical, cartographic, archaeological records). At the local scale gardens are positioned based on horticultural suitability (slope, ecosystem, proximity to habitation site).

#### Inputs
  - garden_sites.shp
  - lc_reclass.txt
  - proximity_reclass.txt
  - slope_reclass.txt

## Successional Model
This class updates the growth of forest type communities (DBH, age, tree height) and transitions early succesional communities to advanced states using pathways defined in welikia_community_table_int.csv

### Inputs ###
 - welikia_community_table_int.csv
 - basal_area_growth_coeffecients.csv
 - site_index_curve_table.csv

