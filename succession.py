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

        self.DEM_ascii = os.path.join(s.INPUT_DIR, 'fire', 'spatial', s.REGION, 'dem.asc')
        self.CANOPY_ascii = os.path.join(s.OUTPUT_DIR, 'canopy.asc')
        self.FOREST_AGE_ascii = os.path.join(s.OUTPUT_DIR, 'forest_age.asc')
        self._ecocommunities_filename = '%s_ecocommunities.tif'

        self.canopy = None
        self.forest_age = None
        self.ecocommunities = None
        self.ecocommunities_array = None
        self.climax_communities = self.raster_to_array(s.ecocommunities)
        self.soil = None
        self.pond_time_since_disturbance = None
        self.garden_time_since_disturbance = None
        self.succession_table = pd.read_csv(os.path.join(s.ROOT_DIR, 'succession_table.csv'))

        self.header = None
        self.header_text = None
        # self.com_list = [624] #self.succession_table['from_ID']

        self.translation_table = pd.read_csv(os.path.join(s.ROOT_DIR, 'ec_translator.txt'),
                                             delim_whitespace=True, index_col='ec_id')


        # TEST ARRAYS
        # self.shape = (10, 10)
        # self.communities = np.empty(shape=self.shape)
        #
        # # create random land cover grid
        # for index, val in np.ndenumerate(self.communities):
        #     self.communities[index[0]][index[1]] = np.random.choice(self.com_list)
        # # self.communities = np.full(shape=self.shape, fill_value=648)
        # self.canopy = np.random.randint(30, size=self.shape)
        # self.forest_age = np.random.randint(30, size=self.shape)
        # self.climax_communities = np.full(shape=self.shape, fill_value=644)
        self.get_header()
        self.set_ecocommunities()
        self.set_canopy()
        self.set_forest_age()

    def get_header(self):
        header = [linecache.getline(self.DEM_ascii, i) for i in range(1, 7)]
        h = {}

        for line in header:
            attribute, value = line.split()
            h[attribute] = value

        h['ncols'] = int(h['ncols'])
        h['nrows'] = int(h['nrows'])
        h['cellsize'] = int(h['cellsize'])
        h['xllcorner'] = float(h['xllcorner'])
        h['yllcorner'] = float(h['yllcorner'])

        self.header = h
        self.header_text = header

    def raster_to_array(self, raster_path):
        ascii = gdal.Open(raster_path, GA_ReadOnly)
        array = gdal_array.DatasetReadAsArray(ascii)
        return array

    def array_to_ascii(self, out_ascii_path, array):
        """

        :rtype: object
        """
        out_asc = open(out_ascii_path, 'w')
        for attribute in self.header_text:
            out_asc.write(attribute)

        numpy.savetxt(out_asc, array, fmt="%4i")
        out_asc.close()

    def set_ecocommunities(self):
        """
        """

        this_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year)
        last_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % (self.year - 1))

        if os.path.isfile(this_year_ecocomms):
            print this_year_ecocomms
            self.ecocommunities = arcpy.Raster(this_year_ecocomms)
            self.ecocommunities= arcpy.RasterToNumPyArray(self.ecocommunities)

        elif os.path.isfile(last_year_ecocomms):
            print last_year_ecocomms
            self.ecocommunities = arcpy.Raster(last_year_ecocomms)
            self.ecocommunities= arcpy.RasterToNumPyArray(self.ecocommunities)

        else:
            print 'initial run'
            self.ecocommunities = arcpy.Raster(s.ecocommunities)
            self.ecocommunities= arcpy.RasterToNumPyArray(self.ecocommunities)
            # self.ecocommunities.save(os.path.join(self.OUTPUT_DIR, self._ecocommunities_filename % self.year))

    def set_canopy(self):

        if os.path.isfile(self.CANOPY_ascii):
            s.logging.info('Setting canopy')
            self.canopy = self.raster_to_array(self.CANOPY_ascii)

        else:
            s.logging.info('Assigning initial values to canopy array')
            self.canopy = numpy.empty((self.header['nrows'], self.header['ncols']))

            # for key in self.translation_table.keys():
            for key in self.translation_table.index:
                self.canopy = numpy.where((self.ecocommunities_array == key),
                                          self.translation_table.ix[key]['max_canopy'], self.canopy)

            self.array_to_ascii(self.CANOPY_ascii, self.canopy)

    def set_forest_age(self):

        if os.path.isfile(self.FOREST_AGE_ascii):
            s.logging.info('Setting forest age')
            self.forest_age = self.raster_to_array(self.FOREST_AGE_ascii)

        else:
            s.logging.info('Assigning initial values to forest age array')
            self.forest_age = numpy.empty((self.header['nrows'], self.header['ncols']))

            for key in self.translation_table.index:
                self.forest_age = numpy.where((self.ecocommunities_array == key),
                                              self.translation_table.ix[key]['start_age'], self.forest_age)

            self.array_to_ascii(self.FOREST_AGE_ascii, self.forest_age)

    def grow(self):

        for index, row in self.succession_table.iterrows():
            key = row['from_ID']
            canopy_growth = row['canopy_growth']
            # increment forest age and canopy
            if row['type'] == 'forest':
                self.forest_age[self.ecocommunities == key] += canopy_growth
                self.canopy[(self.ecocommunities == key) &
                            (self.canopy < 100)] += canopy_growth

            # increment canopy
            else:
                self.canopy[self.ecocommunities == key] += canopy_growth

    def transition(self):

        for index, row in self.succession_table.iterrows():
            key = int(row['from_ID'])
            try:
                to_key = int(row['to_ID'])
            except:
                print 'to initial'

            # SUCCESSIONAL GRASSLAND
            if key == 635:
                self.ecocommunities[(self.ecocommunities == key) &
                                 (self.canopy > row['max_canopy'])] = to_key
            # SUCCESSIONAL OLD FIELD
            if key == 648:
                self.ecocommunities[(self.ecocommunities == key) &
                                 (self.canopy > row['max_canopy'])] = to_key

            # SUCCESSIONAL SHRUBLAND
            if key == 649:
                self.ecocommunities[(self.ecocommunities == key) &
                                 (self.canopy > row['max_canopy'])] = to_key

            # SUCCESSIONAL HARDWOOD FOREST
            if key == 733:
                self.ecocommunities = numpy.where((self.ecocommunities == key) &
                                               (self.canopy > row['max_canopy']),
                                               self.climax_communities, self.ecocommunities)

            # SHALLOW EMERGENT MARSH
            if key == 624:
                self.ecocommunities[(self.ecocommunities == key) &
                                 (self.canopy > row['max_canopy'])] = to_key

            # SHRUB SWAMP
            if key == 625:
                self.ecocommunities[(self.ecocommunities == key) &
                                 (self.canopy > row['max_canopy'])] = to_key

            # RED MAPLE HARDWOOD SWAMP
            if key == 629:
                self.ecocommunities = numpy.where((self.ecocommunities == key) &
                                               (self.forest_age > row['age_out']),
                                                self.climax_communities, self.ecocommunities)

    def run_succession(self):

        self.grow()
        self.transition()

        self.array_to_ascii(array=self.ecocommunities, out_ascii_path=os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year))
        self.array_to_ascii(array=self.canopy, out_ascii_path=self.CANOPY_ascii)
        self.array_to_ascii(array=self.forest_age, out_ascii_path=self.FOREST_AGE_ascii)



s1 = Succession(1409)
print s1.succession_table.head()
s1.run_succession()
#
# for index, row in s1.succession_table.iterrows():
#     key = row['from_ID']
#     print key, type(key)
#     print row['max_canopy']
#     print row['to_ID'], type(row['to_ID'])
    # if key == 635:
    # self.communities[(self.communities == key) &
    #                  (self.canopy > row['max_canopy'])] = row['to_ID']
# print 'communities \n'
# print s1.communities
# print 'canopy \n'
# print s1.canopy
# run = range(0, 25)
# for year in run:
#     print 'year: %s' % year
#     s1.grow()
#     s1.transition()
#     print 'communities \n'
#     print s1.communities
#     print 'canopy \n'
#     print s1.canopy
#
#     if year == max(run):
#         # communities
#         ax = plt.subplot(311)
#         ax.imshow(s1.communities, interpolation='none')
#         min_val, max_val = 0, s1.shape[0]
#         ind_array = np.arange(min_val, max_val, 1.0)
#         x, y = np.meshgrid(ind_array, ind_array)
#
#         for x_val, y_val, com in zip(x.flatten(), y.flatten(), s1.communities.flatten()):
#             c = int(com)
#             ax.text(x_val, y_val, c, va='center', ha='center', color='white')
#
#         # print s1.communities
#         ax2 = plt.subplot(312)
#         ax2.imshow(s1.communities, interpolation='none')
#
#         # canopy
#         min_val, max_val = 0, s1.shape[0]
#         ind_array = np.arange(min_val, max_val, 1.0)
#         x, y = np.meshgrid(ind_array, ind_array)
#
#         for x_val, y_val, com in zip(x.flatten(), y.flatten(), s1.canopy.flatten()):
#             c = int(com)
#             ax2.text(x_val, y_val, c, va='center', ha='center', color='red')
#
#         ax2.imshow(s1.canopy, interpolation='none', cmap='Greens')
#
#         # forest age
#         ax3 = plt.subplot(313)
#         ax3.imshow(s1.forest_age, interpolation='none')
#         min_val, max_val = 0, s1.shape[0]
#         ind_array = np.arange(min_val, max_val, 1.0)
#         x, y = np.meshgrid(ind_array, ind_array)
#
#         for x_val, y_val, com in zip(x.flatten(), y.flatten(), s1.forest_age.flatten()):
#             c = int(com)
#             ax3.text(x_val, y_val, c, va='center', ha='center', color='red')
#
#         ax3.imshow(s1.forest_age, interpolation='none', cmap='Blues')
#         plt.show()
#         # print s1.canopy
