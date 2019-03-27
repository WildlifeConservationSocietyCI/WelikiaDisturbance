import os
import utils


# GENERAL SETTINGS
DEBUG_MODE = False  # print more log lines, save more intermediate files
RUN_LENGTH = range(1409, 1411)  # start year to end year + 1 (range(1409, 1611) = years 1409 through 1610 inclusive)
# flags for whether to run each disturbance module
GARDEN = True
FIRE = True
POND = True


# PATHS AND NAMES
DATA_DIR = 'D:/_data/Welikia/WelikiaDisturbance/data'  # independent of code paths
INPUT_DIR_FULL = os.path.join(DATA_DIR, 'inputs_full_extent')
# 1: Manhattan; 2: Bronx; 3: Brooklyn/Queens; 4: Staten Island
REGION = 1
TRIAL_NAME = 'test'
FARSITE = 'C:/Program Files (x86)/FARSITE4/farsite4.exe'

# REQUIRED FULL-EXTENT INPUT GRIDS AND TABLES: THESE FILES MUST EXIST
ECOCOMMUNITIES_FE = os.path.join(INPUT_DIR_FULL, 'Welikia_Ecocommunities', 'Welikia_Ecocommunities_int.tif')
DEM_FE = os.path.join(INPUT_DIR_FULL, 'dem', 'WELIKIA_DEM_5m_BURNED_STREAMS_10ft_CLIP.tif')
SITES_FE = os.path.join(INPUT_DIR_FULL, 'garden_sites', 'GARDEN_SITES.shp')
BUFFER_FE = os.path.join(INPUT_DIR_FULL, 'garden_sites', 'SITE_BUFFER.shp')
TRAILS_FE = os.path.join(INPUT_DIR_FULL, 'trails', 'fire_trails.tif')
HUNTING_FE = os.path.join(INPUT_DIR_FULL, 'hunting_sites', 'hunting_sites.tif')
REGION_BOUNDARIES = os.path.join(INPUT_DIR_FULL, 'region_boundaries', 'disturbance_regions.shp')  # requires BoroName

COMMUNITY_TABLE = os.path.join(INPUT_DIR_FULL, 'tables', 'welikia_community_table_int.csv')
DBH_LOOKUP = os.path.join(INPUT_DIR_FULL, 'tables', 'dbh_lookup.csv')
PROXIMITY_RECLASS = os.path.join(INPUT_DIR_FULL, 'tables', 'garden', 'proximity_reclass.txt')
SLOPE_RECLASS = os.path.join(INPUT_DIR_FULL, 'tables', 'garden', 'slope_reclass.txt')
PSDI_YEARS = os.path.join(INPUT_DIR_FULL, 'tables', 'fire', 'psdi-years.txt')
DROUGHT_YEARS = os.path.join(INPUT_DIR_FULL, 'tables', 'fire', 'mannahatta-psdi.txt')

# Required by ancillary code (not disturbance model directly)
SITE_INDEX_PARAMETERS = os.path.join(INPUT_DIR_FULL, 'tables', 'site_index_curve_table.csv')
COEFFECIENTS = os.path.join(INPUT_DIR_FULL, 'tables', 'basal_area_growth_coeffecients.csv')

# SCENARIO SETTINGS

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

# FIRE
# initial conditions
MEAN_INITIAL_FOREST_AGE = 65
MINIMUM_FOREST_AGE = 20
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


# INTERNAL CONFIGURATION
trial = utils.format_str(TRIAL_NAME)[:20]
TRIAL_DIR = os.path.join(DATA_DIR, '{}_{}'.format(REGION, trial))
INPUT_DIR = os.path.join(TRIAL_DIR, 'inputs')
OUTPUT_DIR = os.path.join(TRIAL_DIR, 'outputs')
TEMP_DIR = os.path.join(DATA_DIR, 'temp')
FIRE_DIR = os.path.join(INPUT_DIR, 'fire')

# region-specific spatial inputs created by initiate_disturbance_inputs or manual farsite manipulation
# ecocommunities lifecycle:
# initial full extent ec: ECOCOMMUNITIES_FE
# modified full extent ec (initiate_disturbance_inputs): s.TEMP_DIR, 'ecocommunities_fe.tif'
# initial region ec (initiate_disturbance_inputs): ecocommunities below
# yearly output ecs (disturbance scripts): s.OUTPUT_DIR, self._ecocommunities_filename % self.year
ecocommunities = os.path.join(INPUT_DIR, 'ecocommunities.tif')
reference_ascii = os.path.join(INPUT_DIR, 'reference_grid.asc')

# initiate_disturbance_inputs creates these from full-extent inputs
dem_ascii = os.path.join(FIRE_DIR, 'dem.asc')
aspect_ascii = os.path.join(FIRE_DIR, 'aspect.asc')
slope_ascii = os.path.join(FIRE_DIR, 'slope.asc')
trails = os.path.join(FIRE_DIR, 'trails.tif')
hunting_sites = os.path.join(FIRE_DIR, 'hunting_sites.tif')
# paths to farsite files user must create manually, using paths below
fpj = os.path.join(FIRE_DIR, 'PROJECT.FPJ')
lcp = os.path.join(FIRE_DIR, 'LANDSCAPE.LCP')
# (These are the only examples of inputs that both have to exist prior to running AND get replaced during run)
fuel_ascii = os.path.join(FIRE_DIR, 'fuel.asc')
canopy_ascii = os.path.join(FIRE_DIR, 'canopy.asc')
ignition = os.path.join(FIRE_DIR, 'ignition.shp')
fmd = os.path.join(FIRE_DIR, 'custom_fuel_test.fmd')
fms = os.path.join(FIRE_DIR, 'fuel_moisture_test.fms')
adj = os.path.join(FIRE_DIR, 'fuel_adjustment.adj')
wnd = os.path.join(FIRE_DIR, 'wind.wnd')
wtr = os.path.join(FIRE_DIR, 'weather.wtr')
wtr_tables = os.path.join(INPUT_DIR_FULL, 'tables', 'fire', 'wtr')

dem = os.path.join(INPUT_DIR, 'pond', 'dem.tif')
flow_direction = os.path.join(INPUT_DIR, 'pond', 'flow_direction.tif')
stream_suitability = os.path.join(INPUT_DIR, 'pond', 'stream_suitability.tif')

slope_suitability = os.path.join(INPUT_DIR, 'garden', 'slope_suitability.tif')
proximity_suitability = os.path.join(INPUT_DIR, 'garden', 'proximity_suitability.tif')
garden_sites = os.path.join(INPUT_DIR, 'garden', 'garden_sites.shp')

# shared outputs
CANOPY = os.path.join(OUTPUT_DIR, 'canopy.tif')
FOREST_AGE = os.path.join(OUTPUT_DIR, 'forest_age.tif')
DBH = os.path.join(OUTPUT_DIR, 'dbh.tif')

# LOGGING
LOGFILE = os.path.join(DATA_DIR, '{}_{}.log'.format(REGION, trial))
