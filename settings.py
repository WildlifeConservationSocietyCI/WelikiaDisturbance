import os
import arcpy
from arcpy import env
import sys
import logging

# DIRECTORIES
ROOT_DIR = os.path.join('D:\\', '_data', 'Welikia', 'WelikiaDisturbance')
INPUT_DIR = os.path.join(ROOT_DIR, 'inputs')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs')
TEMP_DIR = os.path.join(ROOT_DIR, 'temp')
LOG_DIR = os.path.join('C:\\', 'Users', 'Kim', 'Dropbox')

REGION = '2'

ecocommunities = os.path.join(INPUT_DIR, '%s_ecocommunities.tif' % REGION)

INPUT_FILES = [
    ecocommunities
]

#
DEBUG_MODE = False

# DISTURBANCE FLAG TOGGLE
GARDEN = True
FIRE = True
POND = True

# LOGGING
logging.basicConfig(filename=os.path.join(LOG_DIR, 'disturbance_logs', 'kane_test_2', 'disturbance_log.txt'),
                    level=logging.DEBUG)

# PARAMETERS
# Trial
RUN_LENGTH = range(1409, 1610)

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

# escaped fire probabilities
EXPECTED_TRAIL_ESCAPE = 0.25
EXPECTED_GARDEN_ESCAPE = 0.02
PROB_HUNT_ESCAPE = 10

# nonburnable fuel types
NONBURNABLE = [14, 16, 98, 99]

# fuel accumulation time
TIME_TO_MID_FUEL = 20
TIME_TO_CLIMAX_FUEL = 80

# canopy based succession
SHRUBLAND_CANOPY = 10

# GUI controls
INITIATE_RENDER_WAIT_TIME = 10
SIMULATION_TIMEOUT = 5000

# PONDS
CARRYING_CAPACITY = 35
MINIMUM_DISTANCE = 1000
CELL_SIZE = 5
DAM_HEIGHT = 9

# GARDENS
PROXIMITY_BUFFER = 500
PER_CAPITA_GARDEN_AREA = 1

TIME_TO_ABANDON = 20
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
