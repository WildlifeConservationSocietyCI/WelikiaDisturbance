import settings as s
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
import numpy
import linecache
import arcpy
import pywinauto
import time
import datetime
import random
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import  colors

plt.style.use('ggplot')

new_style = {'grid': False}
matplotlib.rc('axes', **new_style)

class Succession():

    _ecocommunities_filename = 'ecocommunities_%s.tif'

    def __init__(self, year):

        self.year = year
        self.canopy = None
        self.forest_age = None
        self.communities = None
        self.soil = None
        self.pond_time_since_disturbance = None
        self.garden_time_since_disturbance = None
        self.succession_table = pd.read_csv(r'E:\_data\welikia\WelikiaDisturbance\inputs\succession_table .csv')
        self.com_list = [624] #self.succession_table['from_ID']


        # TEST ARRAYS
        self.shape = (10, 10)
        self.communities = np.empty(shape=self.shape)

        # create random land cover grid
        for index, val in np.ndenumerate(self.communities):
            self.communities[index[0]][index[1]] = np.random.choice(self.com_list)
        # self.communities = np.full(shape=self.shape, fill_value=648)
        self.canopy = np.random.randint(30, size=self.shape)
        self.forest_age = np.random.randint(30, size=self.shape)
        self.climax_communities = np.full(shape=self.shape, fill_value=644)

    def raster_to_array(raster_path):
        ascii = gdal.Open(raster_path, GA_ReadOnly)
        array = gdal_array.DatasetReadAsArray(ascii)
        return array

    def set_communities(self):
        this_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year)
        last_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % (self.year - 1))

        if arcpy.Exists(this_year_ecocomms):
            self.ecocommunities = arcpy.RasterToNumPyArray(this_year_ecocomms, nodata_to_value=-9999)


        elif arcpy.Exists(last_year_ecocomms):
            self.ecocommunities = arcpy.RasterToNumPyArray(last_year_ecocomms, nodata_to_value=-9999)


        else:
            self.ecocommunities = arcpy.RasterToNumPyArray(s.ecocommunities, nodata_to_value=-9999)

    def set_canopy(self):

        if os.path.isfile(self.CANOPY_ascii):
            # s.logging.info('Setting canopy')
            self.canopy = self.raster_to_array(self.CANOPY_ascii)

            # if self.garden_disturbance is not None:
            self.canopy = numpy.where(self.ecocommunities == 650,
                                      self.translation_table[650]['max_canopy'], self.canopy)

            # self.canopy = numpy.where((self.ecocommunities == 635) & (self.garden_disturbance == s.TIME_TO_ABANDON),
            #                           [0], self.canopy)

            # if self.pond_disturbance is not None:
            self.canopy = numpy.where((self.ecocommunities == 622),
                                      self.translation_table[622]['max_canopy'], self.canopy)

            # self.canopy = numpy.where((self.ecocommunities == 622) & (self.pond_disturbance == 10),
            #                           self.translation_table[622]['max_canopy'], self.canopy)

        else:
            # s.logging.info('Assigning initial values to canopy array')
            self.canopy = numpy.empty((self.header['nrows'], self.header['ncols']))

            for key in self.translation_table.keys():
                self.canopy = numpy.where((self.ecocommunities == key),
                                          self.translation_table[key]['max_canopy'], self.canopy)

            self.array_to_ascii(self.CANOPY_ascii, self.canopy)

        self.get_memory()
        # s.logging.info('memory usage: %r Mb' % self.memory)

    def set_forest_age(self):

        if os.path.isfile(self.FOREST_AGE_ascii):
            # s.logging.info('Setting forest age')
            self.forest_age = self.raster_to_array(self.FOREST_AGE_ascii)

            self.forest_age[(self.ecocommunities == 650) & (self.forest_age != 0)] = 0

            self.forest_age[(self.ecocommunities == 622) & (self.forest_age != 0)] = 0

        else:
            # s.logging.info('Assigning initial values to forest age array')
            self.forest_age = numpy.empty((self.header['nrows'], self.header['ncols']))
            for key in self.translation_table.keys():
                self.forest_age = numpy.where((self.ecocommunities == key),
                                              self.translation_table[key]['start_age'], self.canopy)

            self.array_to_ascii(self.FOREST_AGE_ascii, self.forest_age)

        self.get_memory()
        # s.logging.info('memory usage: %r Mb' % self.memory)

    def grow(self):

        for index, row in self.succession_table.iterrows():

            # increment forest age and canopy
            if row['type'] == 'forest':
                self.forest_age[self.communities == row['from_ID']] += 1
                self.canopy[(self.communities == row['from_ID']) &
                            (self.canopy < 100)] += row['canopy_growth']

            # increment canopy
            else:
                self.canopy[self.communities == row['from_ID']] += row['canopy_growth']

    def transition(self):

        for index, row in self.succession_table.iterrows():
            key = row['from_ID']

            # SUCCESSIONAL GRASSLAND
            if key == 635:
                self.communities[(self.communities == key) &
                                 (self.canopy > row['max_canopy'])] = row['to_ID']

            # SUCCESSIONAL OLD FIELD
            if key == 648:
                self.communities[(self.communities == key) &
                                 (self.canopy > row['max_canopy'])] = row['to_ID']

            # SUCCESSIONAL SHRUBLAND
            if key == 649:
                self.communities[(self.communities == key) &
                                 (self.canopy > row['max_canopy'])] = row['to_ID'] = row['to_ID']

            # SUCCESSIONAL HARDWOOD FOREST
            if key == 733:
                self.communities = numpy.where((self.communities == key) &
                                               (self.canopy > row['max_canopy']),
                                               self.climax_communities, self.communities)

            # SHALLOW EMERGENT MARSH
            if key == 624:
                self.communities[(self.communities == key) &
                                 (self.canopy > row['max_canopy'])] = row['to_ID']

            # SHRUB SWAMP
            if key == 625:
                self.communities[(self.communities == key) &
                                 (self.canopy > row['max_canopy'])] = row['to_ID']

            # RED MAPLE HARDWOOD SWAMP
            if key == 629:
                self.communities = numpy.where((self.communities == key) &
                                               (self.forest_age > row['max_canopy']),
                                                self.climax_communities, self.communities)



s1 = Succession(1)

print 'communities \n'
print s1.communities
print 'canopy \n'
print s1.canopy
run = range(0, 25)
for year in run:
    print 'year: %s' % year
    s1.grow()
    s1.transition()
    print 'communities \n'
    print s1.communities
    print 'canopy \n'
    print s1.canopy

    if year == max(run):
        # communities
        ax = plt.subplot(311)
        ax.imshow(s1.communities, interpolation='none')
        min_val, max_val = 0, s1.shape[0]
        ind_array = np.arange(min_val, max_val, 1.0)
        x, y = np.meshgrid(ind_array, ind_array)

        for x_val, y_val, com in zip(x.flatten(), y.flatten(), s1.communities.flatten()):
            c = int(com)
            ax.text(x_val, y_val, c, va='center', ha='center', color='white')

        # print s1.communities
        ax2 = plt.subplot(312)
        ax2.imshow(s1.communities, interpolation='none')

        # canopy
        min_val, max_val = 0, s1.shape[0]
        ind_array = np.arange(min_val, max_val, 1.0)
        x, y = np.meshgrid(ind_array, ind_array)

        for x_val, y_val, com in zip(x.flatten(), y.flatten(), s1.canopy.flatten()):
            c = int(com)
            ax2.text(x_val, y_val, c, va='center', ha='center', color='red')

        ax2.imshow(s1.canopy, interpolation='none', cmap='Greens')

        # forest age
        ax3 = plt.subplot(313)
        ax3.imshow(s1.forest_age, interpolation='none')
        min_val, max_val = 0, s1.shape[0]
        ind_array = np.arange(min_val, max_val, 1.0)
        x, y = np.meshgrid(ind_array, ind_array)

        for x_val, y_val, com in zip(x.flatten(), y.flatten(), s1.forest_age.flatten()):
            c = int(com)
            ax3.text(x_val, y_val, c, va='center', ha='center', color='red')

        ax3.imshow(s1.forest_age, interpolation='none', cmap='Blues')
        plt.show()
        # print s1.canopy
