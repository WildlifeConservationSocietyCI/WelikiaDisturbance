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

plt.style.use('ggplot')

# LOG_DIR = os.path.join('C:\\', 'Users', 'LabGuest', 'Dropbox')
#
# fire_area_csv = os.path.join(LOG_DIR, 'fire_area.csv')
#
# fire_area_df = pd.read_csv(fire_area_csv)
#
# total_area_burned = []
#
# total_area_burned.append(fire_area_df.fire_area_t1.sum())
# total_area_burned.append(fire_area_df.fire_area_t2.sum())
# total_area_burned.append(fire_area_df.fire_area_t3.sum())
# total_area_burned.append(fire_area_df.fire_area_t4.sum())
#
# print total_area_burned
# trials = [1, 2, 3, 4]
# plt.bar(trials, total_area_burned, align='center')
# plt.ylim(0, 15000000)
# plt.xticks(trials, ['t1', 't2', 't3', 't4'])
# plt.show()
#


ROOT_DIR = r"E:\_data\welikia\disturbance_log\200_yr_trial_%s\outputs\fire\log_rasters"
OUT_DIR = r"C:\Users\LabGuest\Dropbox\disturbance_logs\200_yr_trial_%s"


def ascii_to_array(in_ascii_path):
    ascii = gdal.Open(in_ascii_path, GA_ReadOnly)
    array = gdal_array.DatasetReadAsArray(ascii)
    return array

l = [1, 2, 3, 4, 5, 6, 7]

for i in l:
    print 'trial: %s' % i
    raster_list = glob.glob1(ROOT_DIR % i, '*_time_since_disturbance.asc')
    pp(raster_list)

    years = []
    recently_burned = []
    fire_size = []
    for raster in raster_list:
        years.append(int(re.findall(r'\d+', raster)[0]))
        raster_path = os.path.join(ROOT_DIR % i, raster)
        a = ascii_to_array(raster_path)
        recently_burned.append((a < 10).sum())
        fire_size.append((a <= 1).sum())

    # convert to data frame
    df = pd.DataFrame({'year': years,
                       'recently_burned_area': recently_burned,
                       'fire_size': fire_size})

    print df.head()

    # save data frame as csv
    df.to_csv(os.path.join(OUT_DIR % i, 'recently_burned_area.csv'))

    # plot figure
    # fig, ax = plt.subplots()
    # ax.scatter(x=df['year'], y=df['recently_burned_area'])
    # # fig.savefig(OUT_DIR % i, 'burned_area_plot.png')
    # plt.show()

