import pandas as pd
import numpy as np
import arcpy
import settings as s
import os
import matplotlib.pyplot as plt
import datetime
import numpy as np
from  prettyprint import *



LOG_DIR = r"C:\Users\LabGuest\Dropbox\disturbance_logs\sensitivity_tests\fire_frequency"

plt.style.use('ggplot')

df_day = pd.read_csv(os.path.join(LOG_DIR, '200_yr_trial_day_scenario', 'ecosystem_areas.csv'))
df_day_2 = pd.read_csv(os.path.join(LOG_DIR, '200_yr_trial_day_scenario_2', 'ecosystem_areas.csv'))

df_russell = pd.read_csv(os.path.join(LOG_DIR, '200_yr_trial_russell_scenario', 'ecosystem_areas.csv'))
df_russell_2 = pd.read_csv(os.path.join(LOG_DIR, '200_yr_trial_russell_scenario_2', 'ecosystem_areas.csv'))

x = df_day.index
ax1 = plt.subplot(411)
plt.title('day fire frequency scenario')
ax1.plot(x, df_day[str(s.GARDEN_ID)], color='green')
ax1.plot(x, df_day[str(s.GRASSLAND_ID)], color='tomato')
plt.ylabel('area $5m^2$')
# ax1.plot(x, d15_ecosystem_area_df[str(s.SHRUBLAND_ID)])

x = df_russell.index
ax2 = plt.subplot(412)
plt.title('russell fire frequency scenario')
ax2.plot(x, df_russell[str(s.GARDEN_ID)], color='green')
ax2.plot(x, df_russell[str(s.GRASSLAND_ID)], color='tomato')
plt.ylabel('area $5m^2$')
# ax1.plot(x, d15_ecosystem_area_df[str(s.SHRUBLAND_ID)])

ax3 = plt.subplot(413)
plt.title('day 2 fire frequency scenario')
ax3.plot(x, df_day_2[str(s.GARDEN_ID)], color='green')
ax3.plot(x, df_day_2[str(s.GRASSLAND_ID)], color='tomato')
plt.ylabel('area $5m^2$')
# ax1.plot(x, d15_ecosystem_area_df[str(s.SHRUBLAND_ID)])

ax4 = plt.subplot(414)
plt.title('russell 2 fire frequency scenario')
ax4.plot(x, df_russell_2[str(s.GARDEN_ID)], color='green', label='garden')
ax4.plot(x, df_russell_2[str(s.GRASSLAND_ID)], color='tomato', label='grassland')
plt.ylabel('area $5m^2$')
plt.xlabel('year')
plt.legend(bbox_to_anchor=(.5, -.5), loc='lower center', ncol=2, mode="expanded")

plt.show()

x = df_day.index
ax1 = plt.subplot(411)
plt.title('day fire frequency scenario')
ax1.plot(x, df_day['622'], color='blue')
ax1.plot(x, df_day['625'], color='red')
plt.ylabel('area $5m^2$')
# ax1.plot(x, d15_ecosystem_area_df[str(s.SHRUBLAND_ID)])

ax2 = plt.subplot(412)
plt.title('russell fire frequency scenario')
ax2.plot(x, df_russell['622'], color='blue')
ax2.plot(x, df_russell['625'], color='red')
plt.ylabel('area $5m^2$')
# ax1.plot(x, d15_ecosystem_area_df[str(s.SHRUBLAND_ID)])

ax3 = plt.subplot(413)
plt.title('day 2 fire frequency scenario')
ax3.plot(x, df_day_2['622'], color='blue')
ax3.plot(x, df_day_2['625'], color='red')
plt.ylabel('area $5m^2$')
# ax1.plot(x, d15_ecosystem_area_df[str(s.SHRUBLAND_ID)])

ax4 = plt.subplot(414)
plt.title('russell 2 fire frequency scenario')
ax4.plot(x, df_russell_2['622'], color='blue', label='pond')
ax4.plot(x, df_russell_2['625'], color='red', label='successional swamp')
# ax1.plot(x, d15_ecosystem_area_df[str(s.SHRUBLAND_ID)])
plt.legend(bbox_to_anchor=(.5, -.5), loc='lower center', ncol=2, mode="expanded")
plt.ylabel('area $5m^2$')
plt.xlabel('year')
xticklabels = ax1.get_xticklabels() + ax2.get_xticklabels()
plt.show()