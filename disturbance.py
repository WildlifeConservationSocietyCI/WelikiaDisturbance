import os
import arcpy
from arcpy import env
import sys
import logging
import numpy
import settings as s


class Disturbance(object):

    def __init__(self, year):
        self.year = year
        self.setup_dirs()
        self.check_inputs()
        self.ecocommunities = None
        self._ecocommunities_filename = '%_ecocommunities.tif'
        self.upland_area = 0
        self.set_upland_area()

    def set_ecocommunities(self):
        """

        :return:
        """

        this_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year)
        last_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % (self.year - 1))

        if os.path.isfile(this_year_ecocomms):
            # print this_year_ecocomms
            self.ecocommunities = arcpy.Raster(this_year_ecocomms)

        elif os.path.isfile(last_year_ecocomms):
            # print last_year_ecocomms
            self.ecocommunities = arcpy.Raster(last_year_ecocomms)
        else:
            print 'initial run'
            self.ecocommunities = arcpy.Raster(s.ecocommunities)
            # self.ecocommunities.save(os.path.join(self.OUTPUT_DIR, self._ecocommunities_filename % self.year))

    # ensure that dir structure exists
    def setup_dirs(self):
        if not os.path.isdir(ROOT_DIR):
            pass

    def check_inputs(self):
        for file in INPUT_FILES:
            pass

    def set_upland_area(self):
        unique = numpy.unique(self.ecocommunities, return_counts=True)
        d = dict(zip(unique[0], (unique[1] * (s.CELL_SIZE ** 2) / 1000000.0)))
        for i in s.UPLAND_COMMUNITIES:
            if i in d.keys():
                self.upland_area += d[i]