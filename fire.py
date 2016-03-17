import settings as s
from settings import os
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
import numpy

class FireDisturbance(s.Disturbance):
    
    # CLASS VARIABLES

    # Directories
    ROOT_DIR = os.join(s.ROOT_DIR, 'fire')
    INPUT_DIR = os.join(ROOT_DIR, 'inputs')
    OUTPUT_DIR = os.join(ROOT_DIR, 'outputs')
    TEMP_DIR = os.join(ROOT_DIR, 'temp')

    #initial parameters
    INITIAL_TIME_SINCE_DISTURBANCE = 20
    TRAIL_OVERGROWN_YRS = 15
    
    #duration settings
    FIRE_SEASON_START = (1, 3)
    FIRE_SEASON_END = (31, 5)
    
    #Rain in mm needed to extinguish a fire
    EXTINGUISH_THRESHOLD = 100
    
    #Number of days used to condition fuel before the start of fire
    CONDITIONING_LENGTH = 15
    
    #escaped fire probabilities
    PROB_TRAIL_ESCAPE = 10
    PROB_GARDEN_ESCAPE = 2.5
    PROB_HUNT_ESCAPE = 10
    
    #Un-burnable fuel types
    UN_BURNABLE = [14, 16, 98, 99]
    
    #succession
    SUCCESSION_TIME_MID = 10
    SUCCESSION_TIME_CLIMAX = 20

    # Inputs
    DEM_ascii = None
    SLOPE_ascii = None
    ASPECT_ascii = None



    def __init__(self):
        self.drought = None
        self.climate_years = None
        self.translation_table = None
        self.header = None
        self.canopy = None
        self.time_since_disturbance = None
        self.fuel = None
        self.camps = None
        self.ignition_sites = None


    def get_header(self):
        self.header = ''

    def get_translation_table(self):
        translation = {}

        with open(os.join(self.INPUT_DIR, 'mannahatta.ec.translators.2.txt'), 'r') as translation_file:

            for line in translation_file:
                ecid, fuel2, fuel1, fuel10, can_val, first_age, for_bin, forshrubin, obstruct_bin = line.split('\t')

                ecid = int(ecid)
                translation[ecid] = {}

                translation[ecid]['climax_fuel'] = int(fuel2)
                translation[ecid]['mid_fuel'] = int(fuel1)
                translation[ecid]['new_fuel'] = int(fuel10)
                translation[ecid]['max_canopy'] = int(can_val)
                translation[ecid]['start_age'] = int(first_age)
                translation[ecid]['forest'] = int(for_bin)
                translation[ecid]['forest_shrub'] = int(forshrubin)
                translation[ecid]['obstruct'] = int(obstruct_bin)

        self.translation_table = translation

    def get_drought(self):
        drought = {}
        with open(os.join(self.INPUT_DIR, 'mannahatta-psdi.txt'), 'r') as drought_file:
            for line in drought_file:
                year, psdi = line.split('\t')
                drought[int(year)] = float(psdi)

        self.drought = drought

    def get_climate_years(self):
        climate_years = {}
        with open(os.join(self.INPUT_DIR, 'psdi-years.txt'), 'r') as psdiyears_file:
            for line in psdiyears_file:
                c_list = line.strip('\n').split('\t')
                climate_years[float(c_list[0])] = []
                for year in c_list[1:]:
                    if year != '':
                        climate_years[float(c_list[0])].append(int(year))

        self.climate_years = climate_years

    def ascii_to_array(self, in_ascii_path):
        ascii = gdal.Open(in_ascii_path, GA_ReadOnly)
        array = gdal_array.DatasetReadAsArray(ascii)
        return array

    def array_to_ascii(self, out_ascii_path, array):
        out_asc = open(out_ascii_path, 'w')
        for attribute in self.header:
            out_asc.write(attribute)

        numpy.savetxt(out_asc, array, fmt="%4i")
        out_asc.close()
