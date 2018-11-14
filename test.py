import arcpy
from arcpy import env
from arcpy.sa import *

env.workspace = "D:\_data\welikia\WelikiaDisturbance"

# input, mask
inRaster = "inputs_full_extent\dem.tif"
inMaskData = "inputs_region/4_ecocommunities_int.tif"

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# ExtractByMask
outExtractByMask = ExtractByMask(inRaster, inMaskData)

# output
outExtractByMask.save("D:\_data\welikia\WelikiaDisturbance/temp/test")