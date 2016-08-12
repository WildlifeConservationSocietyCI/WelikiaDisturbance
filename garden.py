import os
import settings as s
import disturbance as d
import arcpy
import numpy
import random



class GardenDisturbance(d.Disturbance):
    # CLASS VARIABLES

    # Garden Directories
    INPUT_DIR = os.path.join(s.INPUT_DIR, 'garden')
    OUTPUT_DIR = os.path.join(s.OUTPUT_DIR, 'garden')
    SPATIAL = 'spatial'
    TABULAR = 'tabular'

    # Constant Inputs
    CLIMAX_COMMUNITIES = s.ecocommunities
    SLOPE_SUITABILITY = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'slope_suitability.tif')
    PROXIMITY_SUITABILITY = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'proximity_suitability.tif')
    COMMUNITY_RECLASS_TABLE = os.path.join(INPUT_DIR, TABULAR, 'lc_reclass.txt')
    SITES = os.path.join(INPUT_DIR, SPATIAL, s.REGION, 'garden_sites.shp')

    def __init__(self, year):
        super(GardenDisturbance, self).__init__(year)

        self.site_populations = []
        self.coordinate_list = []

        self.new_garden = None
        self.year = year
        self.eccommunities_suitability = None
        self.suitability = None
        self.population = None
        self.garden_area = 0
        self.garden_area_target = None
        self.garden_list = []
        self.garden = None
        self.time_since_disturbance = None
        self.randrast = None
        self.site_center = None
        self.temp_point = os.path.join(s.TEMP_DIR, 'temp_point.shp')
        self.temp_buffer = os.path.join(s.TEMP_DIR, 'temp_buffer.shp')
        self.local_suitability = None
        self.local_ecocommunities = None
        self.new_garden_area = 0

        self.set_time_since_disturbance()

    def set_time_since_disturbance(self):
        """

        :return:

        """
        this_year_time_since_disturbance = os.path.join(self.OUTPUT_DIR,
                                                        'time_since_disturbance_%s.tif' % (self.year - 1))
        if os.path.isfile(this_year_time_since_disturbance):
            self.time_since_disturbance = arcpy.Raster(this_year_time_since_disturbance)
            # print this_year_time_since_disturbance, type(self.time_since_disturbance)
        else:
            # set initial time since disturbance
            self.time_since_disturbance = arcpy.sa.Con(arcpy.Raster(s.ecocommunities), 20)

    def calculate_suitability(self):
        """
        calculate land cover suitability using reclassification table, then sum
        land cover, proximity and slope suitability rasters for overall suitability score.
        :return:
        """
        ecocommunity_suitability = arcpy.sa.ReclassByTable(self.ecocommunities, self.COMMUNITY_RECLASS_TABLE,
                                                           from_value_field='Field1',
                                                           to_value_field='Field1',
                                                           output_value_field='Field3',
                                                           missing_values='NODATA')

        self.suitability = arcpy.sa.Con(ecocommunity_suitability > 0, (ecocommunity_suitability +
                                                                       self.PROXIMITY_SUITABILITY +
                                                                       self.SLOPE_SUITABILITY))

        self.suitability.save(os.path.join(self.OUTPUT_DIR, 'suitability_%s.tif' % self.year))

    def population_to_garden_area(self):
        """
        calculate the area, in cells, needed to feed population at a given site
        :return:
        """

        x = random.choice(s.REQUIREMENT_VARIANCE)
        self.garden_area_target = int(self.population * s.PER_CAPITA_GARDEN_AREA / (s.CELL_SIZE ** 2)) + x

    def abandon_garden(self):
        """
        update communities based on age and current type
        :return:
        """

        # abandon garden if random value is below the abandoment probability
        if random.randint(0, 100) <= s.ABANDONMENT_PROBABILITY:
            print '**************abandoning garden'
            local_communities = arcpy.sa.Con((self.ecocommunities == s.GARDEN_ID),
                                             s.SUCCESSIONAL_OLD_FIELD_ID,
                                             self.ecocommunities)

            # set environment extent and add the old field back to the community raster
            arcpy.env.extent = s.ecocommunities

            self.ecocommunities = arcpy.sa.Con(arcpy.sa.IsNull(local_communities) == 0, local_communities,
                                               self.ecocommunities)

            # set local exent for garden creation
            arcpy.env.extent = self.temp_buffer

    def update_time_since_disturbance(self):
        """

        :return:
        """
        self.time_since_disturbance = arcpy.sa.Con(self.new_garden == s.GARDEN_ID, 1, self.time_since_disturbance)

    def get_garden_area(self, in_raster):
        """
        return count of garden cells in community raster
        :return:
        """
        count = 0
        hist = d.hist(in_raster)
        if s.GARDEN_ID in hist:
            count = hist[s.GARDEN_ID]

        return count

    def set_local_extent(self):
        """

        :return:
        """
        if arcpy.Exists(self.temp_point):
            arcpy.Delete_management(self.temp_point)

        arcpy.CopyFeatures_management(in_features=arcpy.PointGeometry(self.site_center),
                                      out_feature_class=self.temp_point)

        if arcpy.Exists(self.temp_buffer):
            arcpy.Delete_management(self.temp_buffer)

        arcpy.Buffer_analysis(in_features=self.temp_point,
                              out_feature_class=self.temp_buffer,
                              buffer_distance_or_field=500)

        arcpy.env.extent = self.temp_buffer

        # don't abandon gardens on first year of trial
        if self.year > min(s.RUN_LENGTH):
            self.abandon_garden()

        local_ecocommunities = arcpy.sa.ExtractByMask(self.ecocommunities, self.temp_buffer)

        if s.DEBUG_MODE:
            local_ecocommunities.save(os.path.join(self.OUTPUT_DIR, 'local_ecosystem.tif'))

        self.garden_area = self.get_garden_area(local_ecocommunities)

        print self.garden_area
        self.local_suitability = arcpy.sa.ExtractByMask(self.suitability, self.temp_buffer)

        if s.DEBUG_MODE:
            self.local_suitability.save(os.path.join(self.OUTPUT_DIR, 'local_suitability.tif'))

    def set_garden_center(self):
        """
        choose center cell for new garden, out of cells in proximity radius with the
        highest overall suitability.
        :return:
        """

        maxsuit = arcpy.sa.Con(self.local_suitability == self.local_suitability.maximum, self.local_suitability)

        if s.DEBUG_MODE:
            maxsuit.save(os.path.join(self.OUTPUT_DIR, 'maxsuit.tif'))

        # Create random raster to associate with most suitable areas to randomly select garden centroid cell
        self.randrast = arcpy.sa.CreateRandomRaster(345, self.local_suitability, self.local_suitability)

        if s.DEBUG_MODE:
            self.randrast.save(os.path.join(self.OUTPUT_DIR, 'randrast.tif'))

        randrastclip = arcpy.sa.Con(maxsuit, self.randrast)

        if s.DEBUG_MODE:
            randrastclip.save(os.path.join(self.OUTPUT_DIR, 'randrastclip.tif'))

        # print "selecting garden center"
        gardencenter = arcpy.sa.Con(randrastclip == randrastclip.maximum, s.GARDEN_ID)

        if s.DEBUG_MODE:
            gardencenter.save(os.path.join(self.OUTPUT_DIR, 'gardencenter.tif'))

        self.garden = gardencenter

    def points_to_coordinates(self):
        """
        take points shp and convert to X Y coordinate tuples, this intermediate is needed to
        create pour points for the watershed tool.
        :return: coordinate_list
        """

        cursor = arcpy.da.SearchCursor(self.SITES, "SHAPE@XY")

        for point in cursor:
            self.coordinate_list.append((point[0][0], point[0][1]))

    def create_garden(self):
        """
        create a new garden
        :return:
        """
        if s.DEBUG_MODE:
            counter = 0

        while self.garden_area < self.garden_area_target:
            # print 'garden area: %s' % self.garden_area

            # Set nodata values in garden grid to 0
            zero = arcpy.sa.Con(arcpy.sa.IsNull(self.garden) == 1, 0, self.garden)
            if s.DEBUG_MODE:
                zero.save(os.path.join(self.OUTPUT_DIR, "zero_%s.tif" % counter))

            # Create another grid where current garden is NODATA and all other values = 0
            nullgard = arcpy.sa.SetNull(zero == s.GARDEN_ID, 0)
            if s.DEBUG_MODE:
                nullgard.save(os.path.join(self.OUTPUT_DIR, "nullgard_%s.tif" % counter))

            # Expand potential garden grid by one cell
            zone = arcpy.sa.Expand(self.garden, 1, s.GARDEN_ID)
            if s.DEBUG_MODE:
                zone.save(os.path.join(self.OUTPUT_DIR, "zone_%s.tif" % counter))

            # Create a clipping raster for gardens
            zapped = arcpy.sa.Plus(nullgard, self.local_suitability)
            if s.DEBUG_MODE:
                zapped.save(os.path.join(self.OUTPUT_DIR, "zapped_%s.tif" % counter))

            # Clip expanded garden grid by removing unsuitable areas and places where garden currently exists
            #  "NODATA"

            clip = arcpy.sa.ExtractByMask(zone, zapped)
            array = arcpy.RasterToNumPyArray(clip)
            unique_values = numpy.unique(array, return_counts=True)
            value_dict = dict(zip(unique_values[0], unique_values[1]))
            if s.GARDEN_ID not in value_dict.keys():
                print 'no new cells can be added'
                break

            if s.DEBUG_MODE:
                clip.save(os.path.join(self.OUTPUT_DIR, 'clip_%s.tif' % counter))

            ring_suitability = arcpy.sa.Con(clip, self.local_suitability)
            if s.DEBUG_MODE:
                ring_suitability.save(os.path.join(self.OUTPUT_DIR, 'ring_suitability_%s.tif' % counter))

            new_cells = arcpy.sa.Con(ring_suitability == ring_suitability.maximum, s.GARDEN_ID)
            if s.DEBUG_MODE:
                new_cells.save(os.path.join(self.OUTPUT_DIR, 'new_cells_%s.tif' % counter))

            new_cells_area = self.get_garden_area(new_cells)

            if (new_cells_area + self.garden_area) <= self.garden_area_target:
                self.garden = arcpy.sa.Con(zero == s.GARDEN_ID, s.GARDEN_ID,
                                           arcpy.sa.Con(new_cells == s.GARDEN_ID, s.GARDEN_ID, self.garden))

            else:
                random_cells = arcpy.sa.Con(new_cells, self.randrast)

                # print type(random_cells)
                array = arcpy.RasterToNumPyArray(random_cells)
                random_values = numpy.unique(array).tolist()

                random.shuffle(random_values)

                while self.garden_area < self.garden_area_target:
                    # print 'garden area: %s' % self.garden_area

                    r = random_values.pop()

                    new_cell = arcpy.sa.Con(random_cells == r, s.GARDEN_ID)

                    self.garden = arcpy.sa.Con(arcpy.sa.IsNull(new_cell) == 0, new_cell, self.garden)

                    if s.DEBUG_MODE:
                        self.garden.save(os.path.join(self.OUTPUT_DIR, 'garden_%s.tif' % counter))

                    self.garden_area = self.get_garden_area(self.garden)
                    if s.DEBUG_MODE:
                        new_cell.save(os.path.join(self.OUTPUT_DIR, 'new_cell_%s.tif' % counter))

            self.garden_area = self.get_garden_area(self.garden)

    def calculate_garden_area(self):

        time_since_disturbance = os.path.join(self.OUTPUT_DIR, 'time_since_disturbance_%s.tif' % self.year)
        field_names = ['VALUE', 'COUNT']

        with arcpy.da.SearchCursor(time_since_disturbance, field_names=field_names) as sc:
            for row in sc:
                if row[0] == 1:
                    self.new_garden_area = row[1]

    def set_populations(self):
        """

        :return:
        """
        point_cursor = arcpy.SearchCursor(self.SITES)

        for point in point_cursor:
            self.site_populations.append(point.getValue('population'))

    def run_year(self):
        """

        :return:
        """
        s.logging.info('starting garden disturbance for year: %s' % self.year)

        self.calculate_suitability()

        self.points_to_coordinates()

        self.set_populations()

        self.time_since_disturbance = arcpy.sa.Con(self.time_since_disturbance, self.time_since_disturbance + 1)

        # self.succession()

        s.logging.info('checking for existing gardens')
        for population, coordinates in zip(self.site_populations, self.coordinate_list):
            # print population, coordinates

            self.population = population
            self.population_to_garden_area()

            print coordinates[0], coordinates[1]
            self.site_center = arcpy.Point(coordinates[0], coordinates[1])

            self.set_local_extent()
            # check for gardens in area buffered around site

            # self.succession()

            if self.garden_area == 0:

                self.set_garden_center()

                self.create_garden()

                arcpy.env.extent = s.ecocommunities

                # self.garden.save(os.path.join(self.OUTPUT_DIR, 'garden.tif'))

                if self.garden is not None:
                    self.garden = arcpy.sa.Plus(self.garden, 0)
                    self.ecocommunities = arcpy.sa.Con(arcpy.sa.IsNull(self.garden) == 0, self.garden,
                                                       self.ecocommunities)

                    e = arcpy.RasterToNumPyArray(self.ecocommunities)
                    self.canopy[e == s.GARDEN_ID] = 0
                    self.forest_age[e == s.GARDEN_ID] = 0

                    if self.year == s.RUN_LENGTH[0]:
                        random_age = numpy.random.random_integers(1, 19)
                        self.time_since_disturbance = arcpy.sa.Con(arcpy.sa.IsNull(self.garden) == 0, random_age,
                                                                   self.time_since_disturbance)
                    else:
                        self.time_since_disturbance = arcpy.sa.Con(arcpy.sa.IsNull(self.garden) == 0, 1,
                                                                   self.time_since_disturbance)

            arcpy.env.extent = s.ecocommunities

        if arcpy.Exists((os.path.join(s.OUTPUT_DIR, 'ecocommunities_%s.tif' % self.year))):
            arcpy.Delete_management((os.path.join(s.OUTPUT_DIR, 'ecocommunities_%s.tif' % self.year)))

        # print type(self.ecocommunities)
        self.ecocommunities.save((os.path.join(s.OUTPUT_DIR, 'ecocommunities_%s.tif' % self.year)))

        self.time_since_disturbance.save(os.path.join(self.OUTPUT_DIR, 'time_since_disturbance_%s.tif' % self.year))
        self.array_to_ascii(array=self.canopy, out_ascii_path=self.CANOPY_ascii)
        self.array_to_ascii(array=self.forest_age, out_ascii_path=self.FOREST_AGE_ascii)
        self.calculate_garden_area()
        print 'garden area: %s' % self.new_garden_area