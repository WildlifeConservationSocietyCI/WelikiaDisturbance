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
from scipy import stats

plt.style.use('ggplot')

ROOT_DIR = r"E:\_data\welikia\disturbance_log\200_yr_trial_%s"

def ascii_to_array(in_ascii_path):
    ascii = gdal.Open(in_ascii_path, GA_ReadOnly)
    array = gdal_array.DatasetReadAsArray(ascii)
    return array

def time_since_fire(path, ecocommunities):
    # load time_since_disturbance into np_array
    extent = ascii_to_array(ecocommunities)
    time_since_disturbance = ascii_to_array(path)
    # time_since_disturbance = np.where((extent != 600) | (extent != 609) | (extent != 608) | (extent != -9999),
    #                                   time_since_disturbance, -9999)

    time_since_disturbance[(extent == 600) | (extent == 609) | (extent == 608) | (extent == -9999)] = -9999
    table = stats.itemfreq(time_since_disturbance)
    x = table[:, 0]
    y = table[:, 1]
    l = []
    for val, freq in zip(x, y):
        if val >= 0 & val <= 190:
            for count in range(0, freq):
                l.append(val)
    plt.hist(l, bins=20)
    plt.xlim(0, 190)
    plt.ylim(0, 1000000)
    plt.show()
    # print l

t_path = os.path.join(ROOT_DIR, 'outputs', 'fire', '1609_time_since_disturbance.asc')
c_path = os.path.join(ROOT_DIR, 'outputs', 'ecocommunities_1609.tif')
time_since_fire(t_path, c_path)