# WelikiaDisturbance
Integrated fire and horticulture disturbance modeling
## Requirements ##
Python 2.7.10 [MSC v.1500 64 bit (AMD64)]


[GDAL 2.0.2 x64 bindings](http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)

pywinauto is dependent on pywin32 pip install did not work for me but this did

[pywin32-214.win-amd64-py3.0.exe](https://sourceforge.net/projects/pywin32/files/pywin32/Build%20214/)

## Fire ##
The fire script calls FARSITE a fire simulation model and runs a trial, the outputs of the trial are used to update time_since_disturbance and canopy rasters, which subsequently become inputs for the successional model 
### Inputs ###
 - elevation.asc
 - slope.asc
 - aspect.asc
 - canopy.asc
 - fuel.asc

## Ponds 
Description:
### Inputs
 - Hydrologically conditioned DEM with burned streams
 - flow direction
 - suitable streams
 - landcover
 
## Horticulture
### Inputs

## Successional Model ##
### Inputs ###
