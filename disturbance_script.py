import settings as s
import sys
import os
import pond
import fire
import garden
import arcpy
import shutil
import time
from arcpy import env
import pandas as pd
import datetime
import succession


# ArcGIS Extensions

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to checkout spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)

# Environment Settings
print(s.ecocommunities)
arcpy.env.extent = s.ecocommunities
arcpy.env.cellSize = s.ecocommunities
arcpy.env.snapRaster = s.ecocommunities
arcpy.env.outputCoordinateSystem = arcpy.Describe(s.ecocommunities).spatialReference
arcpy.env.cartographicCoordinateSystem = arcpy.Describe(s.ecocommunities).spatialReference

env.workspace = s.TEMP_DIR
env.scratchWorkspace = s.TEMP_DIR
env.overwriteOutput = True


def clear_dir(directory):
    file_list = os.listdir(directory)
    for file_name in file_list:
        path = (os.path.join(directory, file_name))
        if os.path.isfile(path):
            os.remove(path)
        if os.path.isdir(path):
            shutil.rmtree(path)

# log trial settings
shutil.copyfile(os.path.join(s.ROOT_DIR, 'settings_scenario.py'),
                os.path.join(s.LOG_DIR, 'settings_scenario.py'))

clear_dir(s.TEMP_DIR)

columns = ['fire_area', 'fire_occurrence', 'pond_area', 'garden_area',
           'year_run_time', 'garden_run_time', 'fire_run_time', 'pond_run_time']

# create or load disturbance data frame
if os.path.isfile(os.path.join(s.LOG_DIR, 'disturbance_table.csv')):
    disturbance_table = pd.read_csv(os.path.join(s.LOG_DIR, 'disturbance_table.csv'), index_col=0)
    print disturbance_table.head()
else:
    disturbance_table = pd.DataFrame(columns=columns, index=s.RUN_LENGTH)

s.logging.info('starting %s year simulation' % len(s.RUN_LENGTH))
full_run_start = time.time()

t = datetime.datetime

s.logging.info('start time: %s' % t.now())
for year in s.RUN_LENGTH:

    s.logging.info('____YEAR: %s____' % year)

    year_start = time.time()
    s.logging.info('start time: %s' % t.now())

    # garden
    if s.GARDEN:
        s.logging.info('_____starting garden disturbance')
        garden_start = time.time()
        garden_dis = garden.GardenDisturbance(year)
        garden_dis.run_year()
        garden_end = time.time()
        disturbance_table.loc[year, 'garden_area'] = garden_dis.new_garden_area
        disturbance_table.loc[year, 'garden_run_time'] = ((garden_end - garden_start) / 60)
        del garden_dis

    # fire
    if s.FIRE:
        s.logging.info('_____starting fire disturbance')
        fire_start = time.time()
        fire_dis = fire.FireDisturbance(year)
        fire_dis.run_year()
        disturbance_table.loc[year, 'fire_occurrence'] = len(fire_dis.ignition_sites)
        fire_end = time.time()
        disturbance_table.loc[year, 'fire_area'] = fire_dis.area_burned
        disturbance_table.loc[year, 'fire_run_time'] = ((fire_end - fire_start) / 60)

        del fire_dis

    # beaver pond
    if s.POND:
        s.logging.info('_____starting pond disturbance')
        pond_start = time.time()
        pond_dis = pond.PondDisturbance(year)
        pond_dis.run_year()
        pond_end = time.time()
        disturbance_table.loc[year, 'pond_area'] = pond_dis.new_pond_area
        disturbance_table.loc[year, 'pond_run_time'] = ((pond_end - pond_start) / 60)
        del pond_dis

    # run succession module
    s.logging.info('_____starting succession')
    succ = succession.Succession(year)
    succ.run_succession()
    del succ

    year_end = time.time()
    disturbance_table.loc[year, 'year_run_time'] = ((year_end - year_start) / 60)
    s.logging.info('end time: %s' % t.now())
    s.logging.info('year run time: %s minutes' % ((year_end - year_start) / 60))

    # track disturbances
    disturbance_table.to_csv(path_or_buf=os.path.join(s.OUTPUT_DIR, 'disturbance_table.csv'))
    disturbance_table.to_csv(path_or_buf=os.path.join(s.LOG_DIR, 'disturbance_table.csv'))

s.logging.info('______simulation completed')

full_run_end = time.time()
s.logging.info('end time: %s' % t.now)
s.logging.info('full run time: %s minutes' % ((full_run_end - full_run_start) / 60))

s.logging.info('creating ecosystem areas table')
