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

# trials = range(1,8)

trials = np.linspace(1, 7, 7, endpoint=True)

print trials
fire_count = {}

for trial in trials:

    df = pd.read_csv(os.path.join(ROOT_DIR % int(trial), 'disturbance_table.csv'))

    count = len(df['fire_area'][df['fire_area'] > 0])

    fire_count[trial] = count

pp(fire_count)

fig, ax = plt.subplots()

fc = ax.bar(trials, fire_count.values(), color='black')
plt.ylim(0, 50)
plt.title('fire counts 200 year trials')
plt.xlabel('trials')
plt.ylabel('counts')
plt.show()
