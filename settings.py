import os
import arcpy
from arcpy import env
import sys

# DIRECTORIES
ROOT_DIR = os.path.join('E:\\', '_data', 'welikia', 'WelikiaDisturbance')
# ROOT_DIR = os.path.join('E:\\', 'FIRE_MODELING', 'fire_model_python', '_bk_q_test_5m')
INPUT_DIR = os.path.join(ROOT_DIR, 'inputs')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs')
TEMP_DIR = os.path.join(ROOT_DIR, 'temp')

ecocommunities = os.path.join(INPUT_DIR, 'ecocommunities.tif')

INPUT_FILES = [
    ecocommunities,
]

# PARAMETERS
# Trial
RUN_LENGTH = range(1409, 1415)

## Fire
### initial parameters
INITIAL_TIME_SINCE_DISTURBANCE = 20
TRAIL_OVERGROWN_YRS = 15

### duration settings
FIRE_SEASON_START = (1, 3)
FIRE_SEASON_END = (31, 5)

### Rain in mm needed to extinguish a fire
EXTINGUISH_THRESHOLD = 5

### Number of days used to condition fuel before the start of fire
CONDITIONING_LENGTH = 15

### escaped fire probabilities
PROB_TRAIL_ESCAPE = 100
PROB_GARDEN_ESCAPE = 2.5
PROB_HUNT_ESCAPE = 10

### Un-burnable fuel types
UN_BURNABLE = [14, 16, 98, 99]

### succession
SUCCESSION_TIME_MID = 10
SUCCESSION_TIME_CLIMAX = 20

# GUI controls
INITIATE_RENDER_WAIT_TIME = 50

## Ponds
CARRYING_CAPACITY = 5
MINIMUM_DISTANCE = 1000
CELL_SIZE = 5
DAM_HEIGHT = 9

# Disturbance Class Test

class Disturbance(object):
    ROOT_DIR = ROOT_DIR
    INPUT_DIR = INPUT_DIR
    OUTPUT_DIR = OUTPUT_DIR

    def __init__(self):
        self.setup_dirs()
        self.check_inputs()

    # ensure that dir structure exists
    def setup_dirs(self):
        if not os.isdir(ROOT_DIR):
            pass

    def check_inputs(self):
        for file in INPUT_FILES:
            pass


# Environment Setting
env.workspace = TEMP_DIR
print env.workspace
env.scratchWorkspace = TEMP_DIR
print env.scratchWorkspace
env.overwriteOutput = True

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to get spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)
