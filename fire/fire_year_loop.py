__author__ = 'Jesse Moy'

import datetime
import linecache
import shutil
import arcpy
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
from wmi import WMI
from run_farsite import *
from tree_mortality import *
from array_to_raster import *
from ecosystem_to_fuel import *


# Methods
def memory():

    # Reports current memory usage

    w = WMI('.')
    result = w.query("SELECT WorkingSet FROM Win32_PerfRawData_PerfProc_Process WHERE IDProcess=%d" % os.getpid())
    return int(result[0].WorkingSet) / 1000000.0


def write_ignition():

    # Writes ignition site as vct file for FARSITE and shp file for logging

    with open((input_dir + '/farsite/ignition.vct'), 'w') as ignition_file:
        x = (h['xllcorner'] + (h['cellsize'] * ignition_site[1]))
        y = (h['yllcorner'] + (h['cellsize'] * (h['nrows'] - ignition_site[0])))

        ignition_file.write('1 %s %s\nEND' % (x, y))

        # Log ignition site
        shutil.copyfile((input_dir + '/farsite/ignition.vct'),
                        (output_dir + '/log_rasters/%r_ignition.vct' % year))

        # Log as a point
        point = arcpy.Point()
        point.X = x
        point.Y = y
        ptGeoms = arcpy.PointGeometry(point)

        arcpy.CopyFeatures_management(ptGeoms, (output_dir + '/log_rasters/%r_ignition.shp' % year))


def write_wnd():

    # Generates a random wnd file for FARSITE

    with open((input_dir + '/farsite/weather.wtr'), 'r') as weather_file:
        with open((input_dir + '/farsite/wind.wnd'), 'w') as wind_file:
            for line in weather_file:
                line_split = line.split(' ')
                if line_split[0] != 'ENGLISH':
                    month = line_split[0]
                    day = line_split[1]
                    for i in range(1, 5):
                        hour = i * 600 - 41
                        speed = random.choice(range(1, 15))
                        direction = random.choice(range(0, 360))
                        cloud_cover = 20
                        wind_file.write('%s %s %r %r %r %r\n' % (month, day, hour, speed, direction, cloud_cover))


def select_climate_records():

    # Finds similar climate records based on PSDI

    psdi = drought[year]
    logging.info('Drought(PSDI): %r' % psdi)
    potential_years = []
    for climate_year in climate_years[psdi]:
        if 1876 <= climate_year <= 2006:
            potential_years.append(climate_year)

    # If a year doesn't have an equivalent climate year based on PSDI
    # Select equivalent from years with PSDI +/- 0.5
    if len(potential_years) == 0:
        for climate_year in climate_years[psdi + 0.5]:
            if 1876 <= climate_year <= 2006:
                potential_years.append(climate_year)

        for climate_year in climate_years[psdi - 0.5]:
            if 1876 <= climate_year <= 2006:
                potential_years.append(climate_year)

    return random.choice(potential_years)

# Directories
# Brooklyn Queens landmass test directories
input_dir = 'E:/FIRE_MODELING/fire_model_python/_bk_q_test/inputs'
output_dir = 'E:/FIRE_MODELING/fire_model_python/_bk_q_test/outputs'

# input_dir = 'E:/FIRE_MODELING/fire_model_python/_m_test/inputs'
# output_dir = 'E:/FIRE_MODELING/fire_model_python/_m_test/outputs'
log_dir = 'E:/FIRE_MODELING/fire_model_python/log'

# Configure logging
logging.basicConfig(filename=(log_dir + '/fire_log.txt'),
                    level=logging.DEBUG)

# Set workspace
arcpy.env.workspace = 'E:/FIRE_MODELING/fire_model'
arcpy.env.overwriteOutput = True

start_time = time.time()
time_stamp = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d | %H:%M:%S')
logging.info(time_stamp)

####
# Initial Parameters
run_length = range(1409, 1509)
initial_time_since_last_disturbance = 20
trail_overgrown_yrs = 15

# Escaped fire probabilities
prob_trail_escape = 100
prob_hort_escape = 0
prob_hunt_escape = 0

# Un-burnable fuel types
un_burnable = [14, 16, 98, 99]
####

# Read in climate data
logging.info('Reading in climate data')

# Climate dictionaries
drought = {}
climate_years = {}

# Read drought values
with open(input_dir + '/script/mannahatta-psdi.txt', 'r') as drought_file:
    for line in drought_file:
        year, psdi = line.split('\t')
        drought[int(year)] = float(psdi)

# Read in years grouped by PSDI values
with open(input_dir + '/script/psdi-years.txt', 'r') as psdiyears_file:
    for line in psdiyears_file:
        c_list = line.strip('\n').split('\t')
        climate_years[float(c_list[0])] = []
        for year in c_list[1:]:
            if year != '':
                climate_years[float(c_list[0])].append(int(year))

# Read in ecosystem raster
logging.info('Creating starting ecosystem array')
ecosystem_ascii = gdal.Open((input_dir + '/script/ec-start.asc'), GA_ReadOnly)
ecosystem_array = gdal_array.DatasetReadAsArray(ecosystem_ascii)
ecosystem_ascii = None
logging.info('memory usage: %r Mb' % memory())

# Get header
# Linecache header used to write out ascii rasters (header argument in array_to_raster)
header = [linecache.getline((input_dir + '/script/ec-start.asc'), i) for i in range(1, 7)]

# h dictionary stores header attributes used in the script
h = {}
for line in header:
    attribute, value = line.split()
    h[attribute] = float(value)


# Read in climax ecosystem raster
logging.info('Creating climax ecosystem array')
climax_ecosystem_ascii = gdal.Open((input_dir + '/script/ec-climax.asc'), GA_ReadOnly)
climax_ecosystem_array = gdal_array.DatasetReadAsArray(climax_ecosystem_ascii)
climax_ecosystem_ascii = None
logging.info('memory usage: %r Mb' % memory())

# Read in translation table
translation = {}
with open(input_dir + '/script/mannahatta.ec.translators.2.txt', 'r') as trans_file:
    logging.info('Reading translation table')
    for line in trans_file:
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

# Assign initial values to canopy array
logging.info('Assigning initial values to canopy array')
canopy_array = numpy.empty((h['nrows'], h['ncols']))
for index, value in numpy.ndenumerate(ecosystem_array):
    canopy_array[index[0]][index[1]] = translation[int(value)]['max_canopy']
logging.info('memory usage: %r Mb' % memory())


# Assign initial values to forest age array
logging.info('Assigning initial values to forest age array')
forest_age_array = numpy.empty((h['nrows'], h['ncols']))
for index, value in numpy.ndenumerate(ecosystem_array):
    forest_age_array[index[0]][index[1]] = translation[int(value)]['start_age']
logging.info('memory usage: %r Mb' % memory())

# Assign initial values to last disturbance array
logging.info('Assigning initial values to last_disturbance')
last_disturbance_array = numpy.empty((h['nrows'], h['ncols']))
last_disturbance_array.fill(initial_time_since_last_disturbance)
logging.info('memory usage: %r Mb' % memory())

# Assign initial values to fuel array
fuel_array = numpy.empty((h['nrows'], h['ncols']))
logging.info('Assigning initial values to fuel array')
fuel_array = ecosystem_to_fuel(ecosystem_array,
                               last_disturbance_array,
                               fuel_array,
                               translation)
logging.info('memory usage: %r Mb' % memory())

# Write canopy array to ascii
logging.info('Saving canopy array as ascii raster')
array_to_raster((input_dir + '/farsite/canopy.asc'), canopy_array, header)
logging.info('memory usage: %r Mb' % memory())

# Write fuel array to ascii
logging.info('Saving fuel array as ascii raster')
array_to_raster((input_dir + '/farsite/fuel.asc'), fuel_array, header)
logging.info('memory usage: %r Mb' % memory())

# Main Loop
for year in run_length:

    logging.info('Year: %r' % year)

    # Select potential ignition sites
    potential_ignition_sites = []

    # Check for trail fires
    random_trail_fire = random.choice(range(1, 100))
    if prob_trail_escape > random_trail_fire:
        logging.info('escaped trail fire')

        # Read in trail raster
        logging.info('Creating trail array')
        trail_ascii = gdal.Open((input_dir + '/script/fire_trails.asc'), GA_ReadOnly)
        trail_array = gdal_array.DatasetReadAsArray(trail_ascii)
        trail_ascii = None

        for index, cell_value in numpy.ndenumerate(trail_array):
            if cell_value == 1 and last_disturbance_array[index[0]][index[1]] >= trail_overgrown_yrs:
                if fuel_array[index[0]][index[1]] not in un_burnable:
                    potential_ignition_sites.append(index)

        trail_array = None

    # Check for field fires
    random_field_fire = random.choice(range(1, 100))
    if prob_hort_escape > random_field_fire:
        logging.info('escaped horticulture fire')

        # Read in field raster
        logging.info('Creating field array')
        field_ascii = gdal.Open((input_dir + '/script/fire_fields.asc'), GA_ReadOnly)
        field_array = gdal_array.DatasetReadAsArray(field_ascii)
        field_ascii = None

        for index, cell_value in numpy.ndenumerate(field_array):
            if cell_value == 1:
                if fuel_array[index[0]][index[1]] not in un_burnable:
                    potential_ignition_sites.append(index)

        field_array = None

    # Check for hunting fires
    # random_hunt_fire = random.choice(range(1, 100))
    # if prob_hunt_escape > random_hunt_fire:
    #     logging.info('escaped hunting fire')
    #
    #     # Read in hunt raster
    #     logging.info('Creating hunt array')
    #     hunt_ascii = gdal.Open((input_dir + '/script/fire_hunt.asc'), GA_ReadOnly)
    #     hunt_array = gdal_array.DatasetReadAsArray(hunt_ascii)
    #     hunt_ascii = None
    #
    #     for row_index, row_value in enumerate(hunt_array):
    #         for col_index, cell_value in enumerate(row_value):
    #             if cell_value == 1:
    #                 if fuel_array[row_index][col_index] not in un_burnable:
    #                     potential_ignition_sites.append((row_index, col_index))
    #
    #     hunt_array = None
    # Declare area burned
    area_burned = 0

    # Fire
    if len(potential_ignition_sites) > 0:

        # Choose an ignition site
        ignition_site = random.choice(potential_ignition_sites)

        logging.info('Creating ignition point')
        # Write selected ignition sites to .vct file for FARSITE
        # Write ignition sites to .shp for logging
        write_ignition()

        # Select climate file
        equivalent_climate_year = select_climate_records()
        logging.info('Selected climate equivalent-year: %r' % equivalent_climate_year)

        # Get matching climate year file for FARSITE
        shutil.copyfile((input_dir + '/wtr/%r.wtr' % equivalent_climate_year),
                        (input_dir + '/farsite/weather.wtr'))

        # create wind file
        write_wnd()

        # Run Farsite

        run_farsite(year)

        # Create flame length array
        flame_length_ascii = gdal.Open((input_dir + '/script/burn_rasters/farsite_output.fml'), GA_ReadOnly)
        flame_length_array = gdal_array.DatasetReadAsArray(flame_length_ascii)
        flame_length_ascii = None

        # Revise ecosystem raster based on fire
        for index, cell_value in numpy.ndenumerate(ecosystem_array):
            row_index = index[0]
            col_index = index[1]

            climax = climax_ecosystem_array[row_index][col_index]

            flame = flame_length_array[row_index][col_index]

            if flame > 0:
                area_burned += 1

                # Reset last disturbance array
                last_disturbance_array[row_index][col_index] = 1

                # Calculate tree mortality due to fire
                if translation[cell_value]['forest'] == 1:
                    age = forest_age_array[row_index][col_index]
                    percent_mortality = tree_mortality(flame, age)

                    # Revise canopy cover according to tree mortality
                    canopy_array[row_index][col_index] = int(canopy_array[row_index][col_index] *
                                                             (1 - percent_mortality))

                # Revise ecosystems based on new canopy
                # Convert burned forest to shrubland
                if translation[cell_value]['forest'] == 1:
                    if canopy_array[row_index][col_index] < (translation[cell_value]['max_canopy'] / 2):
                        ecosystem_array[row_index][col_index] = 649
                        forest_age_array[row_index][col_index] = 1

                # Convert burned shrubland to grassland
                if cell_value == 649 and canopy_array[row_index][col_index] < 10:
                    ecosystem_array[row_index][col_index] = 635

    # No Fire
    else:
        logging.info('No escaped fires for %r' % year)

        # Revise ecosystem raster based on succesional sequence
        for index, cell_value in numpy.ndenumerate(ecosystem_array):
            row_index = index[0]
            col_index = index[1]

            climax = climax_ecosystem_array[row_index][col_index]

            last_disturbance_array[row_index][col_index] += 1

            if translation[cell_value]['forest_shrub'] == 1:
                canopy_array[row_index][col_index] += 1

            if cell_value == 649:
                if canopy_array[row_index][col_index] >= (translation[cell_value]['max_canopy'] / 2):
                    ecosystem_array[row_index][col_index] = climax

            if cell_value == 635:
                canopy_array[row_index][col_index] += 2

                if canopy_array[row_index][col_index] > 10:
                    ecosystem_array[row_index][col_index] = 649

            if canopy_array[row_index][col_index] > translation[cell_value]['max_canopy']:
                canopy_array[row_index][col_index] = translation[cell_value]['max_canopy']

            if translation[cell_value]['forest'] == 1:
                forest_age_array[row_index][col_index] += 1

    logging.info('Area burned %r: %r acres' % (year, (area_burned * 100 * 0.000247105)))

    # Revise fuel model
    fuel_array = ecosystem_to_fuel(ecosystem_array,
                                   last_disturbance_array,
                                   fuel_array,
                                   translation)

    array_to_raster((input_dir + '/farsite/fuel.asc'), fuel_array, header)
    array_to_raster((input_dir + '/farsite/canopy.asc'), canopy_array, header)

    # Yearly outputs
    if area_burned > 0:
        shutil.copyfile((input_dir + '/farsite/fuel.asc'), (output_dir + '/log_rasters/%s_fuel.asc' % year))
        shutil.copyfile((input_dir + '/farsite/canopy.asc'), (output_dir + '/log_rasters/%s_canopy.asc' % year))
        array_to_raster((output_dir + '/log_rasters/%s_ecosystem.asc' % year), ecosystem_array, header)
        array_to_raster((output_dir + '/log_rasters/%s_last_disturbance.asc' % year), last_disturbance_array, header)

# Write final raster outputs
shutil.copyfile((input_dir + '/farsite/fuel.asc'), (output_dir + '/end_year_rasters/%s_fuel.asc' % run_length[-1]))
shutil.copyfile((input_dir + '/farsite/canopy.asc'), (output_dir + '/end_year_rasters/%s_canopy.asc' % run_length[-1]))
array_to_raster((output_dir + '/end_year_rasters/%s_ecosystem.asc' % run_length[-1]), ecosystem_array, header)
array_to_raster((output_dir + '/end_year_rasters/%s_last_disturbance.asc' % run_length[-1]), last_disturbance_array,
                header)

end_time = time.time()
run_time = end_time - start_time
logging.info('Run time: %s' % run_time)
logging.info('Hello Welikia!')
