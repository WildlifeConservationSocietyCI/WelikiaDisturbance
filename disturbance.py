import os
import logging
import arcpy
import numpy as np
import pandas as pd
import scipy.stats as ss
import settings as s
# import utils


class Disturbance(object):
    REFERENCE = s.ecocommunities

    def __init__(self, year):
        self.year = year
        self._ecocommunities_filename = 'ecocommunities_%s.tif'

        self.ecocommunities = None
        self.ecocommunities_array = None
        self.forest_age = None
        self.canopy = None
        self.dbh = None

        self.community_table = pd.read_csv(s.COMMUNITY_TABLE, index_col=0)
        self.dbh_lookup = pd.read_csv(s.DBH_LOOKUP, index_col=0)

        self.upland_area = 0
        refarray = arcpy.RasterToNumPyArray(self.REFERENCE)
        self.shape = refarray.shape
        # self.shape = utils.raster_to_array(self.REFERENCE).shape
        # self.geot, self.projection = utils.get_geo_info(self.REFERENCE)
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
            logging.info('disturbance set eco, using this year: {}'.format(this_year_ecocomms))
            self.ecocommunities = arcpy.Raster(this_year_ecocomms)

        elif os.path.isfile(last_year_ecocomms):
            logging.info('disturbance set eco using last year: {}'.format(last_year_ecocomms))
            self.ecocommunities = arcpy.Raster(last_year_ecocomms)
        else:
            logging.info('disturbance set eco initial run')
            self.ecocommunities = arcpy.Raster(s.ecocommunities)

        # self.ecocommunities.save(os.path.join(s.TEMP_DIR, 'temp.tif'))

    def set_canopy(self):
        """
        set canopy for given year if no canopy raster exists, use previous year,
        else: initialize canopy raster
        :return:
        """

        if os.path.isfile(s.CANOPY):
            logging.info('Setting canopy')
            # self.canopy = utils.raster_to_array(s.CANOPY)
            self.canopy = arcpy.RasterToNumPyArray(s.CANOPY)

        else:
            logging.info('Assigning initial values to canopy array')
            if self.ecocommunities_array is None:
                self.ecocommunities_array = arcpy.RasterToNumPyArray(self.ecocommunities)

            self.canopy = np.empty(self.shape, dtype=np.int8)

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

            canopy = arcpy.NumPyArrayToRaster(self.canopy, x_cell_size=s.CELL_SIZE, y_cell_size=s.CELL_SIZE)
            canopy.save(s.CANOPY)
            # utils.array_to_raster(self.canopy, s.CANOPY,
            #                       geotransform=self.geot, projection=self.projection)

    def set_forest_age(self):
        """
        set forest age for given year, if no forest age raster exists, use previous year,
        else: initialize forest age raster
        :return:
        """
        if os.path.isfile(s.FOREST_AGE):
            logging.info('Setting forest age')
            self.forest_age = arcpy.RasterToNumPyArray(s.FOREST_AGE)
            # self.forest_age = utils.raster_to_array(s.FOREST_AGE)

        else:
            logging.info('Assigning initial values to forest age array')
            if self.ecocommunities_array is None:
                self.ecocommunities_array = arcpy.RasterToNumPyArray(self.ecocommunities)

            # create truncated normal distrbution for age
            lower = s.MINIMUM_FOREST_AGE
            upper = s.MAXIMUM_FOREST_AGE
            mu = s.MEAN_INITIAL_FOREST_AGE
            sigma = s.AGE_VAR

            n = ss.truncnorm((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)

            # populate an array with ages from distribution
            tn = n.rvs(self.shape).astype(int)

            self.forest_age = np.empty(shape=self.shape, dtype=np.int16)

            # replace reset age for non-forest communities
            for index, row in self.community_table.iterrows():
                if row.forest == 1:
                    self.forest_age = np.where(self.ecocommunities_array == index, tn, self.forest_age)

            forestage = arcpy.NumPyArrayToRaster(self.forest_age, x_cell_size=s.CELL_SIZE, y_cell_size=s.CELL_SIZE)
            forestage.save(s.FOREST_AGE)
            # utils.array_to_raster(self.forest_age, s.FOREST_AGE,
            #                       geotransform=self.geot, projection=self.projection)

    def set_dbh(self):
        """
        set DBH raster, if no raster exists initialize using age raster and dbh_lookup table
        :return:
        """
        if os.path.isfile(s.DBH):
            logging.info('Setting dbh')
            self.dbh = arcpy.RasterToNumPyArray(s.DBH)
            # self.dbh = utils.raster_to_array(s.DBH)

        else:
            logging.info('Assigning initial values to dbh array')
            self.dbh = np.empty(shape=self.shape, dtype=np.float32)

            for index, row in self.community_table.iterrows():
                # print("forest: %s" % row.forest)
                # print("bool: ", row.forest == 1)
                if row.forest == 1:
                    assert isinstance(self.ecocommunities_array, np.ndarray)
                    age = np.ma.masked_where(self.ecocommunities_array != index, self.forest_age)
                    # print(index)
                    # print(np.unique(age))
                    for a in np.ma.compressed(np.unique(age)):
                        d = self.dbh_lookup.ix[int(a)][str(index)]
                        self.dbh[(self.ecocommunities_array == index) & (self.forest_age == a)] = d

            dbh = arcpy.NumPyArrayToRaster(self.dbh, x_cell_size=s.CELL_SIZE, y_cell_size=s.CELL_SIZE)
            dbh.save(s.DBH)
            # utils.array_to_raster(self.dbh, s.DBH,
            #                       geotransform=self.geot, projection=self.projection)  # , dtype=gdal.GDT_Float32)

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
