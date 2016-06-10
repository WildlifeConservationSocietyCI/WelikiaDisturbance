import pandas as pd
import numpy as np
import arcpy
import settings as s
import os
import matplotlib.pyplot as plt
import datetime
import numpy as np
from  prettyprint import *



LOG_DIR = r"C:\Users\LabGuest\Dropbox\disturbance_logs\sensitivity_tests\per-capita_garden_area"

plt.style.use('ggplot')

# load ecosystem areas from each dependency scenario
d15_ecosystem_area = os.path.join(LOG_DIR, '200_yr_trial_dependence_15', 'ecosystem_areas.csv')
d15_ecosystem_area_df = pd.DataFrame.from_csv(d15_ecosystem_area)

d30_ecosystem_area = os.path.join(LOG_DIR, '200_yr_trial_dependence_30', 'ecosystem_areas.csv')
d30_ecosystem_area_df = pd.DataFrame.from_csv(d30_ecosystem_area)

# d60_ecosystem_area = os.path.join(LOG_DIR, '200_yr_trial_1', 'ecosystem_area.csv')
# d60_ecosystem_area_df = pd.DataFrame.from_csv(d15_ecosystem_area)

x = d15_ecosystem_area_df.index
ax1 = plt.subplot(211)
ax1.plot(x, d15_ecosystem_area_df[str(s.GARDEN_ID)])
ax1.plot(x, d15_ecosystem_area_df[str(s.SHRUBLAND_ID)])
# plt.ylim(0, 1500)
plt.xlim(min(x), max(x))

ax2 = plt.subplot(212, sharex=ax1)
ax2.plot(x, d30_ecosystem_area_df[str(s.GARDEN_ID)])
ax2.plot(x, d30_ecosystem_area_df[str(s.GRASSLAND_ID)])
ax2.plot(x, d30_ecosystem_area_df[str(s.SHRUBLAND_ID)])
# plt.ylim(0, 1500)
plt.xlim(min(x), max(x))

xticklabels = ax1.get_xticklabels()
plt.setp(xticklabels, visible=False)

plt.show()
