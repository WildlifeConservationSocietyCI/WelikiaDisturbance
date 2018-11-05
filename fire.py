import settings as s
import disturbance as d
import tree_allometry as ta
import numpy as np
import arcpy
import pywinauto
import time
import datetime
import random
import os
import shutil
import utils
import fnmatch
from wmi import WMI


class FireDisturbance(d.Disturbance):
    # CLASS VARIABLES

    # Directories

    INPUT_DIR = os.path.join(s.INPUT_DIR, 'fire')
    OUTPUT_DIR = os.path.join(s.OUTPUT_DIR, 'fire')
    # INPUT_DIR = s.INPUT_DIR
    # OUTPUT_DIR = s.OUTPUT_DIR
    # LOG_DIR = os.path.join(OUTPUT_DIR, '%s_%s.asc')
    SPATIAL = 'spatial'
    TABULAR = 'tabular'

    # Inputs
    DEM_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'dem.asc')
    SLOPE_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'slope.asc')
    ASPECT_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'aspect.asc')

    FUEL_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'fuel.asc')
    CANOPY_ascii = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'canopy.asc')
    TIME_SINCE_DISTURBANCE_raster = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'time_since_disturbance.tif')

    TRAIL_raster = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'trails.tif')
    HUNTING_raster = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'hunting_sites.tif')
    FPJ = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'PROJECT.FPJ')
    LCP = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'LANDSCAPE.LCP')
    IGNITION = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'ignition.shp')

    FMD = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'custom_fuel_test.fmd')
    FMS = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'fuel_moisture_test.fms')
    ADJ = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'fuel_adjustment_test.adj')
    WND = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'wind.wnd')
    WTR = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'weather.wtr')
    PSDI_YEARS = os.path.join(s.ROOT_DIR, 'tables', 'fire', 'psdi-years.txt')
    DROUGHT_YEARS = os.path.join(s.ROOT_DIR, 'tables', 'fire', 'mannahatta-psdi.txt')

    BURN_RASTERS = os.path.join(OUTPUT_DIR, 'burn_rasters')
    FARSITE_OUTPUT = os.path.join(BURN_RASTERS, '%s_farsite_output')

    def __init__(self, year):
        super(FireDisturbance, self).__init__(year)

        self.year = year
        self.ecocommunities = arcpy.RasterToNumPyArray(self.ecocommunities).astype(np.int32)
        self.drought = None
        self.climate_years = None
        self.equivalent_climate_year = None
        self.weather = []
        self.header = None
        self.header_text = None
        self.shape = None
        self.time_since_disturbance = None
        self.fuel = None
        self.camps = None
        self.ignition_sites = []
        self.potential_trail_ignition_sites = []
        self.potential_garden_ignition_sites = []
        self.potential_hunting_ignition_sites = []
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

        # if self.fuel is None:
        print self.shape
        self.fuel = np.empty(shape=self.shape, dtype=np.int32)
        # self.fuel.astype(np.int32)
        print ('fuel shape', self.fuel.shape)
        print ('ecocommunities shape', self.ecocommunities.shape)
        print ('time since disturbance shape', self.time_since_disturbance.shape)
        for key in self.community_table.index:
            # get fuel values for new, mid and climax states
            fuel_c = self.community_table.loc[key, 'fuel_c']
            fuel_m = self.community_table.loc[key, 'fuel_m']
            fuel_n = self.community_table.loc[key, 'fuel_n']

            # set new fuels
            self.fuel[(self.ecocommunities == key) & (self.time_since_disturbance < s.TIME_TO_MID_FUEL)] = fuel_n

            # set mid fuel
            self.fuel[(self.ecocommunities == key) &
                      (self.time_since_disturbance >= s.TIME_TO_MID_FUEL) &
                      (self.time_since_disturbance < s.TIME_TO_CLIMAX_FUEL)] = fuel_m

            # set climax fuel
            self.fuel[(self.ecocommunities == key) & (self.time_since_disturbance >= s.TIME_TO_CLIMAX_FUEL)] = fuel_c

    def set_fuel_dbh(self):
        """
        Set fuels array based on community type and dbh
        """
        s.logging.info('converting ecosystem to fuel model')

        # if self.fuel is None:
        self.fuel = np.empty(shape=self.shape, dtype=np.int32)
        for key in self.community_table.index:

            # get fuel values for new, mid and climax states
            fuel_c = self.community_table.loc[key, 'fuel_c']
            fuel_m = self.community_table.loc[key, 'fuel_m']
            fuel_n = self.community_table.loc[key, 'fuel_n']

            if self.community_table.loc[key, 'forest'] == 0:
                # set new fuels
                self.fuel[(self.ecocommunities == key) & (self.time_since_disturbance < s.TIME_TO_MID_FUEL)] = fuel_n

                # set mid fuel
                self.fuel[(self.ecocommunities == key) &
                          (self.time_since_disturbance >= s.TIME_TO_MID_FUEL) &
                          (self.time_since_disturbance < s.TIME_TO_CLIMAX_FUEL)] = fuel_m

                # set climax fuel
                self.fuel[(self.ecocommunities == key) & (self.time_since_disturbance >= s.TIME_TO_CLIMAX_FUEL)] = fuel_c

            if self.community_table.loc[key, 'forest'] == 1:
                # set new fuels
                self.fuel[(self.ecocommunities == key) & (self.dbh < 5)] = fuel_n

                # set mid fuel
                self.fuel[(self.ecocommunities == key) &
                          (self.dbh >= 5) & (self.dbh <= 10)] = fuel_m

                # set climax fuel
                self.fuel[
                    (self.ecocommunities == key) & (self.dbh > 10)] = fuel_c

    def write_ignition(self):
        """
        :return:
        """
        # Writes ignition site as vct file for FARSITE and shp file for s.logging
        # s.logging.info(self.header)
        # s.logging.info(self.ignition_sites)
        point_geomtery_list = []
        point = arcpy.Point()

        header, header_text, shape = utils.get_ascii_header(self.REFERENCE_ascii)
        print(self.ignition_sites)
        for ignition, i in zip(self.ignition_sites, range(len(self.ignition_sites))):
            x = (header['xllcorner'] + (s.CELL_SIZE * ignition[1]))
            y = (header['yllcorner'] + (s.CELL_SIZE * (self.shape[0] - ignition[0])))
            print ('point coordinates', x, y)
            point.X = x
            point.Y = y
            point_geometry = arcpy.PointGeometry(point)
            point_geomtery_list.append(point_geometry)

        if arcpy.Exists(self.IGNITION):
            arcpy.Delete_management(self.IGNITION)

        arcpy.CopyFeatures_management(point_geomtery_list, self.IGNITION)

    def set_time_since_disturbance(self):

        if os.path.isfile(self.TIME_SINCE_DISTURBANCE_raster):
            # s.logging.info('Setting time since disturbance')
            self.time_since_disturbance = utils.raster_to_array(self.TIME_SINCE_DISTURBANCE_raster)

        else:
            # s.logging.info('Assigning initial values to time since disturbance array')
            self.time_since_disturbance = np.empty(shape=self.shape, dtype=np.int32)
            print ('time since disturvance', self.time_since_disturbance.shape)
            self.time_since_disturbance.fill(s.INITIAL_TIME_SINCE_DISTURBANCE)
            utils.array_to_raster(self.time_since_disturbance, self.TIME_SINCE_DISTURBANCE_raster,
                                  geotransform=self.geot, projection=self.projection)

        self.get_memory()
        # s.logging.info('memory usage: %r Mb' % self.memory)

    def get_ignition(self, in_ascii):
        array = utils.raster_to_array(in_ascii)
        for index, cell_value in np.ndenumerate(array):
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

        farsite = pywinauto.Application()
        farsite.start(s.FARSITE)

        # Load FARSITE project file
        # s.logging.info('Loading FARSITE project file')

        # Open project window

        farsite_main_win = farsite.window_(title_re='.*FARSITE: Fire Area Simulator$')

        farsite_main_win.Wait('ready', timeout=100)
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

            project_inputs.Wait('ready').SetFocus()
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
            if set_outputs[u'XUpDown'].GetValue() != s.FARSITE_RESOLUTION:
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
            set_parameters[u'ScrollBar3'].Click()
            # set perimeter resolution
            while int(set_parameters[u'Static3'].WindowText().split()[0]) != s.PERIMETER_RESOLUTION:
                if int(set_parameters[u'Static3'].WindowText().split()[0]) > s.PERIMETER_RESOLUTION:
                    set_parameters.TypeKeys('{LEFT}')
                else:
                    set_parameters.TypeKeys('{RIGHT}')
            # set distance resolution
            set_parameters[u'Distance ResolutionScrollBar'].Click()
            while int(set_parameters[u'Static4'].WindowText().split()[0]) != s.DISTANCE_RESOLUTION:
                if int(set_parameters[u'Static4'].WindowText().split()[0]) > s.DISTANCE_RESOLUTION:
                    set_parameters.TypeKeys('{LEFT}')
                else:
                    set_parameters.TypeKeys('{RIGHT}')
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
            #     print('no poly line dialog')
        except farsite.findwindows.WindowNotFoundError:
            s.logging.error('can not find SELECT VECTOR IGNITION FILE window')

        s.logging.info('Starting simulation')
        farsite_main_win.Wait('ready', timeout=20)
        farsite_main_win.SetFocus().MenuItem(u'&Simulate->&Start/Restart').Click()
        simulation_complete = farsite.window_(title_re='.*Simulation Complete')
        simulation_complete.Wait(wait_for='ready', timeout=s.SIMULATION_TIMEOUT, retry_interval=0.5)
        simulation_complete.SetFocus()
        simulation_complete[u'OK'].Click()
        s.logging.info('Simulation complete')
        # Exit FARSITE
        farsite.Kill_()

    @property
    def tree_mortality(self):
        """
        Tree_mortality calculates the percentage of the canopy in a cell killed during a burning event
        This estimate is based on the age of the forest and the length of the flame.
        Model logic and tree size/diameter relationships from Bean 2007
        :param: flame
        :param: age
        """
        flame = self.flame_length
        age = self.forest_age

        # Convert flame length to ft
        flame[flame == -9999] = 0
        flame *= 3.2808399

        # Calculate scorch height
        scorch = (3.1817 * (flame ** 1.4503))

        tree_height = np.empty(shape=self.shape)
        for index, row in self.community_table.iterrows():
            if row.forest == 1:
                tree_height_model = int(row.tree_height_model)
                site_index = int(row.site_index)
                tree_height = np.where(self.ecocommunities == index, ta.tree_height_carmean(key=tree_height_model,
                                                                                            A=age,
                                                                                            S=site_index), tree_height)
        # Save tree height array to raster
        utils.array_to_raster(tree_height, os.path.join(self.OUTPUT_DIR, 'tree_height.tif'),
                              geotransform=self.geot, projection=self.projection)

        # Calculate bark thickness
        vsp_multiplier = np.empty(shape=self.shape)

        for index, row in self.community_table.iterrows():
            vsp_multiplier[self.ecocommunities == index] = row.bark_thickness

        bark_thickness = vsp_multiplier * self.dbh

        # Save bark thickness array to raster
        utils.array_to_raster(bark_thickness, os.path.join(self.OUTPUT_DIR, 'bark_thickness.tif'),
                              geotransform=self.geot, projection=self.projection)


        # Define crown ratio
        crown_ratio = 0.4

        # Calculate crown height
        crown_height = tree_height * (1 - crown_ratio)

        # Calculate crown kill
        # identify cells where the height of scorch is greater than the height of the crown
        crown_scorch = scorch - crown_height
        crown_scorch[crown_scorch < 0] = 0

        crown_length = tree_height * crown_ratio
        crown_length = np.ma.array(crown_length, mask=(crown_length == 0))

        # zero place-holder array
        zero = np.full(shape=flame.shape, fill_value=0, dtype=np.float32)

        crown_kill = np.where(crown_scorch > 0,
                              np.array(41.961 * (100 * np.ma.log(np.ma.divide(crown_scorch, crown_length))) - 89.721),
                              zero)

        crown_kill[crown_kill < 0] = 0
        crown_kill[crown_kill > 100] = 100

        # calculate percent mortality
        mortality = np.where(flame > 0,
                             np.array(
                                 1 / (1 + np.exp((-1.941 + (6.3136 * (1 - (np.exp(-1 * bark_thickness))))) - (
                                     .000535 * (crown_kill ** 2))))), zero)

        return 1 - mortality

    def retrogression(self):
        for index, row in self.community_table.iterrows():
            # reclassify burned forest
            if row.forest == 1:

                # Retrogression forested wetlands
                if index == s.RED_MAPLE_HARDWOOD_SWAMP or index == s.RED_MAPLE_BLACK_GUM_SWAMP \
                        or index == s.RED_MAPLE_SWEETGUM_SWAMP or index == s.ATLANTIC_CEDAR_SWAMP:

                    self.ecocommunities[(self.ecocommunities == index) &
                                        (self.flame_length != 0) &
                                        (self.canopy < self.community_table.ix[
                                            s.SHRUB_SWAMP_ID].max_canopy)] = s.SHRUB_SWAMP_ID

                    self.ecocommunities[(self.ecocommunities == index) &
                                        (self.flame_length != 0) &
                                        (self.canopy < self.community_table.ix[
                                            s.SHALLOW_EMERGENT_MARSH_ID].max_canopy)] = s.SHALLOW_EMERGENT_MARSH_ID

                # Retrogression all other forested communities
                else:
                    self.ecocommunities[(self.ecocommunities == index) &
                                        (self.flame_length != 0) &
                                        (self.canopy < self.community_table.ix[
                                            s.SUCCESSIONAL_SHRUBLAND_ID].max_canopy)] = s.SUCCESSIONAL_SHRUBLAND_ID

                    self.ecocommunities[(self.ecocommunities == index) &
                                        (self.flame_length != 0) &
                                        (self.canopy < self.community_table.ix[
                                            s.SUCCESSIONAL_GRASSLAND_ID].max_canopy)] = s.SUCCESSIONAL_GRASSLAND_ID

            # Retrogression shrub-land
            if index == s.SUCCESSIONAL_SHRUBLAND_ID:
                self.ecocommunities[(self.ecocommunities == index) &
                                    (self.flame_length != 0) &
                                    (self.canopy < self.community_table.ix[
                                        s.SUCCESSIONAL_GRASSLAND_ID].max_canopy)] = s.SUCCESSIONAL_GRASSLAND_ID

            # Retrogression shrub-swamp
            if index == s.SHRUB_SWAMP_ID:
                self.ecocommunities[(self.ecocommunities == index) &
                                    (self.flame_length != 0) &
                                    (self.canopy < self.community_table.ix[
                                        s.SHALLOW_EMERGENT_MARSH_ID].max_canopy)] = s.SHALLOW_EMERGENT_MARSH_ID

        # Reset forest age for grassland community types
        l = [s.SHALLOW_EMERGENT_MARSH_ID, s.SUCCESSIONAL_GRASSLAND_ID]
        for i in l:
            self.forest_age[(self.ecocommunities == i) & (self.flame_length != 0)] = 0

            # Reset dbh in cells that have been converted to grassland
            self.dbh[(self.ecocommunities == i) &
                     (self.forest_age == 0) &
                     (self.flame_length != 0)] = 0.5

        utils.array_to_raster(self.dbh, self.DBH_raster, geotransform=self.geot, projection=self.projection)

    def run_year(self):

        start_time = time.time()

        # s.logging.info('Year: %r' % self.year)

        # set weather and simulation duration
        self.set_climate_years()
        self.set_drought_years()
        self.select_climate_records()
        self.select_duration()
        self.write_wnd()
        self.shape = self.ecocommunities.shape

        # set tracking rasters
        self.set_time_since_disturbance()
        self.set_fuel_dbh()

        # increment time since disturbance tracking raster
        self.time_since_disturbance += 1

        initialize_time = time.time()
        s.logging.info('initialize run time: %s' % (initialize_time - start_time))

        # Check if trail fires escaped
        scaled_expected_trail_escape = s.EXPECTED_TRAIL_ESCAPE * self.upland_area
        s.logging.info('upland area: %s | scaled expected trail fire: %s'
                       % (self.upland_area, scaled_expected_trail_escape))

        number_of_trail_ignitions = np.random.poisson(lam=scaled_expected_trail_escape)

        if number_of_trail_ignitions > 0:

            # Get list of potential trail fire sites
            trail_array = utils.raster_to_array(self.TRAIL_raster)

            rows, cols = np.where((trail_array == s.TRAIL_ID) &
                                  (self.time_since_disturbance >= s.TRAIL_OVERGROWN_YRS) &
                                  (self.fuel != 14) &
                                  (self.fuel != 16) &
                                  (self.fuel != 98) &
                                  (self.fuel != 99))

            # Clear array from memory
            trail_array = None

            for row, col in zip(rows, cols):
                self.potential_trail_ignition_sites.append((row, col))

            # Select i sites from potential sites and appended to ignition_sites
            s.logging.info('potential trail fire sites: %s' % len(self.potential_garden_ignition_sites))
            if len(self.potential_trail_ignition_sites) > 0:
                for i in range(number_of_trail_ignitions):
                    self.ignition_sites.append(random.choice(self.potential_trail_ignition_sites))

        # Check if garden fires escaped
        number_of_garden_ignitions = np.random.poisson(lam=s.EXPECTED_GARDEN_ESCAPE)
        if number_of_garden_ignitions > 0:

            # Get list of potential garden fire sites
            if self.garden_disturbance is not None:
                rows, cols = np.where((self.ecocommunities == s.GARDEN_ID) &
                                      (self.garden_disturbance <= 1))

                for row, col in zip(rows, cols):
                    self.potential_garden_ignition_sites.append((row, col))

            # Select i sites from potential sites and appended to ignition_sites
            if len(self.potential_garden_ignition_sites) > 0:
                for i in range(number_of_garden_ignitions):
                    self.ignition_sites.append(random.choice(self.potential_garden_ignition_sites))

        # Check if hunting fires escaped
        number_of_hunting_ignitions = s.EXPECTED_HUNTING_ESCAPE #np.random.poisson(lam=s.EXPECTED_HUNTING_ESCAPE)
        if number_of_hunting_ignitions > 0:

            # Get list of potential hunting fire sites
            hunting_sites = utils.raster_to_array(self.HUNTING_raster)
            rows, cols = np.where((hunting_sites == s.HUNTING_SITE_ID) &
                                  (self.fuel != 14) &
                                  (self.fuel != 16) &
                                  (self.fuel != 98) &
                                  (self.fuel != 99))

            # clear array from memory
            hunting_sites = None

            for row, col in zip(rows, cols):
                self.potential_hunting_ignition_sites.append((row, col))

            # Select i sites from potential sites and appended to ignition_sites
            if len(self.potential_hunting_ignition_sites) > 0:
                for i in range(number_of_hunting_ignitions):
                    self.ignition_sites.append(random.choice(self.potential_hunting_ignition_sites))

        # Check if lightning fires
        scaled_expected_lightning_fire = s.EXPECTED_LIGHTNING_FIRE * self.upland_area
        s.logging.info('upland area: %s | scaled expected lightning fire: %s'
                       % (self.upland_area, scaled_expected_lightning_fire))
        number_of_lightning_ignitions = np.random.poisson(lam=scaled_expected_lightning_fire)
        if number_of_lightning_ignitions > 0:
            rows, cols = np.where(((self.fuel != 14) &
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
        s.logging.info('escaped hunting fires: %s' % number_of_hunting_ignitions)
        s.logging.info('lightning fires: %s' % number_of_lightning_ignitions)

        s.logging.info('ignition sites: %s' % self.ignition_sites)
        if len(self.ignition_sites) > 0:
            #
            # self.set_fuel()
            # print self.fuel.shape
            # down sample fuel and canopy for FARSITE
            utils.array_to_raster(self.fuel, os.path.join(s.TEMP_DIR, 'fuel.tif'),
                                  geotransform=self.geot, projection=self.projection)
            arcpy.env.cellSize = s.FARSITE_RESOLUTION

            fuel_temp = os.path.join(s.TEMP_DIR, "fuel_ds.tif")
            arcpy.Resample_management(os.path.join(s.TEMP_DIR, 'fuel.tif'), fuel_temp, s.FARSITE_RESOLUTION, "NEAREST")
            arcpy.RasterToASCII_conversion(fuel_temp, self.FUEL_ascii)

            # utils.array_to_ascii(self.CANOPY_ascii, self.canopy, self.header_text)
            canopy_temp = os.path.join(s.TEMP_DIR, "canopy_ds.tif")
            arcpy.Resample_management(self.CANOPY_raster, canopy_temp, s.FARSITE_RESOLUTION, "BILINEAR")
            arcpy.RasterToASCII_conversion(canopy_temp, self.CANOPY_ascii)

            # reset cell size
            arcpy.env.cellSize = s.CELL_SIZE

            # Write selected ignition sites to .shp file for FARSITE
            self.write_ignition()

            # Select equivalent climate year
            self.select_climate_records()
            # s.logging.info('Selected climate equivalent-year: %r' % self.equivalent_climate_year)

            # Save matching climate year wtr to input dir for FARSITE
            shutil.copyfile(os.path.join(self.INPUT_DIR, 'wtr', '%r.wtr' % self.equivalent_climate_year), self.WTR)

            # Create wind file
            self.write_wnd()

            # Run Farsite
            self.run_farsite()

            # Create flame length array
            if os.path.exists(self.FLAME_LENGTH_ascii):

                # rename farsite output .fml to .asc
                rename = os.path.join(self.BURN_RASTERS, '%s_farsite_output_fml.asc' % self.year)
                os.rename(self.FLAME_LENGTH_ascii, rename)
                self.FLAME_LENGTH_ascii = rename

                # resample and mask FARSITE flame length to env settings
                flame_length = os.path.join(self.OUTPUT_DIR, "%s_flame_length.tif" % self.year)
                arcpy.Resample_management(self.FLAME_LENGTH_ascii, flame_length, s.CELL_SIZE, "BILINEAR")
                flame_length_clip = arcpy.sa.ExtractByMask(flame_length, s.ecocommunities)
                flame_length_clip.save(flame_length)

                # read flame length as array
                self.flame_length = utils.raster_to_array(flame_length)
                self.flame_length[self.flame_length < 0] = 0
                self.area_burned = np.count_nonzero(self.flame_length)
                print('burned area', self.area_burned)
                if self.area_burned > 0:


                    # Update time since disturbance
                    self.time_since_disturbance[self.flame_length > 0] = 0

                    # Calculate tree mortality due to fire
                    time_s = time.time()
                    percent_mortality = self.tree_mortality
                    time_e = time.time()
                    s.logging.info('calculating tree mortality : %s' % (time_e - time_s))

                    # Update canopy based on percent mortality
                    self.canopy = np.where(self.flame_length != 0,
                                           np.array(self.canopy * percent_mortality, dtype=np.int8),
                                           self.canopy)

                    # Update communities based on burned canopy
                    time_s = time.time()
                    self.retrogression()
                    time_e = time.time()
                    s.logging.info('updated communities based on lost canopy : %s' % (time_e - time_s))


            self.get_memory()
            # s.logging.info('memory usage: %r Mb' % self.memory)


        s.logging.info('Area burned %r: %r acres' % (self.year, (self.area_burned * 100 * 0.000247105)))

        # Revise fuel model
        # time_s = time.time()
        # self.set_fuel()
        # time_e = time.time()
        # s.logging.info('updated fuel : %s' % (time_e - time_s))

        s.logging.info('saving arrays as ascii')
        time_s = time.time()
        utils.array_to_raster(self.canopy, self.CANOPY_raster,
                              geotransform=self.geot, projection=self.projection)
        utils.array_to_raster(self.forest_age, self.FOREST_AGE_raster,
                              geotransform=self.geot, projection=self.projection)
        utils.array_to_raster(self.time_since_disturbance, self.TIME_SINCE_DISTURBANCE_raster,
                              geotransform=self.geot, projection=self.projection)
        utils.array_to_raster(self.ecocommunities, os.path.join(self.OUTPUT_DIR, 'ecocommunities.tif'),
                              geotransform=self.geot, projection=self.projection)

        utils.array_to_raster(self.ecocommunities, os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year),
                              geotransform=self.geot, projection=self.projection)

        time_e = time.time()
        s.logging.info('saved arrays as rasters : %s' % (time_e - time_s))

        # Log FARSITE outputs when a fire occurs
        if self.area_burned > 0:
            shutil.copy(self.FUEL_ascii, os.path.join(self.OUTPUT_DIR, '%s_%s' % (self.year, 'fuel.asc')))
            for filename in os.listdir(self.INPUT_DIR):
                if fnmatch.fnmatch(filename, 'ignition.*'):
                    name, extension = os.path.splitext(filename)
                    shutil.copyfile(os.path.join(self.INPUT_DIR, filename),
                                    os.path.join(self.OUTPUT_DIR, "%s_ignition%s" % (self.year, extension)))

        shutil.copy(self.TIME_SINCE_DISTURBANCE_raster, os.path.join(self.OUTPUT_DIR, '%s_%s' %
                                                                     (self.year, 'time_since_disturbance.tif')))

        end_time = time.time()

        run_time = end_time - start_time

        s.logging.info('runtime: %s' % run_time)
