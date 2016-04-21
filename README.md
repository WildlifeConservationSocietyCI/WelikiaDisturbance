# WelikiaDisturbance
Integrated fire and horticulture disturbance modeling
## Requirements ##
Python 2.7.10 [MSC v.1500 64 bit (AMD64)]


[GDAL 2.0.2 x64 bindings](http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)

pywinauto is dependent on pywin32 pip install did not work for me but this did

[pywin32-214.win-amd64-py3.0.exe](https://sourceforge.net/projects/pywin32/files/pywin32/Build%20214/)
## Settings
This file contains the key parameters for each of the disturbance classes.
## Fire
The fire script calls FARSITE a fire simulation model and runs a trial, the outputs of the trial are used to update time_since_disturbance and canopy rasters, which subsequently become inputs for the successional model 
### Inputs
####Spatial
- ecosystems
- elevation.asc
- slope.asc
- aspect.asc
- canopy.asc
- fuel.asc
- trails.asc
- ignition.vct
 
####Tabular
- weather.wtr
- wind.wnd
- fuel_adjustments.adj
- custom_fuel.fmd
- fuel_moisture.fms
- translation_table.txt

## Ponds 
The pond class adds ponds to the shared ecosystem raster. 
### Inputs
 - Hydrologically conditioned DEM with burned streams
 - flow direction
 - suitable streams
 - ecosystems
 
## Garden
Garden class uses a cellular growth method to add horticultural fields to the ecosystem raster.
### Inputs
####Spatial
- ecosystems
- slope_suitablity
- proximity_suitability
- sites.shp

####Tabular
- ecosystem_reclasiffy_table

