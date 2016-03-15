# WelikiaDisturbance
Integrated fire and horticulture disturbance modeling

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
