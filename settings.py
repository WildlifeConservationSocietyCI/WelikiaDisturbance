import os
import arcpy
from arcpy import env
import sys
import logging
import numpy


# DIRECTORIES
TRIAL_NAME = ''
LOG_DIR = '%s' % TRIAL_NAME

try:
    from settings_local import *
except ImportError, e:
    pass

INPUT_DIR_REGION = os.path.join(ROOT_DIR, 'inputs_region')
INPUT_DIR_FULL = os.path.join(ROOT_DIR, 'inputs_full_extent')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs', REGION)
TEMP_DIR = os.path.join(ROOT_DIR, 'temp')

ecocommunities = os.path.join(INPUT_DIR_REGION, '%s_ecocommunities_int.tif' % REGION)
community_table = os.path.join(INPUT_DIR_FULL, 'tables', 'welikia_community_table_int.csv')


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
# initial conditions
MEAN_INITIAL_FOREST_AGE = 0
MINIMUM_FOREST_AGE = 0
MAXIMUM_FOREST_AGE = 200
AGE_VAR = 1
INITIAL_TIME_SINCE_DISTURBANCE = 20
TRAIL_OVERGROWN_YRS = 20

# duration settings
FIRE_SEASON_START = (1, 3)
FIRE_SEASON_END = (31, 5)

# model parameters (m)
PERIMETER_RESOLUTION = 20
DISTANCE_RESOLUTION = 10
FARSITE_RESOLUTION = 10

# Minimum amount of rain in 1/100" needed to extinguish a fire
CRITICAL_RAINFALL = 10

# Number of days used to condition fuel before the start of fire
CONDITIONING_LENGTH = 15

# escaped fire probabilities number of fires / km^2
EXPECTED_LIGHTNING_FIRE = 0.0005425
EXPECTED_TRAIL_ESCAPE = 0.00475
EXPECTED_GARDEN_ESCAPE = 0
EXPECTED_HUNTING_ESCAPE = 0

# nonburnable fuel type
NONBURNABLE = [14, 15, 16, 98, 99]

# fuel accumulation time
TIME_TO_MID_FUEL = 10
TIME_TO_CLIMAX_FUEL = 20

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
POPULATION_VARIATION = range(-5, 6)
ABANDONMENT_PROBABILITY = 5


# COMMUNITY CODES
GARDEN_ID = 65000
TRAIL_ID = 1
HUNTING_SITE_ID = 1
SUCCESSIONAL_OLD_FIELD_ID = 64800
SUCCESSIONAL_GRASSLAND_ID = 63500
SUCCESSIONAL_SHRUBLAND_ID = 64900
SUCCESSIONAL_HARDWOOD_FOREST_ID = 73600

ACTIVE_BEAVER_POND_ID = 62201
SHALLOW_EMERGENT_MARSH_ID = 62400
SHRUB_SWAMP_ID = 62500
RED_MAPLE_HARDWOOD_SWAMP = 62900
ATLANTIC_CEDAR_SWAMP = 70900
RED_MAPLE_BLACK_GUM_SWAMP = 71000
RED_MAPLE_SWEETGUM_SWAMP = 71001


# Scenario Settings

try:
    from settings_scenario import *
except ImportError, e:
    pass