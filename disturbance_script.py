import os
import sys
import shutil
import time
import datetime
import pandas as pd
import arcpy
import settings as s
import utils
import pond
import fire
import garden
import succession

# ArcGIS Extensions
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to checkout spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)

arcpy.env.workspace = s.TEMP_DIR
arcpy.env.scratchWorkspace = s.TEMP_DIR
arcpy.env.overwriteOutput = True
utils.set_arc_env(s.ecocommunities)

utils.clear_dir(s.OUTPUT_DIR)
# copy current settings file
shutil.copyfile(os.path.join('{}'.format(sys.path[0]), 'settings.py'),
                os.path.join(s.TRIAL_DIR, 'settings_scenario.py'))

columns = ['fire_area', 'fire_occurrence', 'pond_area', 'garden_area',
           'year_run_time', 'garden_run_time', 'fire_run_time', 'pond_run_time']

# create or load disturbance data frame
if os.path.isfile(os.path.join(s.OUTPUT_DIR, 'disturbance_table.csv')):
    disturbance_table = pd.read_csv(os.path.join(s.OUTPUT_DIR, 'disturbance_table.csv'), index_col=0)
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

    if s.GARDEN:
        s.logging.info('_____starting garden disturbance')
        garden_start = time.time()
        garden_dis = garden.GardenDisturbance(year)
        garden_dis.run_year()
        garden_end = time.time()
        disturbance_table.loc[year, 'garden_area'] = garden_dis.new_garden_area
        disturbance_table.loc[year, 'garden_run_time'] = ((garden_end - garden_start) / 60)
        del garden_dis

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

    if s.POND:
        s.logging.info('_____starting pond disturbance')
        pond_start = time.time()
        pond_dis = pond.PondDisturbance(year)
        pond_dis.run_year()
        pond_end = time.time()
        disturbance_table.loc[year, 'pond_area'] = pond_dis.new_pond_area
        disturbance_table.loc[year, 'pond_run_time'] = ((pond_end - pond_start) / 60)
        del pond_dis

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

s.logging.info('______simulation completed')
full_run_end = time.time()
s.logging.info('end time: %s' % t.now)
s.logging.info('full run time: %s minutes' % ((full_run_end - full_run_start) / 60))
