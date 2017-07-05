import matplotlib.pyplot as plt
import pandas as pd
import settings as s
import os

plt.style.use('ggplot')

df = pd.read_csv(os.path.join(s.LOG_DIR, 'ecosystem_areas.csv'))

x = df.index

ax1 = plt.subplot(211)
ax1.plot(df['63500'], label='grassland')
ax1.plot(df['64800'], label='old field')
ax1.plot(df['64900'], label='shrubland')
ax1.plot(df['73600'], label='successional forest')
plt.ylabel('$5m^2$ cells')
plt.legend()


ax2 = plt.subplot(212)
ax2.plot(df['73700'], label='active beaver pond')
ax2.plot(df['62400'], label='emergent marsh')
ax2.plot(df['62500'], label='shrub swamp')
ax2.plot(df['62900'], label='red maple swamp')
plt.ylabel('$5m^2$ cells')
plt.legend()

plt.show()
