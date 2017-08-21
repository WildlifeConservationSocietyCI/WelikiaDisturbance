import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from prettyprint import *

plt.style.use('ggplot')

ROOT_DIR = r"F:\_data\Welikia\WelikiaDisturbance"
WTR_DIR = os.path.join(ROOT_DIR, 'inputs', 'fire', 'wtr')

weather_files = glob.glob1(WTR_DIR, "*.wtr")

# pp(weather_files)

precip_events = []

for file in weather_files:
    path = os.path.join(WTR_DIR, file)
    # print path
    col_names = ['month', 'day', 'precip', 'hour1', 'hour2', 't1', 't2', 'h1', 'h2', 'elv']
    df = pd.read_csv(path,
                     delim_whitespace=True,
                     header=None,
                     names=col_names,
                     skiprows=[0])

    # print df.head()

    slice = df.ix[df['month'] >= 3]
    print(slice.head())
    x = slice[slice['precip'] > 0]
    precip_events += x['precip'].tolist()





# pp(precip_events)

plt.hist(precip_events, bins=50, color='black', normed=True)
plt.title('Precipitation Events 1876-2006')
plt.ylabel('frequency')
plt.xlabel('rainfall $1/100 in$')
plt.xlim(0, 850)
pe = pd.Series(precip_events, name='precip')

summary = pe.describe()
# print summary.values
# print summary.index
# summary = pd.DataFrame(data=[int(pe.mean), int(pe.std), int(pe.argmin), int(pe.argmax)],
#                        index=['mean', 'std', 'min', 'max'])
# plt.table(cellText=summary.values,
#           rowLabels=summary.index,
#           cellLoc='center',
#           rowLoc='center',
#           loc='top')


# plt.show()

# print(pe.describe())

precip = df['precip']
print(precip.head())
print(df[df['precip'] > 10].count / df.count())