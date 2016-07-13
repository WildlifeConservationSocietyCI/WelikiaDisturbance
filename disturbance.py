import os
import arcpy
import numpy as np
import settings as s
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
import pandas as pd
import linecache

class Disturbance(object):

    def __init__(self, year):

        self.year = year
        # self.check_inputs()
        self.DEM_ascii = os.path.join(s.INPUT_DIR, 'fire', 'spatial', s.REGION, 'dem.asc')
        self.CANOPY_ascii = os.path.join(s.OUTPUT_DIR, 'canopy.asc')
        self.FOREST_AGE_ascii = os.path.join(s.OUTPUT_DIR, 'forest_age.asc')
        self._ecocommunities_filename = 'ecocommunities_%s.tif'

        self.ecocommunities = None

        # arrays
        self.forest_age = None
        self.canopy = None

        self.upland_area = 0

        self.translation_table = pd.read_csv(os.path.join(s.ROOT_DIR, 'ec_translator.txt'),
                                             delim_whitespace=True, index_col='ec_id')

        self.get_header()
        self.set_ecocommunities()
        self.ecocommunities_array = arcpy.RasterToNumPyArray(self.ecocommunities)
        self.set_forest_age()
        self.set_canopy()

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

    def raster_to_array(self, in_raster):
        """
        convert ascii grid in to numpy array
        :type in_ascii: object
        """
        # print in_ascii
        ascii = gdal.Open(in_raster, GA_ReadOnly)
        array = gdal_array.DatasetReadAsArray(ascii)

        return array

    def array_to_ascii(self, out_ascii_path, array):
        """

        :rtype: object
        """
        out_asc = open(out_ascii_path, 'w')
        for attribute in self.header_text:
            out_asc.write(attribute)

        np.savetxt(out_asc, array, fmt="%4i")
        out_asc.close()

    def set_ecocommunities(self):
        """
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
            # self.ecocommunities.save(os.path.join(self.OUTPUT_DIR, self._ecocommunities_filename % self.year))

    def set_canopy(self):

        if os.path.isfile(self.CANOPY_ascii):
            s.logging.info('Setting canopy')
            self.canopy = self.raster_to_array(self.CANOPY_ascii)

        else:
            s.logging.info('Assigning initial values to canopy array')
            self.canopy = np.empty((self.header['nrows'], self.header['ncols']))

            # for key in self.translation_table.keys():
            for key in self.translation_table.index:
                self.canopy = np.where((self.ecocommunities_array == key),
                                          self.translation_table.ix[key]['max_canopy'], self.canopy)

            self.array_to_ascii(self.CANOPY_ascii, self.canopy)

    def set_forest_age(self):

        if os.path.isfile(self.FOREST_AGE_ascii):
            s.logging.info('Setting forest age')
            self.forest_age = self.raster_to_array(self.FOREST_AGE_ascii)

        else:
            s.logging.info('Assigning initial values to forest age array')
            self.forest_age = np.empty((self.header['nrows'], self.header['ncols']))

            for key in self.translation_table.index:
                self.forest_age = np.where((self.ecocommunities_array == key),
                                              self.translation_table.ix[key]['start_age'], self.forest_age)

            self.array_to_ascii(self.FOREST_AGE_ascii, self.forest_age)

    # ensure that dir structure exists
    # def setup_dirs(self):
    #     if not os.path.isdir(ROOT_DIR):
    #         pass
    #
    # def check_inputs(self):
    #     for file in INPUT_FILES:
    #         pass

    def set_upland_area(self):
        if type(self.ecocommunities) is np.ndarray:
            unique = np.unique(self.ecocommunities, return_counts=True)
        else:
            unique = np.unique(arcpy.RasterToNumPyArray(self.ecocommunities), return_counts=True)
        d = dict(zip(unique[0], (unique[1] * (s.CELL_SIZE ** 2) / 1000000.0)))
        for i in s.UPLAND_COMMUNITIES:
            if i in d.keys():
                self.upland_area += d[i]

# dis = Disturbance(1409)
# dis.get_header()
# dis.set_ecocommunities()
# dis.set_forest_age()
# dis.set_canopy()