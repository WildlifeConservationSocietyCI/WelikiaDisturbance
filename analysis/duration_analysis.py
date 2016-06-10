import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import glob
import os
from prettyprint import *

plt.style.use('ggplot')

FIRE_SEASON_START = (1, 3)
FIRE_SEASON_END = (31, 5)
EXTINGUISH_THRESHOLD = 10

ROOT_DIR = r"E:\_data\welikia\WelikiaDisturbance\inputs\fire\wtr"
weather_files = glob.glob1(ROOT_DIR, "*.wtr")

weather = []


# def calculate_duration(start_day, start_month, weather):
#
#     for i in weather.ix[i:]:
#         if int(e[2]) > EXTINGUISH_THRESHOLD:
#             end_month = int(e[0])
#             end_day = int(e[1])
#             break

def set_weather(f):

        path = os.path.join(ROOT_DIR, f)
        # print path
        col_names = ['month', 'day', 'precip', 'hour1', 'hour2', 't1', 't2', 'h1', 'h2', 'elv']
        df = pd.read_csv(path,
                         delim_whitespace=True,
                         header=None,
                         names=col_names,
                         skiprows=[0])

        return df[df['month'] >= FIRE_SEASON_START[1]]
EXTINGUISH_THRESHOLDS = range(10, 110, 10)
plots = range(1, len(EXTINGUISH_THRESHOLDS) + 1)

for threshold, plot in zip(EXTINGUISH_THRESHOLDS, plots):

    print "THRESHOLD: %s " % threshold
    durations = []
    for f in weather_files:
        x = set_weather(f)

        # def get_season_end_index()

        end_index = None
        # print FIRE_SEASON_END[0], FIRE_SEASON_END[1]
        for index, row in x.iterrows():
            if (row['month'] == FIRE_SEASON_END[1]) & (row['day'] == FIRE_SEASON_END[0]):
                end_index = index

        # print end_index
        # print x.ix[:end_index]

        # for all days in fire season
        for index, row in x.ix[0:end_index].iterrows():
            # for days without rain
            if row['precip'] == 0:
                # print row['month'], '|', row['day']

                # slice the data frame, return all days after current day
                slice = x.ix[index:]
                # print slice.head(20)

                # count number of days until next day with extinguishing precipitation
                dur = 0
                for index, row in slice.iterrows():
                    # print row['precip']
                    dur += 1
                    if row['precip'] >= threshold:
                        break
                durations.append(dur)

    # unique = np.unique(durations, return_counts=True)
    plt.subplot(5, 2, plot)

    # print unique[0]
    # print unique[1]

    plt.hist(durations, bins=50)
    # total_count = float(sum(unique[1]))
    # p = [i / total_count for i in unique[1]]
    # print p
    # plt.subplot(5, 2, 2)
    # plt.scatter(x=unique[0], y=p, marker="-")
    plt.xlabel('fire duration (days)', fontsize=8)
    plt.xlim(0, 100)
    matplotlib.rc('xtick', labelsize=8)

    plt.ylabel('frequency', fontsize=8)
    plt.ylim(0, 5500)
    matplotlib.rc('ytick', labelsize=8)

    plt.title('extinguishing threshold: %s' % threshold, fontsize=8)

plt.show()