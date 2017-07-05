import settings as s
import tree_allometry as ta
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
import numpy as np
import linecache
import arcpy
import os
import pandas as pd
import scipy.stats as ss


class Succession(object):
    _ecocommunities_filename = 'ecocommunities_%s.tif'

    def __init__(self, year):

        self.year = year

        # raster paths
        self.DEM_ascii = os.path.join(s.INPUT_DIR, 'fire', 'spatial', s.REGION, 'dem.asc')
        self.CANOPY_ascii = os.path.join(s.OUTPUT_DIR, 'canopy.asc')
        self.FOREST_AGE_ascii = os.path.join(s.OUTPUT_DIR, 'forest_age.asc')
        self.DBH_ascii = os.path.join(s.OUTPUT_DIR, 'dbh.asc')
        self._ecocommunities_filename = 'ecocommunities_%s.tif'

        # arrays
        self.canopy = None
        self.forest_age = None
        self.dbh = None
        self.ecocommunities = None
        self.climax_communities = arcpy.RasterToNumPyArray(s.ecocommunities, nodata_to_value=-9999)
        self.climax_canopy = None
        self.pond_time_since_disturbance = None
        self.garden_time_since_disturbance = None

        # header
        self.shape = None
        self.header = None
        self.header_text = None

        # community info table
        self.community_table = pd.read_csv(s.community_table, index_col=0)

        self.get_header()
        self.set_ecocommunities()
        self.set_canopy()
        self.set_forest_age()
        self.set_dbh()

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
        self.shape = (h['nrows'], h['ncols'])

    def raster_to_array(self, raster_path):
        ascii = gdal.Open(raster_path, GA_ReadOnly)
        array = gdal_array.DatasetReadAsArray(ascii)
        return array

    def array_to_ascii(self, out_ascii_path, array, fmt="%4i"):
        """

        :rtype: object
        """

        out_asc = open(out_ascii_path, 'w')
        for attribute in self.header_text:
            out_asc.write(attribute)

        np.savetxt(out_asc, array, fmt=fmt)
        out_asc.close()

    def set_ecocommunities(self):
        """
        """

        this_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year)
        last_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % (self.year - 1))

        if os.path.isfile(this_year_ecocomms):
            print this_year_ecocomms
            self.ecocommunities = arcpy.Raster(this_year_ecocomms)
            self.ecocommunities = arcpy.RasterToNumPyArray(self.ecocommunities, nodata_to_value=-9999)

        elif os.path.isfile(last_year_ecocomms):
            print last_year_ecocomms
            self.ecocommunities = arcpy.Raster(last_year_ecocomms)
            self.ecocommunities = arcpy.RasterToNumPyArray(self.ecocommunities, nodata_to_value=-9999)

        else:
            print 'initial run'
            self.ecocommunities = arcpy.Raster(s.ecocommunities)
            self.ecocommunities = arcpy.RasterToNumPyArray(self.ecocommunities, nodata_to_value=-9999)
            # self.ecocommunities.save(os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year))

    def set_canopy(self):
        """
        set canopy for given year if no canopy raster exists, use previous year,
        else: initialize canopy raster
        :return:
        """

        if os.path.isfile(self.CANOPY_ascii):
            s.logging.info('Setting canopy')
            self.canopy = self.raster_to_array(self.CANOPY_ascii)

        else:
            s.logging.info('Assigning initial values to canopy array')
            # if self.ecocommunities_array is None:
            #     self.ecocommunities_array = arcpy.RasterToNumPyArray(self.ecocommunities)

            self.canopy = np.empty((self.header['nrows'], self.header['ncols']))

            for index, row in self.community_table.iterrows():
                self.canopy[self.ecocommunities == index] = row.max_canopy

            self.array_to_ascii(self.CANOPY_ascii, self.canopy)

    def set_forest_age(self):
        """
        set forest age for given year, if no forest age raster exists, use previous year,
        else: initialize froest age raster
        :return:
        """
        if os.path.isfile(self.FOREST_AGE_ascii):
            s.logging.info('Setting forest age')
            self.forest_age = self.raster_to_array(self.FOREST_AGE_ascii)

        else:
            s.logging.info('Assigning initial values to forest age array')
            # if self.ecocommunities_array is None:
            #     self.ecocommunities_array = arcpy.RasterToNumPyArray(self.ecocommunities)


            # create truncated normal distrbution for age
            lower = s.MINIMUM_FOREST_AGE
            upper = s.UPPER
            mu = s.MEAN_INITIAL_FOREST_AGE
            sigma = s.AGE_VAR

            n = ss.truncnorm((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)

            # populate an array with ages from distribution
            tn = n.rvs(self.shape).astype(int)

            self.forest_age = np.empty(shape=self.shape, dtype=int)

            for index, row in self.community_table.iterrows():
                if row.forest == 1:
                    self.forest_age = np.where(self.ecocommunities == index, tn, self.forest_age)

            self.array_to_ascii(self.FOREST_AGE_ascii, self.forest_age)

    def set_dbh(self):
        """

        :return:
        """
        if os.path.isfile(self.DBH_ascii):
            s.logging.info('Setting dbh')
            self.dbh = self.raster_to_array(self.DBH_ascii)

        else:
            s.logging.info('Assigning initial values to dbh array')
            self.dbh = np.zeros(shape=self.shape, dtype=np.float16)
            # self.dbh = np.empty(shape=self.shape, dtype=np.float16)
            age_dbh_lookup = pd.read_csv(os.path.join(s.ROOT_DIR, 'dbh_lookup.csv'), index_col=0)

            for index, row in self.community_table.iterrows():

                if row.forest == 1:
                    age = np.ma.masked_where(self.ecocommunities != index, self.forest_age)
                    print index
                    for a in np.ma.compressed(np.unique(age)):
                        print a
                        d = age_dbh_lookup.ix[int(a)][str(index)]
                        self.dbh[(self.ecocommunities == index) & (self.forest_age == a)] = d

            self.array_to_ascii(self.DBH_ascii, self.dbh, fmt="%2.4f")

    def grow(self):
        """
        for each community increment canopy for all cells,
        if the community is a forest type increment forest age
        :return:
        """
        # TODO: create single table that contains the fuel, succession, and canopy info for all communities

        for index, row in self.community_table.iterrows():
                canopy_growth = int(row['canopy_growth'])
                max_canopy = int(row['max_canopy'])

                # increment age of all communities that have trees all upland communities

                if row.forest == 1:

                    # increment canopy
                    self.canopy[(self.ecocommunities == index) & (self.canopy < max_canopy)] += canopy_growth

                else:
                    # increment non forest canopy
                    self.canopy[(self.ecocommunities == index)] += canopy_growth

                print row.dbh_model
                if max_canopy > 0:
                    # increment forest age
                    self.forest_age[self.ecocommunities == index] += 1

                    # increment dbh
                    print "%s %s | max canopy: %s" % (index, row.Name, max_canopy)
                    self.dbh[(self.ecocommunities == index) &
                             (self.forest_age == 1)
                             & (self.dbh == 0)] = 0.5

                    dbh_model = int(row.dbh_model)
                    site_index = int(row.site_index)

                    d_grow = ta.DGROW(species=dbh_model, SI=site_index, DBH=self.dbh)

                    self.dbh = np.where(self.ecocommunities == index, self.dbh + d_grow, self.dbh)


    def transition(self):
        """
        for each community type, transition the community to new state if conditions are met
        :return:
        """
        for index, row in self.community_table.iterrows():

            # CANOPY BASED SUCCESSION
            if row.succession_code == 1:
                self.ecocommunities[(self.ecocommunities == index) &
                                    (self.canopy > row['max_canopy'])] = row.to_ID

            # AGE BASED SUCCESSION
            elif row.succession_code == 2:
                self.ecocommunities = np.where((self.ecocommunities == index) &
                                                  (self.forest_age > row['age_out']),
                                                  self.climax_communities, self.ecocommunities)

    def run_succession(self):
        """

        :return:
        """

        self.grow()
        self.transition()

        out_raster = arcpy.NumPyArrayToRaster(in_array=self.ecocommunities,
                                              lower_left_corner=arcpy.Point(self.header['xllcorner'],
                                                                            self.header['yllcorner']),
                                              x_cell_size=self.header['cellsize'],
                                              value_to_nodata=-9999)

        out_raster.save(os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year))

        self.array_to_ascii(array=self.canopy, out_ascii_path=self.CANOPY_ascii)
        self.array_to_ascii(array=self.forest_age, out_ascii_path=self.FOREST_AGE_ascii)
        self.array_to_ascii(array=self.dbh, out_ascii_path=self.DBH_ascii, fmt='%10.4f')
    # s1 = Succession(1508)
    # print s1.succession_table.head()
    # s1.run_succession()
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
