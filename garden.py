import os
import random
import logging
import arcpy
import settings as s
import disturbance as d
from utils import get_raster_area, smart_buffer

# TODO: Throughout the code, we had previously been leveraging in-memory raster processing,
#  to avoid expensive disk read/write operations. But with the lastest code and (exclusive use of)
#  arcpy 10.7x64, we get errors using *.afr intermediate files. Architecture should be refactored
#  to avoid disk access and be fast.

class GardenDisturbance(d.Disturbance):
    INPUT_DIR = os.path.join(s.INPUT_DIR, 'garden')
    OUTPUT_DIR = os.path.join(s.OUTPUT_DIR, 'garden')
    COMMUNITY_TABLE = s.COMMUNITY_TABLE
    SLOPE_SUITABILITY = s.slope_suitability
    PROXIMITY_SUITABILITY = s.proximity_suitability
    SITES = s.garden_sites

    def __init__(self, year):
        super(GardenDisturbance, self).__init__(year)

        self.temp_point_garden = os.path.join(s.TEMP_DIR, 'temp_point_garden.shp')
        self.temp_buffer = os.path.join(s.TEMP_DIR, 'temp_buffer.shp')
        self.site_populations = []
        self.coordinate_list = []
        self.garden_list = []
        self.new_garden = None
        self.eccommunities_suitability = None
        self.suitability = None
        self.population = None
        self.garden_area_target = None
        self.garden = None
        self.time_since_disturbance = None
        self.randrast = None
        self.site_center = None
        self.local_suitability = None
        self.local_ecocommunities = None
        self.garden_area = 0
        self.new_garden_area = 0

        self.set_time_since_disturbance()

    def set_time_since_disturbance(self):
        this_year_time_since_disturbance = os.path.join(self.OUTPUT_DIR,
                                                        'time_since_disturbance_%s.tif' % (self.year - 1))
        if os.path.isfile(this_year_time_since_disturbance):
            self.time_since_disturbance = arcpy.Raster(this_year_time_since_disturbance)
        else:
            # set initial time since disturbance
            self.time_since_disturbance = arcpy.sa.Con(self.ecocommunities, s.INITIAL_TIME_SINCE_DISTURBANCE)

    def calculate_suitability(self):
        """
        calculate land cover suitability using reclassification table, then sum
        land cover, proximity and slope suitability rasters for overall suitability score.
        :return:
        """
        ecocommunity_suitability = arcpy.sa.ReclassByTable(self.ecocommunities, self.COMMUNITY_TABLE,
                                                           from_value_field='Field1',
                                                           to_value_field='Field1',
                                                           output_value_field='garden_suitability',
                                                           missing_values='NODATA')

        self.suitability = arcpy.sa.Con(ecocommunity_suitability > 0, (ecocommunity_suitability +
                                                                       self.PROXIMITY_SUITABILITY +
                                                                       self.SLOPE_SUITABILITY))

        # if s.DEBUG_MODE:
        #     self.suitability.save(os.path.join(self.OUTPUT_DIR, 'suitability_%s.tif' % self.year))
        # del ecocommunity_suitability

    # def wipe_locks(self):
    #     path_suitability = os.path.join(self.OUTPUT_DIR, 'suitability_{}.tif'.format(self.year))
    #     path_local_suitability = os.path.join(self.OUTPUT_DIR, 'local_suitability.tif')
    #     path_garden = os.path.join(self.OUTPUT_DIR, 'garden_{}.tif'.format(self.year))
    #     if hasattr(self, 'suitability') and os.path.isfile(path_suitability):
    #         del self.suitability
    #         self.suitability = arcpy.Raster(path_suitability)
    #     if hasattr(self, 'local_suitability') and os.path.isfile(path_local_suitability):
    #         del self.local_suitability
    #         self.local_suitability = arcpy.Raster(path_local_suitability)
    #     if hasattr(self, 'garden') and os.path.isfile(path_garden):
    #         del self.garden
    #         self.garden = arcpy.Raster(path_garden)

    def population_to_garden_area(self):
        """
        calculate the area, in cells, needed to feed population at a given site
        :return:
        """

        var = random.choice(s.POPULATION_VARIATION)
        pop = self.population or 0
        self.garden_area_target = int((pop + var) * s.PER_CAPITA_GARDEN_AREA / (s.CELL_SIZE ** 2))

    def abandon_garden(self):
        """
        update communities based on age and current type
        :return:
        """

        # abandon garden if random value is below the abandonment probability
        if random.randint(0, 100) <= s.ABANDONMENT_PROBABILITY:
            logging.info('**************abandoning garden')
            local_communities = arcpy.sa.Con((self.ecocommunities == s.GARDEN_ID),
                                             s.SUCCESSIONAL_OLD_FIELD_ID,
                                             self.ecocommunities)

            # set environment extent and add the old field back to the community raster
            arcpy.env.extent = self.ecocommunities
            self.ecocommunities = arcpy.sa.Con(arcpy.sa.IsNull(local_communities) == 0, local_communities,
                                               self.ecocommunities)
            self.ecocommunities.save((os.path.join(s.OUTPUT_DIR, 'ecocommunities_%s.tif' % self.year)))

            # set extent back to local to proceed with rest of garden process
            arcpy.env.extent = self.temp_buffer
            del local_communities

    def set_local_extent(self):
        if arcpy.Exists(self.temp_point_garden):
            arcpy.Delete_management(self.temp_point_garden)
        arcpy.CopyFeatures_management(in_features=arcpy.PointGeometry(self.site_center),
                                      out_feature_class=self.temp_point_garden)

        if arcpy.Exists(self.temp_buffer):
            arcpy.Delete_management(self.temp_buffer)
        arcpy.Buffer_analysis(in_features=self.temp_point_garden,
                              out_feature_class=self.temp_buffer,
                              buffer_distance_or_field=s.PROXIMITY_BUFFER)

        arcpy.env.extent = self.temp_buffer

        # don't abandon gardens on first year of trial
        if self.year > min(s.RUN_LENGTH):
            self.abandon_garden()

        local_ecocommunities = arcpy.sa.ExtractByMask(self.ecocommunities, self.temp_buffer)
        if s.DEBUG_MODE:
            local_ecocommunities.save(os.path.join(s.TEMP_DIR, 'local_ecosystem.tif'))

        self.garden_area = get_raster_area(local_ecocommunities, s.GARDEN_ID)

        # self.wipe_locks()
        self.local_suitability = arcpy.sa.ExtractByMask(self.suitability, self.temp_buffer)
        self.local_suitability.save(os.path.join(s.TEMP_DIR, 'local_suitability.tif'))

        del local_ecocommunities

    def set_garden_center(self):
        """
        choose center cell for new garden, out of cells in proximity radius with the
        highest overall suitability. DEBUG mode saves out intermediate raster products
        :return:
        """

        # If the maximum suitability is no data or zero set to None
        if self.local_suitability.maximum is None or self.local_suitability.maximum == 0:
            self.garden = None

        # Else select random garden center out of cells with the highest suitability
        else:
            maxsuit = arcpy.sa.Con(self.local_suitability == self.local_suitability.maximum, self.local_suitability)
            # if s.DEBUG_MODE:
            maxsuit.save(os.path.join(s.TEMP_DIR, 'maxsuit.tif'))

            # Create random raster to associate with most suitable areas to randomly select garden centroid cell
            self.randrast = arcpy.sa.CreateRandomRaster(345, self.local_suitability, self.local_suitability)
            # if s.DEBUG_MODE:
            self.randrast.save(os.path.join(s.TEMP_DIR, 'randrast.tif'))

            randrastclip = arcpy.sa.Con(maxsuit, self.randrast)
            # if s.DEBUG_MODE:
            randrastclip.save(os.path.join(s.TEMP_DIR, 'randrastclip.tif'))

            # Select garden center using the maximum value in the random raster
            gardencenter = arcpy.sa.Con(randrastclip == randrastclip.maximum, s.GARDEN_ID)
            # if s.DEBUG_MODE:
            gardencenter.save(os.path.join(s.TEMP_DIR, 'gardencenter.tif'))

            self.garden = gardencenter
            del maxsuit, randrastclip, gardencenter

    def points_to_coordinates(self):
        """
        take points shp and convert to X Y coordinate tuples, this intermediate is needed to
        create pour points for the watershed tool.
        :return: coordinate_list
        """

        cursor = arcpy.da.SearchCursor(self.SITES, "SHAPE@XY")
        for point in cursor:
            self.coordinate_list.append((point[0][0], point[0][1]))
        # del cursor

    # def calculate_garden_area(self):
    #     time_since_disturbance = os.path.join(self.OUTPUT_DIR, 'time_since_disturbance_%s.tif' % self.year)
    #     field_names = ['VALUE', 'COUNT']
    #
    #     with arcpy.da.SearchCursor(time_since_disturbance, field_names=field_names) as sc:
    #         for row in sc:
    #             if row[0] == 1:
    #                 self.new_garden_area = row[1]
    #
    #     hist = d.hist(self.time_since_disturbance)
    #
    #     if 1 in hist:
    #         self.new_pond_area = hist[1]
    #     else:
    #         self.new_pond_area = 0

    def set_populations(self):
        point_cursor = arcpy.SearchCursor(self.SITES)
        for point in point_cursor:
            self.site_populations.append(point.getValue('population'))
        # del point_cursor

    def run_year(self):
        logging.info('starting garden disturbance for year: %s' % self.year)
        logging.info('garden {} is using ecocom: {} {}'.format(self.year,
                                                               self.ecocommunities,
                                                               type(self.ecocommunities)))

        self.calculate_suitability()
        self.points_to_coordinates()
        self.set_populations()

        logging.info('checking for existing gardens')
        for population, coordinates in zip(self.site_populations, self.coordinate_list):
            logging.info('garden coordinates: {} {}'.format(coordinates[0], coordinates[1]))
            self.site_center = arcpy.Point(coordinates[0], coordinates[1])
            self.population = population
            self.population_to_garden_area()

            self.set_local_extent()
            # check for gardens in area buffered around site (from set_local_extent)
            # if garden area of garden is 0 create new garden
            if self.garden_area == 0:
                arcpy.env.extent = self.temp_buffer
                self.set_garden_center()
                # Continue only if garden center has been assigned
                if self.garden is not None:
                    path_garden = os.path.join(self.OUTPUT_DIR, 'garden_{}.tif'.format(self.year))
                    self.garden, self.garden_area = smart_buffer(
                        self.garden,
                        s.GARDEN_ID,
                        self.local_suitability,
                        "garden",
                        self.garden_area,
                        self.garden_area_target,
                    )
                    self.garden.save(path_garden)
                    logging.info('finished create_garden: {}'.format(self.garden))
                    arcpy.env.extent = self.ecocommunities

                    # Return garden cells from self.garden else return existing communities
                    self.ecocommunities = arcpy.sa.Con(arcpy.sa.IsNull(self.garden) == 0, self.garden,
                                                       self.ecocommunities)

                    thisisabsurd = random.randint(0, 1000000)
                    fn = 'ecocommunities_{}_{}.tif'.format(self.year, thisisabsurd)
                    self.ecocommunities.save((os.path.join(s.TEMP_DIR, fn)))
                    logging.info('ecocommunities: {}'.format(self.ecocommunities))
                    e = arcpy.RasterToNumPyArray(self.ecocommunities)
                    self.canopy[e == s.GARDEN_ID | e == s.LENAPE_SITE_ID] = 0
                    self.forest_age[e == s.GARDEN_ID | e == s.LENAPE_SITE_ID] = 0
                    self.dbh[e == s.GARDEN_ID | e == s.LENAPE_SITE_ID] = 0
                    # self.dbh[(e == s.SUCCESSIONAL_OLD_FIELD_ID) & (self.forest_age == 0)] = 0.5

            arcpy.env.extent = self.ecocommunities

        self.ecocommunities.save((os.path.join(s.OUTPUT_DIR, 'ecocommunities_%s.tif' % self.year)))
        logging.info('ecocom after garden disturbance: {}'.format(self.ecocommunities))

        self.time_since_disturbance = arcpy.sa.Con(self.ecocommunities == s.GARDEN_ID, 0,
                                                   self.time_since_disturbance + 1)
        self.time_since_disturbance.save(os.path.join(self.OUTPUT_DIR, 'time_since_disturbance_%s.tif' % self.year))

        canopy = arcpy.NumPyArrayToRaster(self.canopy,
                                          arcpy.Point(arcpy.env.extent.XMin, arcpy.env.extent.YMin),
                                          x_cell_size=s.CELL_SIZE,
                                          y_cell_size=s.CELL_SIZE)
        canopy.save(s.CANOPY)
        forestage = arcpy.NumPyArrayToRaster(self.forest_age,
                                             arcpy.Point(arcpy.env.extent.XMin, arcpy.env.extent.YMin),
                                             x_cell_size=s.CELL_SIZE,
                                             y_cell_size=s.CELL_SIZE)
        forestage.save(s.FOREST_AGE)
        dbh = arcpy.NumPyArrayToRaster(self.dbh,
                                       arcpy.Point(arcpy.env.extent.XMin, arcpy.env.extent.YMin),
                                       x_cell_size=s.CELL_SIZE,
                                       y_cell_size=s.CELL_SIZE)
        dbh.save(s.DBH)

        logging.info('garden area: %s' % self.garden_area)
        self.ecocommunities = None
        del self.ecocommunities
