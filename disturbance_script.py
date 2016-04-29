import settings as s
import os
import pond
import fire
import garden
import arcpy
import shutil
import time

# assign s.ecocommunities to starting raster
arcpy.env.extent = s.ecocommunities
arcpy.env.cellSize = s.ecocommunities
arcpy.env.snapRaster = s.ecocommunities
arcpy.env.outputCoordinateSystem = arcpy.Describe(s.ecocommunities).spatialReference
arcpy.env.cartographicCoordinateSystem = arcpy.Describe(s.ecocommunities).spatialReference
print arcpy.Describe(s.ecocommunities).spatialReference
print arcpy.env.outputCoordinateSystem


def clear_dir(directory):

    file_list = os.listdir(directory)
    for file_name in file_list:
        path = (os.path.join(directory, file_name))
        if os.path.isfile(path):
            os.remove(path)
        if os.path.isdir(path):
            shutil.rmtree(path)

clear_dir(os.path.join(s.INPUT_DIR, 'fire', 'script', 'burn_rasters'))

clear_dir(s.TEMP_DIR)

s.logging.info('starting %s year simulation' % len(s.RUN_LENGTH))
full_run_start = time.time()
s.logging.info('start time: %s' % full_run_start)
for year in s.RUN_LENGTH:

    s.logging.info('____YEAR: %s____' % year)

    year_start = time.time()
    s.logging.info('year start: %s' % year_start)

    # garden
    s.logging.info('starting garden disturbance')
    garden_dis = garden.GardenDisturbance(year)
    garden_dis.run_year()

    # fire
    s.logging.info('starting fire disturbance')
    fire_dis = fire.FireDisturbance(year)
    fire_dis.run_year()

    # beaver pond
    s.logging.info('starting pond disturbance')
    pond_dis = pond.PondDisturbance(year)
    pond_dis.run_year()

    year_end = time.time()
    s.logging.info('year end: %s' % year_end)
    s.logging.info('year run time: %s' % (year_end - year_start))

s.logging.info('simulation completed')

full_run_end = time.time()
s.logging.info('end time: %s' % full_run_end)
s.logging.info('full run time: %s' % (full_run_end - full_run_start))