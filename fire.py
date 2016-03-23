import settings as s
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
import numpy
import linecache
import pyautogui
import pywinauto
import logging
import re
import time
import datetime
import random
import os
import posixpath

class FireDisturbance(s.Disturbance):
    # CLASS VARIABLES

    # Directories

    INPUT_DIR = os.path.join(s.INPUT_DIR, 'fire')
    OUTPUT_DIR = os.path.join(s.OUTPUT_DIR, 'fire')
    FARSITE = 'farsite'
    # Inputs
    DEM_ascii = os.path.join(INPUT_DIR, FARSITE, 'dem.asc')
    SLOPE_ascii = os.path.join(INPUT_DIR, FARSITE, 'slope.asc')
    ASPECT_ascii = os.path.join(INPUT_DIR, FARSITE, 'aspect.asc')
    EC_START_ascii = os.path.join(INPUT_DIR, FARSITE, 'ec-climax.asc')
    FUEL_ascii = os.path.join(INPUT_DIR, FARSITE, 'fuel.asc')
    CANOPY_ascii = os.path.join(INPUT_DIR, FARSITE, 'canopy.asc')
    FPJ = os.path.join(INPUT_DIR, FARSITE, 'manhattan.FPJ')
    LCP = os.path.join(INPUT_DIR, FARSITE, 'MANHATTAN.LCP')
    IGNITION = os.path.join(INPUT_DIR, FARSITE, 'ignition.vct')
    FMD = os.path.join(INPUT_DIR, FARSITE, 'custom_fuel.fmd')
    FMS = os.path.join(INPUT_DIR, FARSITE, 'fuel_moisture.fms')
    ADJ = os.path.join(INPUT_DIR, FARSITE, 'fuel_adjustment.adj')
    WND = os.path.join(INPUT_DIR, FARSITE, 'wind.wnd')
    WTR = os.path.join(INPUT_DIR, FARSITE, 'weather.wtr')
    BURN_RASTERS = os.path.join(INPUT_DIR, 'script', 'burn_rasters')
    FARSITE_OUTPUT = os.path.join(BURN_RASTERS, 'farsite_output')

    def __init__(self, year):
        self.year = year
        self.ecocommunities = None
        self.drought = None
        self.climate_years = None
        self.climate_year = None
        self.weather = None
        self.translation_table = None
        self.header = None
        self.canopy = None
        self.forest_age = None
        self.time_since_disturbance = None
        self.fuel = None
        self.camps = None
        self.ignition_sites = None
        self.potential_ignition_sites = []
        self.weather_lines = []
        self.start_date = None
        self.con_month = None
        self.con_day = None
        self.start_month = None
        self.start_day = None
        self.end_month = None
        self.end_day = None

    def get_header(self):
        header = [linecache.getline(self.EC_START_ascii, i) for i in range(1, 7)]
        h = {}

        for line in header:
            attribute, value = line.split()
            h[attribute] = float(value)

        self.header = h

    def get_translation_table(self):
        translation = {}

        with open(os.path.join(self.INPUT_DIR, 'script', 'mannahatta.ec.translators.2.txt'), 'r') as translation_file:
            for line in translation_file:
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

        self.translation_table = translation

    def get_drought(self):
        drought = {}
        with open(os.path.join(self.INPUT_DIR, 'script', 'mannahatta-psdi.txt'), 'r') as drought_file:
            for line in drought_file:
                year, psdi = line.split('\t')
                drought[int(year)] = float(psdi)

        self.drought = drought

    def get_climate_years(self):
        climate_years = {}
        with open(os.path.join(self.INPUT_DIR, 'script', 'psdi-years.txt'), 'r') as psdiyears_file:
            for line in psdiyears_file:
                c_list = line.strip('\n').split('\t')
                climate_years[float(c_list[0])] = []
                for year in c_list[1:]:
                    if year != '':
                        climate_years[float(c_list[0])].append(int(year))

        self.climate_years = climate_years

    def select_climate_records(self):

        # Finds similar climate records based on PSDI

        psdi = self.drought[self.year]
        logging.info('Drought(PSDI): %r' % psdi)
        potential_years = []
        for climate_year in self.climate_years[psdi]:
            if 1876 <= climate_year <= 2006:
                potential_years.append(climate_year)

        # If a year doesn't have an equivalent climate year based on PSDI
        # Select equivalent from years with PSDI +/- 0.5
        if len(potential_years) == 0:
            for climate_year in self.climate_years[psdi + 0.5]:
                if 1876 <= climate_year <= 2006:
                    potential_years.append(climate_year)

            for climate_year in self.climate_years[psdi - 0.5]:
                if 1876 <= climate_year <= 2006:
                    potential_years.append(climate_year)

        self.climate_year = random.choice(potential_years)

    def set_weather_file(self):
        self.weather = os.path.join(self.INPUT_DIR, 'wtr', '%s.wtr' % self.climate_year)

    def get_clear_day(self):
        print self.weather_lines
        # convert window for ignition start date to ordinal date format
        start = datetime.date(day=s.FIRE_SEASON_START[0], month=s.FIRE_SEASON_START[1], year=self.year).toordinal()
        end = datetime.date(day=s.FIRE_SEASON_END[0], month=s.FIRE_SEASON_END[1], year=self.year).toordinal()

        rain = True
        while rain is True:
            random_date = datetime.date.fromordinal(random.randint(start, end))
            print random_date.month, random_date.day
            for i in self.weather_lines[1:]:
                if int(i[0]) == random_date.month and int(i[1]) == random_date.day:
                    if int(i[2]) == 0:
                        rain = False

        self.start_date = random_date
        self.start_month = random_date.month
        self.start_day = random_date.day

    def select_duration(self):

        # Select a start date without rain from the weather record
        with open(self.weather) as weather:
            for line in weather:
                record = line.split()
                self.weather_lines.append(record)
            self.get_clear_day()

        # Calculate conditioning date
        conditioning_date = datetime.date.fromordinal(self.start_date.toordinal() - s.CONDITIONING_LENGTH)

        self.con_month = conditioning_date.month
        self.con_day = conditioning_date.day


        for i in self.weather_lines[1:]:
            if int(i[0]) == self.start_month and int(i[1]) == self.start_day:
                start_index = self.weather_lines.index(i)
                for e in self.weather_lines[start_index:]:
                    if int(e[2]) > s.EXTINGUISH_THRESHOLD:
                        self.end_month = int(e[0])
                        self.end_day = int(e[1])
                        break

    def ascii_to_array(self, in_ascii_path):
        ascii = gdal.Open(in_ascii_path, GA_ReadOnly)
        array = gdal_array.DatasetReadAsArray(ascii)
        return array

    def array_to_ascii(self, out_ascii_path, array):
        out_asc = open(out_ascii_path, 'w')
        for attribute in self.header:
            out_asc.write(attribute)

        numpy.savetxt(out_asc, array, fmt="%4i")
        out_asc.close()

    def ecosystem_to_fuel(self):

        for index, cell_value in numpy.ndenumerate(self.ecocommunities):
            row_index = index[0]
            col_index = index[1]

            if self.time_since_disturbance[row_index][col_index] > s.SUCCESSION_TIME_CLIMAX:
                self.fuel[row_index][col_index] = self.translation_table[cell_value]['climax_fuel']

            elif self.time_since_disturbance[row_index][col_index] > s.SUCCESSION_TIME_MID:
                self.fuel[row_index][col_index] = self.translation_table[cell_value]['mid_fuel']

            else:
                self.fuel[row_index][col_index] = self.translation_table[cell_value]['new_fuel']

    def write_ignition(self):
        """
        :return:
        """
        # Writes ignition site as vct file for FARSITE and shp file for logging

        with open(self.IGNITION, 'w') as ignition_file:
            x = (self.header['xllcorner'] + (self.header['cellsize'] * self.ignition_sites[1]))
            y = (self.header['yllcorner'] + (self.header['cellsize'] * (self.header['nrows'] - self.ignition_sites[0])))

            ignition_file.write('1 %s %s\nEND' % (x, y))

            # Log ignition site
            # shutil.copyfile((self.INPUT_DIR, 'ignition.vct'),
            #                 (output_dir + '/log_rasters/%r_ignition.vct' % year))
            #
            # # Log as a point
            # point = arcpy.Point()
            # point.X = x
            # point.Y = y
            # ptGeoms = arcpy.PointGeometry(point)
            #
            # arcpy.CopyFeatures_management(ptGeoms, (output_dir + '/log_rasters/%r_ignition.shp' % year))

    def initial_from_ecocommunities(self, in_property):

        reference = ''

        if in_property == 'canopy':
            reference = 'max_canopy'
        elif in_property == 'forest_age':
            reference = 'start_age'

        array = numpy.empty((self.header['nrows'], self.header['ncols']))
        for index, value in numpy.ndenumerate(self.ecocommunities):
            array[index[0]][index[1]] = self.translation_table[int(value)][reference]

        if in_property == 'canopy':
            self.canopy = array
        elif in_property == 'forest_age':
            self.forest_age = array

    def get_ignition(self, in_ascii):
        array = self.ascii_to_array(in_ascii)
        for index, cell_value in numpy.ndenumerate(array):
            if cell_value == 1:
                    if self.fuel[index[0]][index[1]] not in s.UN_BURNABLE:
                        self.potential_ignition_sites.append(index)

        field_array = None

    def run_farsite(self):
        # cond_month, cond_day, start_month, start_day, end_month, end_day = select_duration(year)
        ordinal_start = datetime.date(day=self.start_day, month=self.start_month, year=1409).toordinal()
        ordinal_end = datetime.date(day=self.end_day, month=self.end_month, year=1409).toordinal()

        logging.info('Start date: %r/%r/%r | End date:  %r/%r/%r | Duration: %r days'% (self.start_month,
                                                                                        self.start_day,
                                                                                        self.year,
                                                                                        self.end_month,
                                                                                        self.end_day,
                                                                                        self.year,
                                                                                        (ordinal_end-ordinal_start)))
        pyautogui.PAUSE = 0.25

        # full extent test input_dir

        farsite = pywinauto.application.Application()
        farsite.start(r"C:\\Program Files (x86)\\farsite4.exe")

        # Load FARSITE project file
        logging.info('Loading FARSITE project file')

        # Open project window

        farsite_main_win = farsite.window_(title_re='.*FARSITE: Fire Area Simulator$')

        farsite_main_win.MenuItem('File->Load Project').Click()
        try:
            load_project = farsite.window_(title='Select Project File')
            load_project.SetFocus()

            pyautogui.typewrite(self.FPJ)
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
                pyautogui.typewrite(self.FUEL_ascii)
                pyautogui.press('enter')
                pyautogui.press(['down', 'space'])
                pyautogui.typewrite(self.CANOPY_ascii)
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
        for f in os.listdir(self.BURN_RASTERS):
            if re.search('farsite_output', f):
                os.remove(os.path.join(self.BURN_RASTERS,  f))

        # Export and output options
        logging.info('Setting export and output options')

        # Open export and output option window
        farsite_main_win.MenuItem('Output->Export and Output').Click()
        try:
            set_outputs = farsite.window_(title='Export and Output Options')
            set_outputs.SetFocus()
            set_outputs[u'&Select Rater File Name'].Click()
            pyautogui.typewrite(self.FARSITE_OUTPUT)
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
            while int(simulation_duration[u'Static5'].Texts()[0]) != self.con_month:
                if int(simulation_duration[u'Static5'].Texts()[0]) > self.con_month:
                    simulation_duration.Updown1.Decrement()
                if int(simulation_duration[u'Static5'].Texts()[0]) < self.con_month:
                    simulation_duration.Updown1.Increment()

            # Conditioning day
            while int(simulation_duration[u'Static6'].Texts()[0]) != self.con_day:
                if int(simulation_duration[u'Static6'].Texts()[0]) > self.con_day:
                    simulation_duration.Updown2.Decrement()
                if int(simulation_duration[u'Static6'].Texts()[0]) < self.con_day:
                        simulation_duration.Updown2.Increment()

            # Start month
            while int(simulation_duration[u'Static9'].Texts()[0]) != self.start_month:
                if int(simulation_duration[u'Static9'].Texts()[0]) > self.start_month:
                    simulation_duration.Updown5.Decrement()
                if int(simulation_duration[u'Static9'].Texts()[0]) < self.start_month:
                    simulation_duration.Updown5.Increment()

            # Start day
            while int(simulation_duration[u'Static10'].Texts()[0]) != self.start_day:
                if int(simulation_duration[u'Static10'].Texts()[0]) > self.start_day:
                    simulation_duration.Updown6.Decrement()
                if int(simulation_duration[u'Static10'].Texts()[0]) < self.start_day:
                    simulation_duration.Updown6.Increment()

            # End month
            while int(simulation_duration[u'Static13'].Texts()[0]) != self.end_month:
                if int(simulation_duration[u'Static13'].Texts()[0]) > self.end_month:
                    simulation_duration.Updown9.Decrement()
                if int(simulation_duration[u'Static13'].Texts()[0]) < self.end_month:
                    simulation_duration.Updown9.Increment()
            # End day
            while int(simulation_duration[u'Static14'].Texts()[0]) != self.end_day:
                if int(simulation_duration[u'Static14'].Texts()[0]) > self.end_day:
                    simulation_duration.Updown10.Decrement()
                if int(simulation_duration[u'Static14'].Texts()[0]) < self.end_day:
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
            pyautogui.typewrite(self.IGNITION)
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

