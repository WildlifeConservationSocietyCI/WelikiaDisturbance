import os
import arcpy
from arcpy import env
import sys
import logging

# TODO
# DIRECTORIES
ROOT_DIR = os.path.join('E:\\', '_data', 'welikia', 'WelikiaDisturbance')
INPUT_DIR = os.path.join(ROOT_DIR, 'inputs')
OUTPUT_DIR = os.path.join(r"E:\_data\welikia\disturbance_log\sensitivity_tests\per-capita_garden_area\200_yr_trial_dependence_60\outputs")
TEMP_DIR = os.path.join(ROOT_DIR, 'temp')
LOG_DIR = r'C:\Users\LabGuest\Dropbox\disturbance_logs\sensitivity_tests\per-capita_garden_area\200_yr_trial_dependence_60'

REGION = '2'

ecocommunities = os.path.join(INPUT_DIR, '%s_ecocommunities.tif' % REGION)
UPLAND_COMMUNITIES = [616, 621, 622, 625, 629, 632, 635, 644, 647, 649, 650, 654]
INPUT_FILES = [
    ecocommunities
]

#
DEBUG_MODE = False

# DISTURBANCE FLAG TOGGLE
GARDEN = True
FIRE = True
POND = False

# LOGGING
logging.basicConfig(filename=os.path.join(LOG_DIR, 'disturbance_log.txt'),
                    level=logging.DEBUG)

# PARAMETERS
# Trial
RUN_LENGTH = range(1409, 1420)

# FIRE
# initial parameters
INITIAL_TIME_SINCE_DISTURBANCE = 20
TRAIL_OVERGROWN_YRS = 15

# duration settings
FIRE_SEASON_START = (1, 3)
FIRE_SEASON_END = (31, 5)

# Rain in mm needed to extinguish a fire
EXTINGUISH_THRESHOLD = 10

# Number of days used to condition fuel before the start of fire
CONDITIONING_LENGTH = 15

# escaped fire probabilities number of fires / km^2
EXPECTED_LIGHTNING_FIRE = 0.0005425
EXPECTED_TRAIL_ESCAPE = 0.002222222222
EXPECTED_GARDEN_ESCAPE = 0.0002777777778
# PROB_HUNT_ESCAPE = 10

# nonburnable fuel types
NONBURNABLE = [14, 16, 98, 99]

# fuel accumulation time
TIME_TO_MID_FUEL = 20
TIME_TO_CLIMAX_FUEL = 80

# canopy based succession
SHRUBLAND_CANOPY = 10

# GUI controls
INITIATE_RENDER_WAIT_TIME = 10
SIMULATION_TIMEOUT = 100000

# PONDS
# carrying capacity is
DENSITY = 0.8
MINIMUM_DISTANCE = 1000
CELL_SIZE = 5
DAM_HEIGHT = 9

# GARDENS
PROXIMITY_BUFFER = 500
PER_CAPITA_GARDEN_AREA = 15
REQUIREMENT_VARIANCE = range(-5, 6)
ABANDONMENT_PROBABILITY = 5

# TIME_TO_ABANDON = 20
# SHRUB_SUCCESSION = 36
# FOREST_SUCCESSION = 80

# COMMUNITY CODES
GARDEN_ID = 650  # ecosystem id for gardens (will look for this value when processing raster.
GRASSLAND_ID = 635  # 648  # ecosystem id for abandoned fields.
SHRUBLAND_ID = 649


# Disturbance Class Test

class Disturbance(object):
    ROOT_DIR = ROOT_DIR
    INPUT_DIR = INPUT_DIR
    OUTPUT_DIR = OUTPUT_DIR

    def __init__(self, year):
        self.setup_dirs()
        self.check_inputs()


    # ensure that dir structure exists
    def setup_dirs(self):
        if not os.path.isdir(ROOT_DIR):
            pass

    def check_inputs(self):
        for file in INPUT_FILES:
            pass


# Environment Setting

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to get spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)
