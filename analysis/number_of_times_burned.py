import os
import sys
import numpy as np
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
from prettyprint import *
import glob
import arcpy

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to get spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)


ROOT_DIR = r'E:\_data\welikia\disturbance_log\sensitivity_tests\extinguishing_threshold\200_year_threshold_50_trial_%s\burn_rasters'

def ascii_to_array(in_ascii_path):
    ascii = gdal.Open(in_ascii_path, GA_ReadOnly)
    array = gdal_array.DatasetReadAsArray(ascii)
    return array

cell_size = 5
ll_corner = arcpy.Point(589779.34038235, 4515478.8842849)

trials = range(1, 2)
pp(trials)

for trial in trials:


    def number_of_times_burned():

        raster_list = glob.glob1(ROOT_DIR % trial, '*_farsite_output.fml')

        pp(raster_list)
        print len(raster_list)

        # # pp(raster_list)
        times_burned = []
        for i in raster_list:

            path = os.path.join(ROOT_DIR % trial, i)

            a = ascii_to_array(path)

            # convert flame length map to binary burn/un-burn raster
            a[a != -1] = 1
            a[a == -1] = 0

            # print a[0]

            # append to trial list
            times_burned.append(a)

        t = sum(times_burned)
        out_ras = arcpy.NumPyArrayToRaster(t,
                                           value_to_nodata=-1,
                                           lower_left_corner=ll_corner,
                                           x_cell_size=5)

        out_ras.save(r'E:\_data\welikia\disturbance_log\sensitivity_tests\extinguishing_threshold\200_year_threshold_50_trial_%s\times_burned.tif' % trial)





