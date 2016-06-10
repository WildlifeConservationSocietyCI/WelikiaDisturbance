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
SENSITIVITY_DIR = r'C:\Users\LabGuest\Dropbox\disturbance_logs\sensitivity_tests\extinguishing_threshold\200_yr_threshold_50_trial_1'
trials = range(1,8)

burned_area = []
for trial in trials:

    df = pd.read_csv(os.path.join(ROOT_DIR % trial, 'disturbance_table.csv'))
    print df.head()
    burned_area.append((df['fire_area'].sum() * (5.0 ** 2) / 1000000))

df = pd.read_csv(os.path.join(SENSITIVITY_DIR, 'disturbance_table.csv'))
print df.head()
burned_area.append((df['fire_area'].sum() * (5.0 ** 2) / 1000000))


pp(burned_area)
trials.append(8)
plt.bar(trials, burned_area, align='center', color='black')
# plt.ylim(0)
plt.xticks(trials, trials)
plt.ylabel('burned area ($km^2$)')
plt.xlabel('trials')
plt.title('total burned area 200 year trials')
plt.show()