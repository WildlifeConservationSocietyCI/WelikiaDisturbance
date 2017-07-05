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

plt.style.use('grayscale')

# load ecosystem areas from each dependency scenario
d15_ecosystem_area = os.path.join(LOG_DIR, '200_yr_trial_dependence_15', 'ecosystem_areas.csv')
d15_ecosystem_area_df = pd.DataFrame.from_csv(d15_ecosystem_area)


d30_ecosystem_area = os.path.join(LOG_DIR, '200_yr_trial_dependence_30', 'ecosystem_areas.csv')
d30_ecosystem_area_df = pd.DataFrame.from_csv(d30_ecosystem_area)


d60_ecosystem_area = os.path.join(LOG_DIR, '200_yr_trial_dependence_60', 'ecosystem_areas.csv')
d60_ecosystem_area_df = pd.DataFrame.from_csv(d60_ecosystem_area)


d15_ecosystem_area_df['635'].fillna(0, inplace=True)
d30_ecosystem_area_df['635'].fillna(0, inplace=True)
d60_ecosystem_area_df['635'].fillna(0, inplace=True)

x = d15_ecosystem_area_df.index
ax1 = plt.subplot(311)
plt.title('15% dependency')
ax1.plot(x, d15_ecosystem_area_df[str(s.GARDEN_ID)])
ax1.plot(x, d15_ecosystem_area_df[str(s.SUCCESSIONAL_GRASSLAND_ID)])
# ax1.plot(x, d15_ecosystem_area_df[str(s.SHRUBLAND_ID)])

plt.ylim(0, 1000)
plt.xlim(min(x), max(x))

ax2 = plt.subplot(312, sharex=ax1)
plt.title('30% dependency')
ax2.plot(x, d30_ecosystem_area_df[str(s.GARDEN_ID)])
ax2.plot(x, d30_ecosystem_area_df[str(s.SUCCESSIONAL_GRASSLAND_ID)])
# ax2.plot(x, d30_ecosystem_area_df[str(s.SHRUBLAND_ID)])
plt.ylim(0, 1000)
plt.xlim(min(x), max(x))

ax3 = plt.subplot(313, sharex=ax1)
plt.title('60% dependency')
ax3.plot(x, d60_ecosystem_area_df[str(s.GARDEN_ID)], label='garden area')
ax3.plot(x, d60_ecosystem_area_df[str(s.SUCCESSIONAL_GRASSLAND_ID)], label='grassland area')
# ax2.plot(x, d60_ecosystem_area_df[str(s.SHRUBLAND_ID)])
plt.ylim(0, 1000)
plt.xlim(min(x), max(x))
plt.legend(bbox_to_anchor=(.5, -.5), loc='lower center', ncol=2, mode="expanded")
xticklabels = ax1.get_xticklabels() + ax2.get_xticklabels()
plt.setp(xticklabels, visible=False)

plt.show()
