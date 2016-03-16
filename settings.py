import posixpath as os


# DIRECTORIES
ROOT_DIR = os.join('E:', '_data', 'welikia', 'WelikiaDisturbances')
INPUT_DIR = os.join(ROOT_DIR, 'inputs')
OUTPUT_DIR = os.join(ROOT_DIR, 'outputs')

# PARAMETERS
# Trial
RUN_LENGTH = range(1409, 1509)

## Fire
### initial parameters
INITIAL_TIME_SINCE_DISTURBANCE = 20
TRAIL_OVERGROWN_YRS = 15

### duration settings
FIRE_SEASON_START = (1, 3)
FIRE_SEASON_END = (31, 5)

### Rain in mm needed to extinguish a fire
EXTINGUISH_THRESHOLD = 100

### Number of days used to condition fuel before the start of fire
CONDITIONING_LENGTH = 15

### escaped fire probabilities
PROB_TRAIL_ESCAPE = 10
PROB_GARDEN_ESCAPE = 2.5
PROB_HUNT_ESCAPE = 10

### Un-burnable fuel types
UN_BURNABLE = [14, 16, 98, 99]

### succession
SUCCESSION_TIME_MID = 10
SUCCESSION_TIME_CLIMAX = 20

## Ponds
CARRYING_CAPACITY = 100
MINIMUM_DISTANCE = 1000
CELL_SIZE = 5
DAM_HEIGHT = 9