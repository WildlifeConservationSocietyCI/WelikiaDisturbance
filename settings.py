import os
import arcpy
from arcpy import env
import sys
import logging
import numpy


# DIRECTORIES
TRIAL_NAME = 'test'

ROOT_DIR = os.path.join(r'F:\_data\Welikia\WelikiaDisturbance')
REGION = '1'
INPUT_DIR = os.path.join(ROOT_DIR, 'inputs')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs', REGION)
TEMP_DIR = os.path.join(ROOT_DIR, 'temp')
LOG_DIR = r"F:\_data\Welikia\disturbance_logs\%s" % TRIAL_NAME

ecocommunities = os.path.join(INPUT_DIR, '%s_ecocommunities_int.tif' % REGION)
community_table = os.path.join(ROOT_DIR, 'welikia_community_table_int.csv')


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
RUN_LENGTH = range(1409, 1610)

# FIRE
# initial parameters
# initial conditions
INITIAL_TIME_SINCE_DISTURBANCE = 20
TRAIL_OVERGROWN_YRS = 20

# duration settings
FIRE_SEASON_START = (1, 3)
FIRE_SEASON_END = (31, 5)

# model parameters (m)
PERIMETER_RESOLUTION = 20
DISTANCE_RESOLUTION = 10

# Minimum amount of rain in 1/100" needed to extinguish a fire
CRITICAL_RAINFALL = 10

# Number of days used to condition fuel before the start of fire
CONDITIONING_LENGTH = 15

# escaped fire probabilities number of fires / km^2
EXPECTED_LIGHTNING_FIRE = 0.0005425
EXPECTED_TRAIL_ESCAPE = 0.001222222222
EXPECTED_GARDEN_ESCAPE = 0.0001777777778
# PROB_HUNT_ESCAPE = 10

# nonburnable fuel types
#TODO check these types
NONBURNABLE = [14, 15, 16, 98, 99]

# fuel accumulation time
TIME_TO_MID_FUEL = 10
TIME_TO_CLIMAX_FUEL = 20

# canopy based succession
SHRUBLAND_CANOPY = 10

# GUI controls
INITIATE_RENDER_WAIT_TIME = 20
SIMULATION_TIMEOUT = 100000

# PONDS
# density: number of ponds/km^2
DENSITY = 0.4
# minimum distance: used to buffer out from existing ponds to create territories
MINIMUM_DISTANCE = 1000
POND_ABANDONMENT_PROBABILITY = 10
CELL_SIZE = 5
DAM_HEIGHT = 9

# GARDENS
PROXIMITY_BUFFER = 500
PER_CAPITA_GARDEN_AREA = 15
REQUIREMENT_VARIANCE = range(-5, 6)
ABANDONMENT_PROBABILITY = 5


# COMMUNITY CODES
GARDEN_ID = 65000
SUCCESSIONAL_OLD_FIELD_ID = 64800
SUCCESSIONAL_GRASSLAND_ID = 63500
SUCCESSIONAL_SHRUBLAND_ID = 64900
SUCCESSIONAL_HARDWOOD_FOREST_ID = 73600

ACTIVE_BEAVER_POND_ID = 73700
SHALLOW_EMERGENT_MARSH_ID = 62400
SHRUB_SWAMP_ID = 62500
RED_MAPLE_HARDWOOD_SWAMP = 62900
ATLANTIC_CEDAR_SWAMP = 70900
RED_MAPLE_BLACK_GUM_SWAMP = 71000
RED_MAPLE_SWEETGUM_SWAMP = 71001


# Environment Setting

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to get spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)
