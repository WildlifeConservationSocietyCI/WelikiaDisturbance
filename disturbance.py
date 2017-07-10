import os
import arcpy
import numpy as np
import settings as s
import utils
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
import pandas as pd
import scipy.stats as ss
import linecache

class Disturbance(object):

    def __init__(self, year):

        self.year = year

        # raster paths
        self.DEM_ascii = os.path.join(s.INPUT_DIR, 'fire', 'spatial', s.REGION, 'dem.asc')
        self.CANOPY_ascii = os.path.join(s.OUTPUT_DIR, 'canopy.asc')
        self.FOREST_AGE_ascii = os.path.join(s.OUTPUT_DIR, 'forest_age.asc')
        self.DBH_ascii = os.path.join(s.OUTPUT_DIR, 'dbh.asc')
        self._ecocommunities_filename = 'ecocommunities_%s.tif'

        # arrays
        self.ecocommunities = None
        self.ecocommunities_array = None
        self.forest_age = None
        self.canopy = None
        self.dbh = None

        # community info table
        self.community_table = pd.read_csv(s.community_table, index_col=0)

        self.upland_area = 0

        self.shape = None
        self.get_header()
        self.header, self.header_text, self.shape = utils.get_ascii_header(self.DEM_ascii)
        self.set_ecocommunities()
        self.set_canopy()
        self.set_forest_age()
        self.set_dbh()

    def set_ecocommunities(self):
        """
        set community raster for given year, if no raster exists use previous year,
        else: use initial conditions community raster
        """

        this_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year)
        last_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % (self.year - 1))

        if os.path.isfile(this_year_ecocomms):
            print this_year_ecocomms
            self.ecocommunities = arcpy.Raster(this_year_ecocomms)

        elif os.path.isfile(last_year_ecocomms):
            print last_year_ecocomms
            self.ecocommunities = arcpy.Raster(last_year_ecocomms)
        else:
            print 'initial run'
            self.ecocommunities = arcpy.Raster(s.ecocommunities)

        self.ecocommunities.save(os.path.join(s.TEMP_DIR, 'temp.tif'))

    def set_canopy(self):
        """
        set canopy for given year if no canopy raster exists, use previous year,
        else: initialize canopy raster
        :return:
        """

        if os.path.isfile(self.CANOPY_ascii):
            s.logging.info('Setting canopy')
            self.canopy = utils.raster_to_array(self.CANOPY_ascii)

        else:
            s.logging.info('Assigning initial values to canopy array')
            if self.ecocommunities_array is None:
                self.ecocommunities_array = arcpy.RasterToNumPyArray(self.ecocommunities)

            self.canopy = np.empty((self.header['nrows'], self.header['ncols']))

            # random canopy values for forests, shrublands and grasslands
            # f = np.random.randint(low=51, high=100, size=(self.header['nrows'], self.header['ncols']))
            # sh = np.random.randint(low=17, high=50, size=(self.header['nrows'], self.header['ncols']))
            # g = np.random.randint(low=1, high=16, size=(self.header['nrows'], self.header['ncols']))
            for index, row in self.community_table.iterrows():
                self.canopy[self.ecocommunities_array == index] = row.max_canopy
                # print row.max_canopy, type(row.max_canopy)
                # if row.max_canopy > 50:
                #     self.canopy = np.where(self.ecocommunities_array == index, f, self.canopy)
                # elif 20 < row.max_canopy <= 50:
                #     self.canopy = np.where(self.ecocommunities_array == index, sh, self.canopy)
                # elif 0 < int(row.max_canopy) <= 20:
                #     self.canopy = np.where(self.ecocommunities_array == index, g, self.canopy)
                # elif row.max_canopy == 0:
                #     self.canopy[self.ecocommunities_array == index] = row.max_canopy

            utils.array_to_ascii(self.CANOPY_ascii, self.canopy, header=self.header)

    def set_forest_age(self):
        """
        set forest age for given year, if no forest age raster exists, use previous year,
        else: initialize forest age raster
        :return:
        """
        if os.path.isfile(self.FOREST_AGE_ascii):
            s.logging.info('Setting forest age')
            self.forest_age = utils.raster_to_array(self.FOREST_AGE_ascii)

        else:
            s.logging.info('Assigning initial values to forest age array')
            if self.ecocommunities_array is None:
                self.ecocommunities_array = arcpy.RasterToNumPyArray(self.ecocommunities)


            # create truncated normal distrbution for age
            lower = s.MINIMUM_FOREST_AGE
            upper = s.UPPER
            mu = s.MEAN_INITIAL_FOREST_AGE
            sigma = s.AGE_VAR

            n = ss.truncnorm((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)

            # populate an array with ages from distribution
            tn = n.rvs(self.shape).astype(int)

            self.forest_age = np.empty(shape=self.shape, dtype=int)

            # replace reset age for non-forest communities
            for index, row in self.community_table.iterrows():
                if row.forest == 1:
                    self.forest_age = np.where(self.ecocommunities_array == index, tn, self.forest_age)

            utils.array_to_ascii(self.FOREST_AGE_ascii, self.forest_age, header=self.header_text)

    def set_dbh(self):
        """
        set DBH raster, if no raster exists initialize using age raster and age_dbh_lookup table
        :return:
        """
        if os.path.isfile(self.DBH_ascii):
            s.logging.info('Setting dbh')
            self.dbh = utils.raster_to_array(self.DBH_ascii)

        else:
            s.logging.info('Assigning initial values to dbh array')
            self.dbh = np.empty(shape=self.shape, dtype=np.float16)
            age_dbh_lookup = pd.read_csv(os.path.join(s.ROOT_DIR, 'tables', 'dbh_lookup.csv'), index_col=0)

            for index, row in self.community_table.iterrows():
                print("forest: %s" % row.forest)
                print("bool: ", row.forest == 1)
                if row.forest == 1:
                    age = np.ma.masked_where(self.ecocommunities_array != index, self.forest_age)
                    print(index)
                    print(np.unique(age))
                    for a in np.ma.compressed(np.unique(age)):
                        print(a)
                        d = age_dbh_lookup.ix[int(a)][str(index)]
                        self.dbh[(self.ecocommunities_array == index) & (self.forest_age == a)] = d

            utils.array_to_ascii(self.DBH_ascii, self.dbh, header=self.header_text, fmt="%2.4f")

    def set_upland_area(self):
        if type(self.ecocommunities) is np.ndarray:
            unique = np.unique(self.ecocommunities, return_counts=True)
        else:
            unique = np.unique(arcpy.RasterToNumPyArray(self.ecocommunities), return_counts=True)
        area_hist = dict(zip(unique[0], (unique[1] * (s.CELL_SIZE ** 2) / 1000000.0)))
        for index, row in self.community_table.iterrows():
            if row.upland == 1 and index in area_hist:
                self.upland_area += area_hist[index]


def hist(a):
    if type(a) is np.ndarray:
        values, counts = np.unique(a, return_counts=True)
    else:
        values, counts = np.unique(arcpy.RasterToNumPyArray(a, nodata_to_value=-9999), return_counts=True)
    return dict(zip(values, counts))
