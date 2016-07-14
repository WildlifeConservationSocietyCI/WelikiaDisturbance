import settings as s
import disturbance as d
import numpy
import arcpy
import pywinauto
import time
import datetime
import random
import os
import shutil
from wmi import WMI


class FireDisturbance(d.Disturbance):
    # CLASS VARIABLES

    # Directories

    INPUT_DIR = os.path.join(s.INPUT_DIR, 'fire')
    OUTPUT_DIR = os.path.join(s.OUTPUT_DIR, 'fire')
    # INPUT_DIR = s.INPUT_DIR
    # OUTPUT_DIR = s.OUTPUT_DIR
    LOG_DIR = os.path.join(OUTPUT_DIR, '%s_%s.asc')
    # FARSITE = 'farsite'
    # SCRIPT = 'script'
    SPATIAL = 'spatial'
    TABULAR = 'tabular'

    # Inputs
    DEM_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'dem.asc')
    SLOPE_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'slope.asc')
    ASPECT_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'aspect.asc')

    FUEL_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'fuel.asc')
    TIME_SINCE_DISTURBANCE_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'time_since_disturbance.asc')

    TRAIL_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'fire_trails.asc')
    FPJ = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'PROJECT.FPJ')
    LCP = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'LANDSCAPE.LCP')
    IGNITION = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'ignition.shp')

    FMD = os.path.join(INPUT_DIR, TABULAR, 'custom_fuel.fmd')
    FMS = os.path.join(INPUT_DIR, TABULAR, 'fuel_moisture.fms')
    ADJ = os.path.join(INPUT_DIR, TABULAR, 'fuel_adjustment.adj')
    WND = os.path.join(INPUT_DIR, TABULAR, 'wind.wnd')
    WTR = os.path.join(INPUT_DIR, TABULAR, 'weather.wtr')
    TRANSLATOR = os.path.join(s.ROOT_DIR, 'ec_translator.txt')
    PSDI_YEARS = os.path.join(INPUT_DIR, TABULAR, 'psdi-years.txt')
    DROUGHT_YEARS = os.path.join(INPUT_DIR, TABULAR, 'mannahatta-psdi.txt')

    BURN_RASTERS = os.path.join(OUTPUT_DIR, 'burn_rasters')
    FARSITE_OUTPUT = os.path.join(BURN_RASTERS, '%s_farsite_output')

    _ecocommunities_filename = 'ecocommunities_%s.tif'

    def __init__(self, year):
        super(FireDisturbance, self).__init__(year)

        self.year = year
        # self.ECOCOMMUNITIES_ascii = os.path.join(self.INPUT_DIR, self.SCRIPT, s.REGION, 'ecocommunities_%s.asc' %
        # year)
        self.ecocommunities = arcpy.RasterToNumPyArray(self.ecocommunities, nodata_to_value=-9999)
        self.climax_communities = None
        self.drought = None
        self.climate_years = None
        self.equivalent_climate_year = None
        self.weather = []
        self.header = None
        self.header_text = None
        self.time_since_disturbance = None
        self.fuel = None
        self.camps = None
        self.ignition_sites = []
        self.potential_trail_ignition_sites = []
        self.potential_garden_ignition_sites = []
        self.potential_lightning_ignition_sites = []
        self.start_date = None
        self.con_month = None
        self.con_day = None
        self.start_month = None
        self.start_day = None
        self.end_month = None
        self.end_day = None
        self.area_burned = 0
        self.upland_area = 0
        self.farsite_output = os.path.join(self.BURN_RASTERS, '%s_farsite_output' % year)
        self.FLAME_LENGTH_ascii = os.path.join(self.BURN_RASTERS, '%s_farsite_output.fml' % year)
        self.flame_length = None
        self.memory = None

        self.garden_disturbance = None
        self.pond_disturbance = None

        # self.get_header()
        # self.set_communities()
        self.climax_communities = arcpy.RasterToNumPyArray(s.ecocommunities)
        self.set_upland_area()

    def get_memory(self):
        # Reports current memory usage

        w = WMI('.')
        result = w.query("SELECT WorkingSet FROM Win32_PerfRawData_PerfProc_Process WHERE IDProcess=%d" % os.getpid())
        self.memory = int(result[0].WorkingSet) / 1000000.0

    def set_drought_years(self):
        drought = {}
        with open(self.DROUGHT_YEARS, 'r') as drought_file:
            for line in drought_file:
                year, psdi = line.split('\t')
                drought[int(year)] = float(psdi)

        self.drought = drought

    def set_climate_years(self):
        climate_years = {}
        with open(self.PSDI_YEARS, 'r') as psdiyears_file:
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
        # s.logging.info('Drought(PSDI): %r' % psdi)
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

        self.equivalent_climate_year = random.choice(potential_years)

    def set_weather(self):

        weather = os.path.join(self.INPUT_DIR, 'wtr', '%s.wtr' % self.equivalent_climate_year)

        with open(weather) as weather:
            for line in weather:
                record = line.split()
                self.weather.append(record)

        shutil.copyfile(os.path.join(self.INPUT_DIR, 'wtr', '%r.wtr' % self.equivalent_climate_year), self.WTR)

    def get_clear_day(self):
        """
        :return:
        """

        # convert window for ignition start date to ordinal date format
        start = datetime.date(day=s.FIRE_SEASON_START[0], month=s.FIRE_SEASON_START[1], year=self.year).toordinal()
        end = datetime.date(day=s.FIRE_SEASON_END[0], month=s.FIRE_SEASON_END[1], year=self.year).toordinal()

        random_date = None
        rain = True
        while rain is True:
            # select random date within season
            random_date = datetime.date.fromordinal(random.randint(start, end))
            for i in self.weather[1:]:
                if int(i[0]) == random_date.month and int(i[1]) == random_date.day:
                    if int(i[2]) == 0:
                        rain = False

        self.start_date = random_date
        self.start_month = random_date.month
        self.start_day = random_date.day

    def select_duration(self):
        self.set_weather()

        # Select a start date without rain from the weather record
        self.get_clear_day()

        # Calculate conditioning date
        conditioning_date = datetime.date.fromordinal(self.start_date.toordinal() - s.CONDITIONING_LENGTH)

        self.con_month = conditioning_date.month
        self.con_day = conditioning_date.day

        # conditioning may start on 2/29, check and set to 2/28
        if self.con_month == 2 and self.con_day > 28:
            self.con_day = 28

        for i in self.weather[1:]:
            if int(i[0]) == self.start_month and int(i[1]) == self.start_day:
                start_index = self.weather.index(i)
                for e in self.weather[start_index:]:
                    if int(e[2]) > s.CRITICAL_RAINFALL:
                        self.end_month = int(e[0])
                        self.end_day = int(e[1])
                        break

    def write_wnd(self):
        with open(self.WTR, 'r') as weather_file:
            with open(self.WND, 'w') as wind_file:
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

    def set_fuel(self):
        """
        Set fuels array. Crosswalk communities and time since disturbance using translator table
        """
        s.logging.info('converting ecosystem to fuel model')

        if self.fuel is None:
            self.fuel = numpy.empty((self.header['nrows'], self.header['ncols']))
            self.fuel.astype(numpy.int32)

        for key in self.translation_table.index:
            fuel_c = self.translation_table.ix[key]['fuel_c']
            fuel_m = self.translation_table.ix[key]['fuel_m']
            fuel_n = self.translation_table.ix[key]['fuel_n']

            # set new fuels
            self.fuel[(self.ecocommunities == key) & (self.time_since_disturbance < s.TIME_TO_MID_FUEL)] = fuel_n

            # set mid fuel
            self.fuel[(self.ecocommunities == key) &
                      (self.time_since_disturbance >= s.TIME_TO_MID_FUEL) &
                      (self.time_since_disturbance < s.TIME_TO_CLIMAX_FUEL)] = fuel_m

            # set climax fuel
            self.fuel[(self.ecocommunities == key) & (self.time_since_disturbance >= s.TIME_TO_CLIMAX_FUEL)] = fuel_c

    def write_ignition(self):
        """
        :return:
        """
        # Writes ignition site as vct file for FARSITE and shp file for s.logging
        # s.logging.info(self.header)
        # s.logging.info(self.ignition_sites)
        point_geomtery_list = []
        point = arcpy.Point()

        # print self.ignition_sites
        for ignition, i in zip(self.ignition_sites, range(len(self.ignition_sites))):
            x = (self.header['xllcorner'] + (self.header['cellsize'] * ignition[1]))
            y = (self.header['yllcorner'] + (self.header['cellsize'] * (self.header['nrows'] - ignition[0])))
            point.X = x
            point.Y = y
            point_geometry = arcpy.PointGeometry(point)
            point_geomtery_list.append(point_geometry)

        if arcpy.Exists(self.IGNITION):
            arcpy.Delete_management(self.IGNITION)

        arcpy.CopyFeatures_management(point_geomtery_list, self.IGNITION)

        # with open(self.IGNITION, 'w') as ignition_file:
        #     for s, i in zip(self.ignition_sites, range(len(self.ignition_sites))):
        #         x = (self.header['xllcorner'] + (self.header['cellsize'] * s[1]))
        #         y = (self.header['yllcorner'] + (self.header['cellsize'] * (self.header['nrows'] - s[0])))
        #
        #         ignition_file.write('%s %s %s\n' % ((i + 1), x, y))
        #     ignition_file.write('END')

    def set_time_since_disturbance(self):

        if os.path.isfile(self.TIME_SINCE_DISTURBANCE_ascii):
            # s.logging.info('Setting time since disturbance')
            self.time_since_disturbance = self.raster_to_array(self.TIME_SINCE_DISTURBANCE_ascii)

        else:
            # s.logging.info('Assigning initial values to time since disturbance array')
            self.time_since_disturbance = numpy.empty((self.header['nrows'], self.header['ncols']))
            self.time_since_disturbance.astype(numpy.int32)
            self.time_since_disturbance.fill(s.INITIAL_TIME_SINCE_DISTURBANCE)
            self.array_to_ascii(self.TIME_SINCE_DISTURBANCE_ascii, self.time_since_disturbance)

        self.get_memory()
        # s.logging.info('memory usage: %r Mb' % self.memory)

    def get_ignition(self, in_ascii):
        array = self.raster_to_array(in_ascii)
        for index, cell_value in numpy.ndenumerate(array):
            if cell_value == 1:
                if self.fuel[index[0]][index[1]] not in s.NONBURNABLE:
                    self.potential_trail_ignition_sites.append(index)

    def run_farsite(self):
        # cond_month, cond_day, start_month, start_day, end_month, end_day = select_duration(year)
        ordinal_start = datetime.date(day=self.start_day, month=self.start_month, year=self.year).toordinal()
        ordinal_end = datetime.date(day=self.end_day, month=self.end_month, year=self.year).toordinal()

        s.logging.info('Start date: %r/%r/%r | End date:  %r/%r/%r | Duration: %r days' %
                       (self.start_month,
                        self.start_day,
                        self.year,
                        self.end_month,
                        self.end_day,
                        self.year,
                        (ordinal_end - ordinal_start)))

        # full extent test input_dir

        farsite = pywinauto.Application()
        farsite.start(os.path.join('C:\\', 'Program Files (x86)', 'farsite4.exe'))

        # Load FARSITE project file
        # s.logging.info('Loading FARSITE project file')

        # Open project window

        farsite_main_win = farsite.window_(title_re='.*FARSITE: Fire Area Simulator$')

        farsite_main_win.Wait('ready')
        farsite_main_win.SetFocus().MenuItem('File->Load Project').Click()

        try:
            load_project = farsite.window_(title='Select Project File')
            load_project.Wait('ready').SetFocus()
            load_project[u'File &name:Edit'].SetEditText(self.FPJ)
            load_project[u'&Open'].Click()
            # time.sleep(.5)
            # farsite[u'Custom Fuel Model File Converted to new Format'].Wait('ready').SetFocus()
            # farsite[u'Custom Fuel Model File Converted to new Format'][u'OK'].Click()
            # s.logging.info('Project file loaded')

        except pywinauto.findwindows.WindowNotFoundError:
            s.logging.error('Can not find SELECT PROJECT FILE window')
            farsite.Kill_()

        # Load FARSITE landscape file
        # s.logging.info('Loading FARSITE landscape file')

        # Open project input window
        farsite_main_win.MenuItem('Input-> Project Inputs').Click()

        try:
            project_inputs = farsite.window_(title='FARSITE Project')
            project_inputs.Wait('ready').SetFocus()
            project_inputs[u'->13'].Click()

            # Load fuel and canopy rasters
            try:
                landscape_load = farsite.window_(title='Landscape (LCP) File Generation')
                landscape_load.Wait('ready').SetFocus()
                landscape_load[u'&Fuel Model ASCII'].Click()
                load_fuel = farsite.window_(title='Select ASCII Raster File')
                load_fuel.SetFocus()
                load_fuel[u'File &name:Edit'].SetEditText(self.FUEL_ascii)
                load_fuel[u'&Open'].DoubleClick()
                landscape_load.SetFocus()
                landscape_load.Wait('ready')
                landscape_load[u'Canopy Co&ver ASCII'].Click()
                load_canopy = farsite.window_(title='Select ASCII Raster File')
                load_canopy.SetFocus()
                load_canopy.Wait('ready')
                load_canopy[u'File &name:Edit'].SetEditText(self.CANOPY_ascii)
                load_canopy[u'&Open'].DoubleClick()
                landscape_load.SetFocus()
                landscape_load[u'&OK'].Click()

            except pywinauto.findwindows.WindowNotFoundError:
                s.logging.error('Can not find Landscape (LCP) File Generation window')
                farsite.Kill_()

            # Wait while FARSITE generates the landscape file
            landscape_generated = farsite.window_(title_re='.*Landscape Generated$')
            landscape_generated.Wait('visible', timeout=10000, retry_interval=0.5)
            landscape_generated.SetFocus()
            landscape_generated[u'OK'].Click()

            # s.logging.info('landscape file loaded')

            project_inputs.SetFocus()
            project_inputs[u'&OK'].Click()

        except pywinauto.findwindows.WindowNotFoundError:
            s.logging.info('Unable to generate landscape file')
            farsite.Kill_()

        # Delete FARSITE_output from output folder
        # logging.info('Deleting previous FARSITE outputs')
        # for f in os.listdir(self.BURN_RASTERS):
        #     if re.search('%s_farsite_output' % self.year, f):
        #         os.remove(os.path.join(self.BURN_RASTERS, f))

        # Export and output options
        # s.logging.info('Setting export and output options')

        # Open export and output option window
        farsite_main_win.SetFocus().MenuItem('Output->Export and Output').Click()
        try:
            set_outputs = farsite.window_(title='Export and Output Options')
            set_outputs.Wait('ready').SetFocus()
            set_outputs[u'&Select Rater File Name'].Click()
            select_raster = farsite.window_(title='Select Raster File')
            select_raster[u'File &name:Edit'].SetEditText(self.farsite_output)
            select_raster[u'&Save'].DoubleClick()
            set_outputs[u'Flame Length (m)'].Click()
            # set_outputs[u'&Default'].Click()
            if set_outputs[u'XUpDown'].GetValue() != self.header['cellsize']:
                set_outputs[u'&Default'].Click()
            set_outputs[u'&OK'].Click()
            # s.logging.info('Outputs set')

        except pywinauto.findwindows.WindowNotFoundError:
            s.logging.error('Can not find EXPORT AND OUTPUT OPTIONS window')
            farsite.Kill_()

        # Set simulation parameters
        # s.logging.info('Setting simulation parameters')

        # Open parameter window
        farsite_main_win.SetFocus().MenuItem('Model->Parameters').Click()
        try:
            set_parameters = farsite.window_(title='Model Parameters')
            set_parameters.SetFocus()
            set_parameters.TypeKeys('{RIGHT 90}')
            set_parameters.TypeKeys('{TAB 2}')
            set_parameters.TypeKeys('{LEFT 30}')
            set_parameters.TypeKeys('{TAB}')
            set_parameters.TypeKeys('{LEFT 20}')
            set_parameters[u'&OK'].Click()
            time.sleep(3)
            # s.logging.info('Parameters set')

        except pywinauto.findwindows.WindowNotFoundError:
            s.logging.error('Can not find MODEL PARAMETERS window')
            farsite.Kill_()

        # fire behavior options: disable crown fire
        # Open fire behavior window
        farsite_main_win.SetFocus().MenuItem('Model->Fire Behavior Options').Click()
        try:
            set_fire_behavior = farsite.window_(title='Fire Behavior Options')
            set_fire_behavior.SetFocus()
            set_fire_behavior[u'Enable Crownfire'].UnCheck()
            set_fire_behavior[u'&OK'].Click()

        except pywinauto.findwindows.WindowNotFoundError:
            s.logging.error('can not find FIRE BEHAVIOR OPTIONS window')
            farsite.Kill_()

        # Set number of simulation threads
        farsite_main_win.SetFocus().MenuItem('Simulate->Options').Click()
        try:
            simulation_options = farsite.window_(title='Simulation Options')
            simulation_options.SetFocus()
            simulation_options.Wait('ready')
            simulation_options.UpDown.SetValue(8)
            simulation_options[u'&OK'].Click()

        except pywinauto.findwindows.WindowNotFoundError:
            s.logging.error('can not find SIMULATION OPTIONS window')
            farsite.Kill_()

        # Open duration window
        farsite_main_win.SetFocus().MenuItem('Simulate->Duration').Click()
        try:
            simulation_duration = farsite.window_(title='Simulation Duration')
            simulation_duration.SetFocus()

            if simulation_duration[u'Use Conditioning Period for Fuel Moistures'].GetCheckState() == 0:
                simulation_duration[u'Use Conditioning Period for Fuel Moistures'].Click()

            simulation_duration.SetFocus()
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

            # s.logging.info('Duration set')

        except farsite.findwindows.WindowNotFoundError:
            s.logging.info('can not find SIMULATION DURATION window')
            farsite.Kill_()

        # Initiate simulation
        farsite_main_win.SetFocus().MenuItem('Simulate->Initiate/Terminate').Click()
        landscape_initiated = farsite.window_(title_re='LANDSCAPE:*')
        landscape_initiated.Wait('ready', timeout=40)

        time.sleep(s.INITIATE_RENDER_WAIT_TIME)

        # Set Ignition
        farsite_main_win.SetFocus().MenuItem('Simulate->Modify Map->Import Ignition File').Click()
        try:
            set_ignition = farsite.window_(title='Select Vector Ignition File')
            set_ignition.SetFocus()
            set_ignition.Wait('ready')
            set_ignition[u'Files of &type:ComboBox'].Select(u', SHAPE FILES (*.SHP)')
            set_ignition[u'File &name:Edit'].SetEditText(self.IGNITION)
            set_ignition[u'&Open'].DoubleClick()
            # try:
            #     contains_polygon = farsite.window_(title=self.IGNITION)
            #     contains_polygon.SetFocus()
            #     contains_polygon[u'&No'].Click()
            #     contains_line = farsite.window_(title=self.IGNITION)
            #     contains_line.SetFocus()
            #     contains_line[u'&No'].Click()
            # except:
            #     print 'no poly line dialog'
        except farsite.findwindows.WindowNotFoundError:
            s.logging.error('can not find SELECT VECTOR IGNITION FILE window')

        s.logging.info('Starting simulation')
        farsite_main_win.SetFocus().MenuItem(u'&Simulate->&Start/Restart').Click()
        simulation_complete = farsite.window_(title_re='.*Simulation Complete')
        simulation_complete.Wait(wait_for='ready', timeout=s.SIMULATION_TIMEOUT, retry_interval=0.5)
        simulation_complete.SetFocus()
        simulation_complete[u'OK'].Click()
        s.logging.info('Simulation complete')
        # Exit FARSITE
        farsite.Kill_()

    def tree_mortality(self):
        """
        Tree_mortality calculates the percentage of the canopy in a cell killed during a burning event
        This estimate is based on the age of the forest and the length of the flame
        Model logic and tree size/diameter regressions from Tim Bean
        :param: flame
        :param: age
        """
        flame = self.flame_length
        age = self.forest_age

        # Convert flame length to ft
        flame[flame == -1] = 0
        flame *= 3.2808399

        # Calculate scorch height
        scorch = (3.1817 * (flame ** 1.4503))

        # Calculate tree height
        log_age = numpy.ma.log(age)

        tree_height = numpy.where(age > 0, numpy.array(log_age * 44 - 93), age)
        tree_height[tree_height < 0] = 1

        # Calculate tree diameter at breast height
        dbh = numpy.array(25.706 * log_age - 85.383)

        dbh[age <= 35] = 5
        dbh[age <= 25] = 3
        dbh[age <= 20] = 2
        dbh[age <= 15] = 1

        # Calculate bark thickness
        bark_thickness = 0.045 * dbh

        # Define crown ratio
        crown_ratio = 0.4

        # Calculate crown height
        crown_height = tree_height * (1 - crown_ratio)

        # Calculate crown kill
        scorch_crown_height_dif = scorch - crown_height
        scorch_crown_height_dif[scorch_crown_height_dif < 0] = 0

        height_x_cr = tree_height * crown_ratio
        height_x_cr = numpy.ma.array(height_x_cr, mask=(height_x_cr == 0))

        crown_kill = numpy.where(scorch_crown_height_dif > 0,
                                 numpy.array(41.961 * numpy.ma.log(
                                     100 * numpy.ma.divide(scorch_crown_height_dif, height_x_cr)) - 89.721), 0)

        crown_kill[crown_kill < 0] = 0
        crown_kill[crown_kill > 100] = 100

        # calculate percent mortality
        mortality = numpy.where(flame > 0,
                                numpy.array(
                                    1 / (1 + numpy.exp((-1.941 + (6.3136 * (1 - (numpy.exp(-1 * bark_thickness))))) - (
                                        .000535 * (crown_kill ** 2))))), flame)

        return 1 - mortality

    def retrogression(self):
        for key in self.translation_table.index:
            # reclassify burned forest
            if self.translation_table.ix[key]['forest'] == 1:

                # Retrogression forested wetlands
                if key == 629:
                    self.ecocommunities[(self.ecocommunities == key) &
                                        (self.flame_length != 0) &
                                        (self.canopy < 90)] = 625

                    self.ecocommunities[(self.ecocommunities == key) &
                                        (self.flame_length != 0) &
                                        (self.canopy < 50)] = 624

                # Retrogression all other forested communities
                else:
                    self.ecocommunities[(self.ecocommunities == key) &
                                        (self.flame_length != 0) &
                                        (self.canopy < 90)] = s.SHRUBLAND_ID

                    self.ecocommunities[(self.ecocommunities == key) &
                                        (self.flame_length != 0) &
                                        (self.canopy < 50)] = s.GRASSLAND_ID

            # Retrogression shrubland
            if key == s.SHRUBLAND_ID:
                self.ecocommunities[(self.ecocommunities == key) &
                                    (self.flame_length != 0) &
                                    (self.canopy < 50)] = s.GRASSLAND_ID

            # Retrogression shrub-swamp
            if key == 625:
                self.ecocommunities[(self.ecocommunities == key) &
                                    (self.flame_length != 0) &
                                    (self.canopy < 50)] = 624

            # Reset forest age
            l = [624, 625, 648, 649]
            for i in l:
                self.forest_age[self.ecocommunities == i] = 0

    def run_year(self):

        start_time = time.time()

        # s.logging.info('Year: %r' % self.year)

        # set weather and simulation duration
        self.set_climate_years()
        self.set_drought_years()
        self.select_climate_records()
        self.select_duration()
        self.write_wnd()
        self.get_header()

        # set tracking rasters
        self.set_time_since_disturbance()
        self.set_fuel()

        self.array_to_ascii(self.FUEL_ascii, self.fuel)

        initialize_time = time.time()
        s.logging.info('initialize run time: %s' % (initialize_time - start_time))

        # Check if trail fires escaped
        scaled_expected_trail_escape = s.EXPECTED_TRAIL_ESCAPE * self.upland_area
        s.logging.info('upland area: %s | scaled expected trail fire: %s'
                       % (self.upland_area, scaled_expected_trail_escape))

        number_of_trail_ignitions = numpy.random.poisson(lam=scaled_expected_trail_escape)
        if number_of_trail_ignitions > 0:

            # Get list of potential trail fire sites
            trail_array = self.raster_to_array(self.TRAIL_ascii)

            rows, cols = numpy.where((trail_array == 1) &
                                     (self.time_since_disturbance >= s.TRAIL_OVERGROWN_YRS) &
                                     (self.fuel != 14) &
                                     (self.fuel != 16) &
                                     (self.fuel != 98) &
                                     (self.fuel != 99))

            for row, col in zip(rows, cols):
                self.potential_trail_ignition_sites.append((row, col))

            # Select i sites from potential sites and appended to ignition_sites
            s.logging.info('potential trail fire sites: %s' % len(self.potential_garden_ignition_sites))
            if len(self.potential_trail_ignition_sites) > 0:
                for i in range(number_of_trail_ignitions):
                    self.ignition_sites.append(random.choice(self.potential_trail_ignition_sites))

        # Check if garden fires escaped
        number_of_garden_ignitions = numpy.random.poisson(lam=s.EXPECTED_GARDEN_ESCAPE)
        if number_of_garden_ignitions > 0:

            # Get list of potential garden fire sites
            if self.garden_disturbance is not None:
                rows, cols = numpy.where((self.ecocommunities == 650) &
                                         (self.garden_disturbance <= 1))

                for row, col in zip(rows, cols):
                    self.potential_garden_ignition_sites.append((row, col))

            # Select i sites from potential sites and appended to ignition_sites
            if len(self.potential_garden_ignition_sites) > 0:
                for i in range(number_of_garden_ignitions):
                    self.ignition_sites.append(random.choice(self.potential_garden_ignition_sites))

        # Check if lightning fires
        scaled_expected_lightning_fire = s.EXPECTED_LIGHTNING_FIRE * self.upland_area
        s.logging.info('upland area: %s | scaled expected lightning fire: %s'
                       % (self.upland_area, scaled_expected_lightning_fire))
        number_of_lightning_ignitions = numpy.random.poisson(lam=scaled_expected_lightning_fire)
        if number_of_lightning_ignitions > 0:
            rows, cols = numpy.where(((self.fuel != 14) &
                                      (self.fuel != 16) &
                                      (self.fuel != 98) &
                                      (self.fuel != 99)))

            for row, col in zip(rows, cols):
                self.potential_lightning_ignition_sites.append((row, col))

            # Select i sites from potential sites and appended to ignition_sites
            if len(self.potential_lightning_ignition_sites) > 0:
                for i in range(number_of_lightning_ignitions):
                    self.ignition_sites.append(random.choice(self.potential_lightning_ignition_sites))

        s.logging.info('escaped trail fires: %s' % number_of_trail_ignitions)
        s.logging.info('escaped garden fires: %s' % number_of_garden_ignitions)
        s.logging.info('lightning fires: %s' % number_of_lightning_ignitions)

        s.logging.info('ignition sites: %s' % self.ignition_sites)
        if len(self.ignition_sites) > 0:

            # s.logging.info('Creating ignition point')

            # Write selected ignition sites to .shp file for FARSITE
            self.write_ignition()

            # Select climate file
            self.select_climate_records()
            # s.logging.info('Selected climate equivalent-year: %r' % self.equivalent_climate_year)

            # Get matching climate year file for FARSITE
            shutil.copyfile(os.path.join(self.INPUT_DIR, 'wtr', '%r.wtr' % self.equivalent_climate_year), self.WTR)

            # Create wind file
            self.write_wnd()

            # Run Farsite
            self.run_farsite()

            # Create flame length array
            if os.path.exists(self.FLAME_LENGTH_ascii):
                self.flame_length = self.raster_to_array(self.FLAME_LENGTH_ascii)
                self.flame_length[self.flame_length == -1] = 0
                self.area_burned = numpy.count_nonzero(self.flame_length)

                # Update time since disturbance
                self.time_since_disturbance[self.flame_length > 0] = 0
                self.time_since_disturbance[self.flame_length <= 0] += 1

                # Calculate tree mortality due to fire
                percent_mortality = self.tree_mortality()

                # Update canopy based on percent mortality
                self.canopy = numpy.where(self.flame_length != 0,
                                          numpy.array(self.canopy * percent_mortality, dtype=numpy.int8),
                                          self.canopy)

                # Update communities based on burned canopy
                self.retrogression()

            self.get_memory()
            # s.logging.info('memory usage: %r Mb' % self.memory)

        # s.logging.info('Area burned %r: %r acres' % (self.year, (self.area_burned * 100 * 0.000247105)))

        # Revise fuel model
        self.set_fuel()

        # s.logging.info('saving arrays as ascii')
        self.array_to_ascii(self.FUEL_ascii, self.fuel)
        self.array_to_ascii(self.CANOPY_ascii, self.canopy)
        self.array_to_ascii(self.FOREST_AGE_ascii, self.forest_age)
        self.array_to_ascii(self.TIME_SINCE_DISTURBANCE_ascii, self.time_since_disturbance)
        self.array_to_ascii(self.LOG_DIR % (self.year, 'ecocommunities'), self.ecocommunities)

        # save the updated community array as a TIF raster to the shared output directory
        out_raster = arcpy.NumPyArrayToRaster(in_array=self.ecocommunities,
                                              lower_left_corner=arcpy.Point(self.header['xllcorner'],
                                                                            self.header['yllcorner']),
                                              x_cell_size=self.header['cellsize'],
                                              value_to_nodata=-9999)

        out_raster.save(os.path.join(s.OUTPUT_DIR, 'ecocommunities_%s.tif' % self.year))

        # log outputs when a fire occurs and on the file year
        if self.area_burned > 0 or self.year == max(s.RUN_LENGTH):
            # s.logging.info('copying outputs to log folder')
            shutil.copyfile(self.FUEL_ascii, self.LOG_DIR % (self.year, 'fuel'))
            shutil.copyfile(self.CANOPY_ascii, self.LOG_DIR % (self.year, 'canopy'))
            shutil.copyfile(self.FOREST_AGE_ascii, self.LOG_DIR % (self.year, 'forest_age'))
        shutil.copyfile(self.FUEL_ascii, self.LOG_DIR % (self.year, 'fuel'))
        shutil.copyfile(self.CANOPY_ascii, self.LOG_DIR % (self.year, 'canopy'))
        shutil.copyfile(self.FOREST_AGE_ascii, self.LOG_DIR % (self.year, 'forest_age'))
        shutil.copyfile(self.TIME_SINCE_DISTURBANCE_ascii, self.LOG_DIR % (self.year, 'time_since_disturbance'))

        end_time = time.time()

        run_time = end_time - start_time

        s.logging.info('runtime: %s' % run_time)
