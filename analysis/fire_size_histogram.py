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

ROOT_DIR = r"C:\Users\LabGuest\Dropbox\disturbance_logs\200_yr_trial_%s"

trials = range(1,8)

fire_size = []
fire_size_log_transform = []
for trial in trials:

    df = pd.read_csv(os.path.join(ROOT_DIR % trial, 'disturbance_table.csv'))

    for i in df['fire_area'].tolist():
        if i != 0:
            fire_size.append(i * 5.0 * 0.0001)
            fire_size_log_transform.append(np.log(i * 5.0 / 1000000))
# pp(fire_size)
plt.subplot(1,1,1)
n, bins, patches = plt.hist(fire_size, bins=50, color='black')
plt.ylabel('frequency')
plt.xlabel('fire area ($hectare$)')
plt.title('fire size 200 year trials')
# plt.xscale('log', nonposx='clip' )
# plt.yscale('log')
# plt.xscale('log')

# pp(n)
# pp(bins)
# y = n
# x = [100, 1000, 10000]
# print x
# plt.subplot(3,1,2)
# plt.scatter(x=x, y=y)
# # determine best fit line
# slope, intercept, r_value, p_value, std_err = stats.linregress(np.log10(x+1), np.log10(y))
#
# xfid = np.linspace(0,3)     # This is just a set of x to plot the straight line
# plt.plot(np.log10(x + 1), np.log10(y), 'k.')
# plt.plot(xfid, xfid*slope+intercept)
# plt.xscale('log')
# plt.yscale('log')
# # pp(fire_size_log_transform)
# plt.subplot(3,1,3)
# n, bins, patches = plt.hist(fire_size_log_transform, bins=20, color='black')
# plt.ylabel('frequency')
# plt.xlabel('fire area log transformed')

plt.show()