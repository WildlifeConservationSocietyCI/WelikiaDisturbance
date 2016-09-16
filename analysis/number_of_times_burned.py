import os
import sys
import numpy as np
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
from prettyprint import *
import glob
import arcpy
import settings as s
import linecache
import itertools

def ascii_to_array(in_ascii_path):
    ascii = gdal.Open(in_ascii_path, GA_ReadOnly)
    array = gdal_array.DatasetReadAsArray(ascii)
    return array


def get_header(raster):
    header = [linecache.getline(raster, i) for i in range(1, 6)]
    h = {}

    for line in header:
        attribute, value = line.split()
        h[attribute] = value
    print h
    h['NCOLS'] = int(h['NCOLS'])
    h['NROWS'] = int(h['NROWS'])
    h['CELLSIZE'] = int(float(h['CELLSIZE']))
    h['XLLCORNER'] = float(h['XLLCORNER'])
    h['YLLCORNER'] = float(h['YLLCORNER'])

    return h


cell_size = s.CELL_SIZE


trials = range(1, 2)
pp(trials)

def number_of_times_burned():

    h = None
    ll_corner = None

    flame_dir =os.path.join(s.OUTPUT_DIR, 'fire', 'burn_rasters')
    print flame_dir
    raster_list = glob.glob1(os.path.join(s.OUTPUT_DIR, 'fire', 'burn_rasters'), '*_farsite_output.fml')

    pp(raster_list)
    print len(raster_list)

    # # pp(raster_list)
    times_burned = []
    for i in raster_list:

        if h is None:
            h = get_header(os.path.join(flame_dir, i))
            ll_corner = arcpy.Point(h['XLLCORNER'], h['YLLCORNER'])
        print 'loading raster %s' % i
        path = os.path.join(flame_dir, i)

        a = ascii_to_array(path)

        # convert flame length map to binary burn/un-burn raster
        a[a != -1] = 1
        a[a == -1] = 0

        # print a[0]

        # append to trial list
        times_burned.append(a)

    print 'summing raster list'
    t = sum(times_burned)

    print 'saving as tif'
    out_ras = arcpy.NumPyArrayToRaster(t,
                                       value_to_nodata=-1,
                                       lower_left_corner=ll_corner,
                                       x_cell_size=5)

    out_ras.save(os.path.join(s.OUTPUT_DIR, 'times_burned.tif'))

number_of_times_burned()



