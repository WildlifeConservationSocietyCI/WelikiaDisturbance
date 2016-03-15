__author__ = 'Jesse Moy'

import numpy
import os
import random
import pyautogui
import pywinauto
import linecache
import shutil
import arcpy
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
from wmi import WMI
from datetime import date
import logging
import math
import re
import time

from pywinauto.application import Application

# Convert numpy to ASCII raster for use in FARSITE
def array_to_raster(out_path, array, header):

    out_asc = open(out_path, 'w')
    for attribute in header:
        out_asc.write(attribute)

    numpy.savetxt(out_asc, array, fmt="%4i")
    out_asc.close()


# Creates a fuel array based on ecosystem type and time since last disturbance
def ecosystem_to_fuel(ecosystem_array, last_disturbance_array, fuel_array, translation):

    # Constants
    succession_time_mid = 10
    succession_time_climax = 20

    for index, cell_value in numpy.ndenumerate(ecosystem_array):
            row_index = index[0]
            col_index = index[1]

            if last_disturbance_array[row_index][col_index] > succession_time_climax:
                fuel_array[row_index][col_index] = translation[cell_value]['climax_fuel']

            elif last_disturbance_array[row_index][col_index] > succession_time_mid:
                fuel_array[row_index][col_index] = translation[cell_value]['mid_fuel']

            else:
                fuel_array[row_index][col_index] = translation[cell_value]['new_fuel']

    return fuel_array


def memory():

    # Reports current memory usage

    w = WMI('.')
    result = w.query("SELECT WorkingSet FROM Win32_PerfRawData_PerfProc_Process WHERE IDProcess=%d" % os.getpid())
    return int(result[0].WorkingSet) / 1000000.0


def write_ignition(input_dir, output_dir, ignition_site, h, year):

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


def write_wnd(input_dir):

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


def select_climate_records(year, drought, climate_years):

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


def select_duration(input_dir, year):
    # Rain in mm needed to extinguish a fire
    extinguish_threshold = 100

    # Number of days used to condition fuel before the start of fire
    conditioning_length = 15

    # Define Window for ignition start date
    fire_season_start = date(day=1, month=3, year=year).toordinal()
    fire_season_end = date(day=31, month=5, year=year).toordinal()

    # Weather lines holds the climate records for a given year
    weather_lines = []

    # Select a start date without rain
    def get_clear_day():

        rain = True
        while rain is True:
            random_date = date.fromordinal(random.randint(fire_season_start, fire_season_end))
            for i in weather_lines[1:]:
                if int(i[0]) == random_date.month and int(i[1]) == random_date.day:
                    if int(i[2]) == 0:
                        rain = False

        return random_date

    with open(input_dir + '/weather.wtr') as weather:
        for line in weather:
            record = line.split()
            weather_lines.append(record)
        start_date = get_clear_day()

    # Calculate conditioning date
    conditioning_date = date.fromordinal(start_date.toordinal() - conditioning_length)

    con_month = conditioning_date.month
    con_day = conditioning_date.day
    start_month = start_date.month
    start_day = start_date.day
    end_month = 0
    end_day = 0

    # Find the next day with sufficient rain to end the fire
    for i in weather_lines[1:]:
        if int(i[0]) == start_month and int(i[1]) == start_day:
            start_index = weather_lines.index(i)
            for e in weather_lines[start_index:]:
                if int(e[2]) > extinguish_threshold:
                    end_month = int(e[0])
                    end_day = int(e[1])
                    break

    return con_month, con_day, start_month, start_day, end_month, end_day


def run_farsite(year):
    cond_month, cond_day, start_month, start_day, end_month, end_day = select_duration(year)
    ordinal_start = date(day=start_day, month=start_month, year=1409).toordinal()
    ordinal_end = date(day=end_day, month=end_month, year=1409).toordinal()

    logging.info('Start date: %r/%r/%r | End date:  %r/%r/%r | Duration: %r days'% (start_month,
                                                                                    start_day,
                                                                                    year,
                                                                                    end_month,
                                                                                    end_day,
                                                                                    year,
                                                                                    (ordinal_end-ordinal_start)))
    pyautogui.PAUSE = 0.25

    # full extent test input_dir
    input_dir = 'E:\\FIRE_MODELING\\fire_model_python\\bk_q_test\\inputs'

    farsite = pywinauto.application.Application()
    farsite.start_(r"C:\\Program Files (x86)\\farsite4.exe")

    # Load FARSITE project file
    logging.info('Loading FARSITE project file')

    # Open project window
    farsite_main_win = farsite.window_(title_re='.*FARSITE: Fire Area Simulator$')

    farsite_main_win.MenuItem('File->Load Project').Click()
    try:
        load_project = farsite.window_(title='Select Project File')
        load_project.SetFocus()

        pyautogui.typewrite(input_dir + '\\farsite\\manhattan.FPJ')
        pyautogui.press('enter')
        pyautogui.press('enter')

        logging.info('Project file loaded')

    except pywinauto.findwindows.WindowNotFoundError:
        logging.error('Can not find SELECT PROJECT FILE window')
        farsite.Kill_()

    # Load FARSITE landscape file
    logging.info('Loading FARSITE landscape file')

    # Open project input window
    farsite_main_win.MenuItem('Input-> Project Inputs').Click()

    try:
        project_inputs = farsite.window_(title='FARSITE Project')
        project_inputs.SetFocus()
        project_inputs[u'->13'].Click()

        # Load fuel and canopy rasters
        try:
            landscape_load = farsite.window_(title='Landscape (LCP) File Generation')
            landscape_load.SetFocus()
            pyautogui.press(['tab'] * 8)
            pyautogui.press('space')
            pyautogui.typewrite(input_dir + '\\farsite\\fuel.asc')
            pyautogui.press('enter')
            pyautogui.press(['down', 'space'])
            pyautogui.typewrite(input_dir + '\\farsite\\canopy.asc')
            pyautogui.press('enter')
            pyautogui.press('enter')

        except pywinauto.findwindows.WindowNotFoundError:
            logging.error('Can not find Landscape (LCP) File Generation window')
            farsite.Kill_()

        # Wait while FARSITE generates the landcape file
        landscape_generated = farsite.window_(title_re='.*Landscape Generated$')
        landscape_generated.Wait('exists', timeout=60)
        landscape_generated.SetFocus()
        pyautogui.press('enter')
        pyautogui.press('esc')

        logging.info('landscape file loaded')

    except pywinauto.findwindows.WindowNotFoundError:
        logging.info('Unable to generate landscape file')
        farsite.Kill_()

    # Delete FARSITE_output from output folder
    logging.info('Deleting previous FARSITE outputs')
    for f in os.listdir((input_dir + '\\script\\burn_rasters')):
        if re.search('farsite_output', f):
            os.remove(((input_dir + '\\script\\burn_rasters') + '\\' + f))

    # Export and output options
    logging.info('Setting export and output options')

    # Open export and output option window
    farsite_main_win.MenuItem('Output->Export and Output').Click()
    try:
        set_outputs = farsite.window_(title='Export and Output Options')
        set_outputs.SetFocus()
        set_outputs[u'&Select Rater File Name'].Click()
        pyautogui.typewrite(input_dir + '\\script\\burn_rasters\\farsite_output')
        pyautogui.press('enter')
        set_outputs[u'Flame Length (m)'].Click()
        set_outputs[u'&Default'].Click()
        set_outputs[u'&OK'].Click()
        logging.info('Outputs set')

    except pywinauto.findwindows.WindowNotFoundError:
        logging.error('Can not find EXPORT AND OUTPUT OPTIONS window')
        farsite.Kill_()

    # Set simulation parameters
    logging.info('Setting simulation parameters')

    # Open parameter window
    farsite_main_win.MenuItem('Model->Parameters').Click()
    try:
        set_parameters = farsite.window_(title='Model Parameters')
        set_parameters.SetFocus()
        pyautogui.press(['right'] * 90)
        pyautogui.press(['tab'] * 2)
        pyautogui.press(['left'] * 30)
        pyautogui.press('tab')
        pyautogui.press(['left'] * 20)
        pyautogui.press('enter')
        time.sleep(3)
        logging.info('Parameters set')

    except pywinauto.findwindows.WindowNotFoundError:
        logging.error('Can not find MODEL PARAMETERS window')
        farsite.Kill_()

    # fire behavior options: disable crown fire
    # Open fire behavior window
    farsite_main_win.MenuItem('Model->Fire Behavior Options').Click()
    try:
        set_fire_behavior = farsite.window_(title='Fire Behavior Options')
        set_fire_behavior.SetFocus()
        set_fire_behavior[u'Enable Crownfire'].UnCheck()
        set_fire_behavior[u'&OK'].Click()
        # pyautogui.press(['space', 'enter'])

    except pywinauto.findwindows.WindowNotFoundError:
        logging.error('can not find FIRE BEHAVIOR OPTIONS window')
        farsite.Kill_()

    # Set number of simulation threads
    farsite_main_win.MenuItem('Simulate->Options').Click()
    try:
        simulation_options = farsite.window_(title='Simulation Options')
        simulation_options.SetFocus()
        simulation_options.Wait('ready')
        simulation_options.UpDown.SetValue(8)
        simulation_options[u'&OK'].Click()

    except pywinauto.findwindows.WindowNotFoundError:
        logging.error('can not find SIMULATION OPTIONS window')
        farsite.Kill_()

    # Open duration window
    farsite_main_win.MenuItem('Simulate->Duration').Click()
    try:
        simulation_duration = farsite.window_(title='Simulation Duration')
        simulation_duration.SetFocus()
        simulation_duration[u'Use Conditioning Period for Fuel Moistures'].Click()
        time.sleep(.5)
        # Conditioning month
        while int(simulation_duration[u'Static5'].Texts()[0]) != cond_month:
            if int(simulation_duration[u'Static5'].Texts()[0]) > cond_month:
                simulation_duration.Updown1.Decrement()
            if int(simulation_duration[u'Static5'].Texts()[0]) < cond_month:
                simulation_duration.Updown1.Increment()

        # Conditioning day
        while int(simulation_duration[u'Static6'].Texts()[0]) != cond_day:
            if int(simulation_duration[u'Static6'].Texts()[0]) > cond_day:
                simulation_duration.Updown2.Decrement()
            if int(simulation_duration[u'Static6'].Texts()[0]) < cond_day:
                    simulation_duration.Updown2.Increment()

        # Start month
        while int(simulation_duration[u'Static9'].Texts()[0]) != start_month:
            if int(simulation_duration[u'Static9'].Texts()[0]) > start_month:
                simulation_duration.Updown5.Decrement()
            if int(simulation_duration[u'Static9'].Texts()[0]) < start_month:
                simulation_duration.Updown5.Increment()

        # Start day
        while int(simulation_duration[u'Static10'].Texts()[0]) != start_day:
            if int(simulation_duration[u'Static10'].Texts()[0]) > start_day:
                simulation_duration.Updown6.Decrement()
            if int(simulation_duration[u'Static10'].Texts()[0]) < start_day:
                simulation_duration.Updown6.Increment()

        # End month
        while int(simulation_duration[u'Static13'].Texts()[0]) != end_month:
            if int(simulation_duration[u'Static13'].Texts()[0]) > end_month:
                simulation_duration.Updown9.Decrement()
            if int(simulation_duration[u'Static13'].Texts()[0]) < end_month:
                simulation_duration.Updown9.Increment()
        # End day
        while int(simulation_duration[u'Static14'].Texts()[0]) != end_day:
            if int(simulation_duration[u'Static14'].Texts()[0]) > end_day:
                simulation_duration.Updown10.Decrement()
            if int(simulation_duration[u'Static14'].Texts()[0]) < end_day:
                simulation_duration.Updown10.Increment()

        simulation_duration[u'OK'].Click()

        logging.info('Duration set')

    except farsite.findwindows.WindowNotFoundError:
        logging.info('can not find SIMULATION DURATION window')
        farsite.Kill_()

    # Initiate simulation
    farsite_main_win.MenuItem('Simulate->Initiate/Terminate').Click()
    landscape_initiated = farsite.window_(title_re='.*LANDSCAPE:')
    landscape_initiated.Wait('ready', timeout=40)

    time.sleep(5)

    # Set Ignition
    farsite_main_win.MenuItem('Simulate->Modify Map->Import Ignition File').Click()
    try:
        set_ignition = farsite.window_(title='Select Vector Ignition File')
        set_ignition.SetFocus()
        pyautogui.press('right')
        pyautogui.typewrite(input_dir + '\\farsite\\ignition.vct')
        pyautogui.press('enter')
        pyautogui.press(['right', 'enter'])
        pyautogui.press(['right', 'enter'])

    except farsite.findwindows.WindowNotFoundError:
            logging.error('can not find SELECT VECTOR IGNITION FILE window')

    logging.info('Starting simulation')
    farsite_main_win.SetFocus()
    farsite_main_win.MenuItem(u'&Simulate->&Start/Restart').Click()
    simulation_complete = farsite.window_(title_re='.*Simulation Complete')
    simulation_complete.Wait('exists', timeout=1800)
    simulation_complete.SetFocus()
    pyautogui.press('enter')

    # Exit FARSITE
    farsite.Kill_()
    pyautogui.press('enter')


def tree_mortality(flame, age):

    """
    Tree_mortality calculates the percentage of the canopy in a cell killed during a burning event
    This estimate is based on the age of the forest and the length of the flame
    Model logic and tree size/diameter regressions from Tim Bean
    """

    # Convert flame length to ft
    flame *= 3.2808399

    # Calculate scorch height
    scorch = (3.1817*(flame**1.4503))

    # Calculate tree height
    tree_height = 44 * math.log(age) - 93

    # Calculate tree diameter at breast height
    DBH = (25.706 * math.log(age))-85.383

    if tree_height < 0:
        tree_height = 1
    if age <= 35:
        DBH = 5
    if age <= 25:
        DBH = 3
    if age <= 20:
        DBH = 2
    if age <= 15:
        DBH = 1

    # Calculate bark thickness
    bark_thickness = 0.045 * DBH

    # Define crown ratio
    crown_ratio = 0.4

    # Calculate crown height
    crown_height = tree_height*(1-crown_ratio) #calc crown height

    # Calculate crown kill
    if scorch < crown_height:
        crown_kill = 0


    else:

        crown_kill = 41.961 * (math.log (100*(scorch - crown_height)/(tree_height * crown_ratio)))-89.721

        if crown_kill < 5:
            crown_kill = 5

        if crown_kill > 100:
            crown_kill = 100

    # Calculate percent mortality
    mortality = (1/(1 + math.exp((-1.941+(6.3136*(1-(math.exp(-bark_thickness)))))-(.000535*(crown_kill**2)))))

    return mortality
    #print 'Age: %r\t| Height: %r\t| DBH %r\t | Crown Kill: %r\t| Mortality: %r' %(age, tree_height, DBH, ck, pm)