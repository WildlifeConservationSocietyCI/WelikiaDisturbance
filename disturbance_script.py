import os
import sys
import shutil
import time
import datetime
import logging
import pandas as pd
import arcpy
import settings as s
import utils
import pond
import fire
import garden
import succession

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=s.LOGFILE,  # use same log file as initiate_disturbance
                    # filemode='w',  # defaults to 'a' for append
                    format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S')

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to checkout spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)

utils.clear_dir(s.TEMP_DIR)
arcpy.env.workspace = s.TEMP_DIR
scratchdir = os.path.join(s.TEMP_DIR, 'scratch')
utils.mkdir(scratchdir)
arcpy.env.scratchWorkspace = scratchdir
# arcpy.env.workspace = os.path.join(s.TEMP_DIR, 'working.gdb')
# arcpy.env.scratchWorkspace = os.path.join(s.TEMP_DIR, 'working.gdb')
arcpy.env.overwriteOutput = True
utils.set_arc_env(s.ecocommunities)

utils.clear_dir(s.OUTPUT_DIR)
utils.mkdir(os.path.join(s.OUTPUT_DIR, 'fire', 'burn_rasters'))
utils.mkdir(os.path.join(s.OUTPUT_DIR, 'garden'))
utils.mkdir(os.path.join(s.OUTPUT_DIR, 'pond'))
# copy current settings file
shutil.copyfile(os.path.join('{}'.format(sys.path[0]), 'settings.py'),
                os.path.join(s.TRIAL_DIR, 'settings.py'))

columns = ['fire_area', 'fire_occurrence', 'pond_area', 'garden_area',
           'year_run_time', 'garden_run_time', 'fire_run_time', 'pond_run_time']

# create or load disturbance data frame
if os.path.isfile(os.path.join(s.OUTPUT_DIR, 'disturbance_table.csv')):
    disturbance_table = pd.read_csv(os.path.join(s.OUTPUT_DIR, 'disturbance_table.csv'), index_col=0)
else:
    disturbance_table = pd.DataFrame(columns=columns, index=s.RUN_LENGTH)

logging.info('starting %s year simulation' % len(s.RUN_LENGTH))
full_run_start = time.time()

t = datetime.datetime

logging.info('start time: %s' % t.now())
for year in s.RUN_LENGTH:
    logging.info('____YEAR: %s____' % year)

    year_start = time.time()
    logging.info('start time: %s' % t.now())

    if s.GARDEN:
        logging.info('_____starting garden disturbance')
        garden_start = time.time()
        garden_dis = garden.GardenDisturbance(year)
        garden_dis.run_year()
        garden_end = time.time()
        disturbance_table.loc[year, 'garden_area'] = garden_dis.new_garden_area
        disturbance_table.loc[year, 'garden_run_time'] = ((garden_end - garden_start) / 60)
        del garden_dis

    if s.FIRE:
        logging.info('_____starting fire disturbance')
        fire_start = time.time()
        fire_dis = fire.FireDisturbance(year)
        fire_dis.run_year()
        disturbance_table.loc[year, 'fire_occurrence'] = len(fire_dis.ignition_sites)
        fire_end = time.time()
        disturbance_table.loc[year, 'fire_area'] = fire_dis.area_burned
        disturbance_table.loc[year, 'fire_run_time'] = ((fire_end - fire_start) / 60)
        del fire_dis

    if s.POND:
        logging.info('_____starting pond disturbance')
        pond_start = time.time()
        pond_dis = pond.PondDisturbance(year)
        pond_dis.run_year()
        pond_end = time.time()
        disturbance_table.loc[year, 'pond_area'] = pond_dis.new_pond_area
        disturbance_table.loc[year, 'pond_run_time'] = ((pond_end - pond_start) / 60)
        del pond_dis

    logging.info('_____starting succession')
    succ = succession.Succession(year)
    succ.run_succession()
    del succ

    year_end = time.time()
    disturbance_table.loc[year, 'year_run_time'] = ((year_end - year_start) / 60)
    logging.info('end time: %s' % t.now())
    logging.info('year run time: %s minutes' % ((year_end - year_start) / 60))

    # track disturbances
    disturbance_table.to_csv(path_or_buf=os.path.join(s.OUTPUT_DIR, 'disturbance_table.csv'))

logging.info('______simulation completed')
full_run_end = time.time()
logging.info('end time: %s' % t.now)
logging.info('full run time: %s minutes' % ((full_run_end - full_run_start) / 60))
