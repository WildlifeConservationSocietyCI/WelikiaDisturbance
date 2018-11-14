import arcpy
from arcpy import env
from arcpy.sa import *

env.workspace = "D:\_data\welikia\WelikiaDisturbance"

# input, mask
inRaster = "D:\_data\welikia\WelikiaDisturbances\inputs_full_extent\dem.tif"
inMaskData = "D:\_data\welikia\WelikiaDisturbances\inputs_region\4_ecocommunities_int.tif"

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# ExtractByMask
test2 = ExtractByMask(inRaster, inMaskData)

# output
test2.save("D:\_data\welikia\WelikiaDisturbance\temp\test2")