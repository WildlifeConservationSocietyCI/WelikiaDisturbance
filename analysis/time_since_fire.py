import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
from prettyprint import *
import glob
import re
import settings as s
import arcpy

plt.style.use('ggplot')

ROOT_DIR = r"E:\_data\welikia\disturbance_log\200_yr_trial_%s"

def ascii_to_array(in_ascii_path):
    ascii = gdal.Open(in_ascii_path, GA_ReadOnly)
    array = gdal_array.DatasetReadAsArray(ascii)
    return array

for i in range(1, 2):
    # load time_since_disturbance into np_array
    path = os.path.join(ROOT_DIR % i, 'test.tif')
    # extent = ascii_to_array(r"E:\_data\welikia\disturbance_log\200_yr_trial_%s\outputs\ecocommunities_1609.tif" % i)
    time_since_disturbance = ascii_to_array(path)
    # time_since_disturbance = np.where((extent != 600) | (extent != 609) | (extent != 608) | (extent != -9999),
    #                                   time_since_disturbance, -9999)

    print time_since_disturbance.shape

    # create data frame of unique values and counts

    unique = np.unique(time_since_disturbance, return_counts=True)

    d = dict(zip(unique[0], (unique[1] * (s.CELL_SIZE ** 2) / 1000000.0)))
    # df = pd.DataFrame(data={'count': unique[1]}, index=unique[0])
    del d[2147483647]
    # total = sum(d.values())
    # for z in d:
    #     d[z] = d[z] / total
    pp(d)

    plt.subplot(4, 2, i)
    plt.hist(d.keys(), weights=d.values(), bins=50, color='black')
    if i == 6 or i == 7:
        plt.xlabel('years since fire')

    plt.ylim(0, 20)
    plt.xlim(0, 200)
    plt.ylabel('area ($km^2$)')
    plt.title('trial %s' % i)

    # ll_corner = arcpy.Point(589779.34038235,4515478.8842849)
    # out_ras = arcpy.NumPyArrayToRaster(time_since_disturbance,
    #                                     value_to_nodata=-9999,
    #                                     lower_left_corner=ll_corner,
    #                                     x_cell_size=5)
    #
    # out_ras.save(r'E:\_data\welikia\disturbance_log\200_yr_trial_%s\clip_tsd.tif' % i)

plt.show()
