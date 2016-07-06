import pandas as pd
import numpy as np
import arcpy
import settings as s
import os
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
import datetime

x = datetime.datetime

print x.now()
# DIR = r"E:\_data\welikia\disturbance_log\sensitivity_tests\per-capita_garden_area\200_yr_trial_dependence_15\outputs"
# LOG_DIR = r"C:\Users\LabGuest\Dropbox\disturbance_logs\sensitivity_tests\per-capita_garden_area\200_yr_trial_dependence_15"

def raster_to_array(raster_path):
    raster = gdal.Open(raster_path, GA_ReadOnly)
    array = gdal_array.DatasetReadAsArray(raster)
    return array


def get_counts(array):
    unique = np.unique(array, return_counts=True)
    return dict(zip(unique[0], unique[1]))

def ecosystem_areas():
    communities = [600, 608, 609, 616, 621, 622, 625, 629, 632, 635, 644, 647, 649, 650, 654]
    index = range(1409, 1610)  #s.RUN_LENGTH
    df = pd.DataFrame(columns=communities, index=index)
    ecocommunities = os.path.join(s.OUTPUT_DIR, 'ecocommunities_%s.tif')

    for year in range(1409, 1610):

        if arcpy.Exists(ecocommunities % year):
            array = raster_to_array(ecocommunities % year)
            d = get_counts(array)
            df.loc[year] = pd.Series(d)

    df.fillna(value=0, inplace=True)
    df.to_csv(path_or_buf=os.path.join(s.LOG_DIR, 'ecosystem_areas.csv'))

ecosystem_areas()