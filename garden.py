import os


class GardenDisturbance():
    # CLASS VARIABLES
    year = None
    ecocommunities = None

    # PRIVATE VARIABLES

    # CONSTANTS
    CENTROID = 10000
    PER_CAPITA_GARDEN_AREA = 1

    TIME_TO_ABANDON = 20  # abandon a garden after 20 years.
    SHRUB_SUCCESSION = 36  # after 36 years abandoned garden turns to successional shrubland.
    FOREST_SUCCESSION = 80

    GARDEN_ID = 650  # ecosystem id for gardens (will look for this value when processing raster.
    OLD_FIELD_ID = 648  # ecosystem id for abandoned fields.
    SHRUBLAND_ID = 649

    # Garden Directories
    INPUT_DIR = os.path.join(s.INPUT_DIR, 'garden')
    OUTPUT_DIR = os.path.join(s.OUTPUT_DIR, 'garden')

    # Constant Inputs
    CLIMAX_COMMUNITIES = ''
    SLOPE_SUITABILITY = ''
    PROXIMITY_SUITABILITY = ''
    COMMUNITY_RECLASS_TABLE = ''

    def __init__(self):

        self.eccommunities_suitability = None
        self.slope_suitability = None
        self.proximity_suitability = None
        self.suitability = None
        self.population = None
        self.garden_area = 0
        self.garden_area_target = None
        self.ecocommunities = None
        self.forest_age = None
        self.garden_list = []
        self.garden = None
        self.time_since_disturbance = None

    def set_eccommunities(self):
        """

        :return:
        """

        self.ecocommunities = None

    def set_time_since_disturbance(self):
        """

        :return:
        """

        self.time_since_disturbance = None

    def calculate_suitability(self):
        """
        calculate land cover suitability using reclassification table, then sum
        land cover, proximity and slope suitability rasters for overall suitability score.
        :return:
        """

        ecocommunity_suitability = None # reclassify ecocommunities
        self.suitability = arcpy.sa.Con(ecocommunity_suitability > 0, (ecocommunity_suitablity +
                                                                       self.proximity_suitability +
                                                                       self.slope_suitability),
                                                                       arcpy.sa.SetNull)

    def population_to_garden_area(self):
        """
        calculate the area, in cells, needed to feed population at a given site
        :return:
        """
        self.garden_area_target = self.population * self.PER_CAPITA_GARDEN_AREA

    def succession(self):
        """
        update communities based on age and current type
        :return:
        """

        self.ecocommunities = arcpy.sa.Con((self.ecocommunities == self.GARDEN_ID) &
                                           (self.time_since_disturbance > self.TIME_TO_ABANDON), self.OLD_FIELD_ID,
                                           arcpy.sa.Con((self.ecocommunities == self.OLD_FIELD_ID) &
                                                        (self.time_since_disturbance > self.SHRUB_SUCCESSION),
                                                        self.SHRUBLAND_ID,
                                                        arcpy.sa.Con((self.ecocommunities == self.FOREST_SUCCESSION) &
                                                                     (
                                                                     self.time_since_disturbance > self.FOREST_SUCCESSION),
                                                                     self.CLIMAX_COMMUNITIES,
                                                                     self.ecocommunities)))

        # update age
    def create_buffer(self):
        """
        create a X meter buffer around site center point. clip ecocommunity and suitability rasters to extent
        :return:
        """

    def get_garden_area(self):
        """
        return count of garden cells in community raster
        :return:
        """

        ecocommunities_cursor = arcpy.SearchCursor(self.ecocommunities)
        print"Checking if a garden exists..."
        for row in ecocommunities_cursor:
            if row.getValue('VALUE') == self.GARDEN_ID:
                self.garden_area = row.getValue('VALUE')


    def set_garden_center(self):
        """
        choose center cell for new garden, out of cells in proximity radius with the
        highest overall suitability.
        :return:
        """

        potential_center_cells = self.suitability # find cells with highest suitability values

        #  generate a single random point in the center of a potential_center_cell
        #  point to raster
        #  where cells are null return 0

        self.garden = None # raster with one cell == GARDEN_ID else 0

    def create_garden(self):
        """
        create a new garden
        :return:
        """

        self.calculate_suitability()

        self.get_garden_area()

        # Grow garden iteratively until threshold is reached
        while self.garden_area < self.garden_area_target:

            # Calculate the suitability surface for garden development
            last_area = self.garden_area

            self.set_garden_center()

            # Expand potential garden grid by one cell
            zone = arcpy.sa.Expand(self.garden, 1, [self.GARDEN_ID])

            # where zone cells are coincident with unsuitable cells set null

            # calculate focal mean suitability values, within a rectangular 3x3 window
            mean_suitability = arcpy.sa.FocalStatistics(suitability, "#", "MEAN", "#")

            # Find maximum mean suitability value in zone
            zone_max = arcpy.sa.ZonalStatistics(clip, "VALUE", mean_suitability, "MEAN", "#")

            # Expand garden to the most suitable locations
            garden = arcpy.sa.Con(zero == elf.GARDEN_ID, self.GARDEN_ID,
                                  arcpy.sa.Con(mean_suitability >= zone_max, self.GARDEN_ID, self.ecocommunities))

            garcounter.save('garcounter%s.tif' % counter)

            # re-count number of garden cells
            self.get_garden_area()

            # Break if garden stops expanding before reaching required size
            if last_area == self.garden_area:
                break

            gardenexists = 1

        print "This garden is done at %d cells!" % currentsize

        gardens = garcounter

        garcounter_nonull = arcpy.sa.Con(IsNull(garcounter), 0, garcounter)
        lc1 = arcpy.sa.Con(garcounter_nonull == 10000, 650, lc)
        age1 = arcpy.sa.Con(garcounter_nonull == 10000, 0, age)
        lc = lc1

        age = age1

    def run_year(self):
        """

        :return:
        """
