import os
import arcpy
from arcpy import env
import sys
import logging
import numpy

# TODO
# DIRECTORIES
TRIAL_NAME = 'test'

ROOT_DIR = os.path.join('')
INPUT_DIR = os.path.join(ROOT_DIR, 'inputs')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs')
TEMP_DIR = os.path.join(ROOT_DIR, 'temp')
LOG_DIR = r"%s" % TRIAL_NAME

REGION = '2'

ecocommunities = os.path.join(INPUT_DIR, '%s_ecocommunities.tif' % REGION)
community_table = os.path.join(ROOT_DIR, 'welikia_community_table.csv')
UPLAND_COMMUNITIES = [616, 621, 622, 625, 629, 632, 635, 644, 647, 648, 649, 650, 654, 733]
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
logging.basicConfig(filename=os.path.join(LOG_DIR, 'disturbance_log.txt'),
                    level=logging.DEBUG)

# PARAMETERS
# Trial
RUN_LENGTH = range(, )

# FIRE
# initial parameters
INITIAL_TIME_SINCE_DISTURBANCE = 20
TRAIL_OVERGROWN_YRS = 15

# duration settings
FIRE_SEASON_START = (1, 3)
FIRE_SEASON_END = (31, 5)

# Minimum amount of rain in 1/100" needed to extinguish a fire
CRITICAL_RAINFALL = 10

# Number of days used to condition fuel before the start of fire
CONDITIONING_LENGTH = 15

# escaped fire probabilities number of fires / km^2
EXPECTED_LIGHTNING_FIRE = 0.0005425
EXPECTED_TRAIL_ESCAPE = 
EXPECTED_GARDEN_ESCAPE = 
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
DENSITY = 0.4
MINIMUM_DISTANCE = 1000
POND_ABANDONMENT_PROBABILITY = 10
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

# Environment Setting

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to get spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)
