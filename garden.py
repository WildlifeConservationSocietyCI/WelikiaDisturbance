import os
import settings as s
import arcpy


class GardenDisturbance():
    # CLASS VARIABLES
    year = None
    ecocommunities = None

    # PRIVATE VARIABLES
    _ecocommunities_filename = 'ecocommunities_%s.tif'

    # Garden Directories
    INPUT_DIR = os.path.join(s.INPUT_DIR, 'garden')
    OUTPUT_DIR = os.path.join(s.OUTPUT_DIR, 'garden')

    # Constant Inputs
    CLIMAX_COMMUNITIES = ''
    SLOPE_SUITABILITY = os.path.join(INPUT_DIR, 'slope_suitability.tif')
    PROXIMITY_SUITABILITY = os.path.join(INPUT_DIR, 'proximity_suitability.tif')
    COMMUNITY_RECLASS_TABLE = os.path.join(INPUT_DIR, 'lc_reclass2.csv')
    SITES = os.path.join(INPUT_DIR, 'garden_sites.shp')

    def __init__(self, year):

        self.coordinate_list = []
        self.temp_point = os.path.join(s.TEMP_DIR, 'temp_point.shp')
        self.temp_buffer = os.path.join(s.TEMP_DIR, 'temp_buffer.shp')
        self.new_garden = None
        self.year = year
        self.eccommunities_suitability = None
        self.suitability = None
        self.population = None
        self.garden_area = 0
        self.garden_area_target = None
        self.ecocommunities = None
        self.forest_age = None
        self.garden_list = []
        self.garden = None
        self.time_since_disturbance = None

        self.set_ecocommunities()

    def set_ecocommunities(self):
        """

        :return:
        """

        this_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year)
        last_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % (self.year - 1))

        if os.path.isfile(this_year_ecocomms):
            print this_year_ecocomms
            self.ecocommunities = arcpy.Raster(this_year_ecocomms)
        elif os.path.isfile(last_year_ecocomms):
            print last_year_ecocomms
            self.ecocommunities = arcpy.Raster(last_year_ecocomms)
        else:
            print 'initial run'
            self.ecocommunities = arcpy.Raster(s.ecocommunities)

    def set_time_since_disturbance(self):
        """

        :return:

        """
        this_year_time_since_disturbance = os.path.join(self.OUTPUT_DIR,
                                                        'time_since_disturbance_%s.tif' % (self.year - 1))
        if os.path.isfile(this_year_time_since_disturbance):
            self.time_since_disturbance = arcpy.Raster(this_year_time_since_disturbance)
            print this_year_time_since_disturbance, type(self.time_since_disturbance)
        else:
            # set initial time since disturbance
            self.time_since_disturbance = arcpy.sa.Con(arcpy.Raster(s.ecocommunities), 20)
            self.time_since_disturbance.save(os.path.join(self.OUTPUT_DIR,
                                                          'time_since_disturbance_%s.tif' % self.year))

    def calculate_suitability(self):
        """
        calculate land cover suitability using reclassification table, then sum
        land cover, proximity and slope suitability rasters for overall suitability score.
        :return:
        """

        ecocommunity_suitability = arcpy.sa.ReclassByTable(self.ecocommunities, self.COMMUNITY_RECLASS_TABLE,
                                                           from_value_field='Field1',
                                                           to_value_field='Field2',
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
        self.garden_area_target = self.population * s.PER_CAPITA_GARDEN_AREA

    def succession(self):
        """
        update communities based on age and current type
        :return:
        """

        self.ecocommunities = arcpy.sa.Con((self.ecocommunities == s.GARDEN_ID) &
                                           (self.time_since_disturbance > s.TIME_TO_ABANDON), s.OLD_FIELD_ID,
                                           arcpy.sa.Con((self.ecocommunities == s.OLD_FIELD_ID) &
                                                        (self.time_since_disturbance > s.SHRUB_SUCCESSION),
                                                        s.SHRUBLAND_ID,
                                                        arcpy.sa.Con((self.ecocommunities == s.FOREST_SUCCESSION) &
                                                                     (
                                                                         self.time_since_disturbance >
                                                                         s.FOREST_SUCCESSION),
                                                                     self.CLIMAX_COMMUNITIES,
                                                                     self.ecocommunities)))

        # update age

    def update_time_since_disturbance(self):
        """

        :return:
        """
        self.time_since_disturbance = arcpy.sa.Con(self.new_garden == s.GARDEN_ID, 1, self.time_since_disturbance)

    def create_buffer(self):
        """
        create a X meter buffer around site center point. clip ecocommunity and suitability rasters to extent
        :return:
        """

    def get_garden_area(self, in_raster):
        """
        return count of garden cells in community raster
        :return:
        """
        cursor = arcpy.SearchCursor(in_raster)
        # cursor = arcpy.SearchCursor(os.path.join(self.OUTPUT_DIR, 'garden.tif'))

        # print"Checking if a garden exists..."
        for row in cursor:
            if row.getValue('VALUE') == s.GARDEN_ID:
                self.garden_area = row.getValue('Count')

    def set_garden_center(self):
        """
        choose center cell for new garden, out of cells in proximity radius with the
        highest overall suitability.
        :return:
        """
        #
        # value = arcpy.sa.Lookup(in_raster=self.suitability,
        #               lookup_field="Value")
        #
        # # find cells with highest suitability values
        # potential_center_cells = arcpy.sa.ZonalStatistics(in_zone_data=self.temp_buffer,
        #                                                   zone_field='Value',
        #                                                   in_value_raster=self.suitability,
        #                                                   statistics_type='MAXIMUM')

        # potential_center_cells.save(os.path.join(self.OUTPUT_DIR, 'start_cells.tif'))
        #  generate a single random point in the center of a potential_center_cell
        #  point to raster
        #  where cells are null return 0

        # self.garden = None  # raster with one cell == GARDEN_ID else 0

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

        # self.calculate_suitability()
        self.points_to_coordinates()

        print self.coordinate_list

        site_zone = None
        point_cursor = arcpy.SearchCursor(self.SITES)
        populations = []
        for point in point_cursor:
            populations.append(point.getValue('population'))

        print populations

        for population, coordinates in zip(populations, self.coordinate_list)[:1]:
            print population, coordinates

            self.population = population

            site_center = arcpy.Point(coordinates[0], coordinates[1])

            arcpy.CopyFeatures_management(in_features=arcpy.PointGeometry(site_center),
                                          out_feature_class=self.temp_point)

            if arcpy.Exists(self.temp_buffer):
                arcpy.Delete_management(self.temp_buffer)
            #
            arcpy.Buffer_analysis(in_features=self.temp_point,
                                  out_feature_class=self.temp_buffer,
                                  buffer_distance_or_field=500)

            ecocommunities = arcpy.sa.ExtractByMask(self.ecocommunities, self.temp_buffer)
            self.get_garden_area(ecocommunities)
            print self.garden_area

            local_suitability = arcpy.sa.ExtractByMask(self.suitability, self.temp_buffer)

            arcpy.env.extent = self.temp_buffer

            if self.garden_area == 0:

                # Find most suitable areas for garden
                maxsuit = arcpy.sa.Con(local_suitability == local_suitability.maximum, local_suitability)
                maxsuit.save(os.path.join(self.OUTPUT_DIR, 'maxsuit.tif'))

                # Create random raster to associate with most suitable areas to randomly select garden centroid cell
                # TODO: Exclude already gardened cells from suitable areas (so centroid should be well outside garden)
                randrast = arcpy.sa.CreateRandomRaster(345, local_suitability, local_suitability)
                randrast.save(os.path.join(self.OUTPUT_DIR, 'randrast.tif'))
                randrastclip = arcpy.sa.Con(maxsuit, randrast)
                randrastclip.save(os.path.join(self.OUTPUT_DIR, 'randrastclip.tif'))
                print "Selecting random starting place..."
                gardencenter = arcpy.sa.Con(randrastclip == randrastclip.maximum, s.GARDEN_ID)
                gardencenter.save(os.path.join(self.OUTPUT_DIR, 'gardencenter.tif'))

                self.garden = gardencenter

                self.population_to_garden_area()

                counter = 0
                while self.garden_area < self.garden_area_target:
                    print 'garden area: %s' % self.garden_area

                    lastsize = self.garden_area

                    # Set nodata values in garden grid to 0
                    zero = arcpy.sa.Con(arcpy.sa.IsNull(self.garden) == 1, 0, self.garden)
                    zero.save(os.path.join(self.OUTPUT_DIR, "zero_%s.tif" % counter))

                    # Create another grid where current garden is NODATA and all other values = 0
                    nullgard = arcpy.sa.SetNull(zero == s.GARDEN_ID, 0)
                    nullgard.save(os.path.join(self.OUTPUT_DIR, "nullgard_%s.tif" % counter))

                    # Expand potential garden grid by one cell
                    zone = arcpy.sa.Expand(self.garden, 1, s.GARDEN_ID)
                    zone.save(os.path.join(self.OUTPUT_DIR, "zone_%s.tif" % counter))

                    # Create a clipping raster for gardens
                    zapped = arcpy.sa.Plus(nullgard, local_suitability)
                    zapped.save(os.path.join(self.OUTPUT_DIR, "zapped_%s.tif" % counter))

                    # Clip expanded garden grid by removing unsuitable areas and places where garden currently exists "NODATA"
                    clip = arcpy.sa.ExtractByMask(zone, zapped)
                    clip.save(os.path.join(self.OUTPUT_DIR, 'clip_%s.tif' % counter))

                    ring_suitability = arcpy.sa.Con(clip, local_suitability)
                    ring_suitability.save(os.path.join(self.OUTPUT_DIR, 'ring_suitability_%s.tif' % counter))

                    new_cells = arcpy.sa.Con(ring_suitability == ring_suitability.maximum, s.GARDEN_ID)
                    new_cells.save(os.path.join(self.OUTPUT_DIR, 'new_cells_%s.tif' % counter))

                    random_cells = arcpy.sa.Con(new_cells, randrast)
                    random_cells.save(os.path.join(self.OUTPUT_DIR, 'random_cells_%s.tif' % counter))

                    new_cell = arcpy.sa.Con(random_cells == random_cells.maximum, s.GARDEN_ID)
                    new_cell.save(os.path.join(self.OUTPUT_DIR, 'new_cell_%s.tif' % counter))

                    # # Find focal mean suitability values, to smooth them assumes a 3x3 window (default of second arg in function below)
                    # mean_suitability = arcpy.sa.FocalStatistics(local_suitability, "#", "MEAN", "#")
                    # mean_suitability.save(os.path.join(self.OUTPUT_DIR, 'mean_suitability_%s.tif'))
                    #
                    # # Find maximum focal suitability value in zone
                    # ring_max = arcpy.sa.ZonalStatistics(clip, "VALUE", mean_suitability, "MEAN", "#")
                    # ring_max.save(os.path.join(self.OUTPUT_DIR, 'ring_max_%s.tif'))
                    # # Expand garden to the most suitable locations
                    #
                    self.garden = arcpy.sa.Con(zero == s.GARDEN_ID, s.GARDEN_ID,
                                               arcpy.sa.Con(new_cell == s.GARDEN_ID, s.GARDEN_ID, self.garden))

                    counter += 1
                    self.get_garden_area(self.garden)

                self.garden.save(os.path.join(self.OUTPUT_DIR, 'garden.tif'))

                self.ecocommunities = (self.garden == s.GARDEN_ID, self.garden, self.ecocommunities)

            self.ecocommunities.save((os.path.join(self.OUTPUT_DIR, 'ecocommunities_%s.tif' % self.year)))
                
                    # garcounter: raster showing garden extent at each loop
                    # garcounter should be 1 cell = 10000 (from gardencenter)
                    # garcounter = arcpy.sa.SetNull(garcounter, garcounter, garcounter == 10000)
                    # garcounter = arcpy.sa.Con(null == 1, gardencenter, null)
                    # #TODO: look into refactoring garcounter and other rasters to have no NoData cells
                    # garcounter = gardencenter
                    # #garcounter = arcpy.sa.SetNull(gardencenter, gardencenter, 'VALUE = %s' % CENTROID)
                    # garcounter.save("garcounter.tif")
                    #
                    #
                    #
                    # # Grow garden iteratively until threshold is reached
                    # while currentsize < patchsize:
                    #
                    #     lastsize = currentsize
                    #
                    #
                    #     # Set nodata values in garden grid to 0
                    #     zerocounter = arcpy.sa.Con(IsNull(garcounter), 0, garcounter)
                    #     zerocounter.save("zerocounter%s.tif" % counter)
                    #
                    #     # Create another grid where current garden is NODATA and all other values = 0
                    #     nullgard = arcpy.sa.SetNull(zerocounter == CENTROID, 0)
                    #     nullgard.save("nullgard%s.tif" % counter)
                    #
                    #     # Expand potential garden grid by one cell
                    #     zonecounter = arcpy.sa.Expand(garcounter, 1, [CENTROID])
                    #     zonecounter.save("zonecounter%s.tif" % counter)
                    #
                    #
                    #     # Create a clipping raster for gardens
                    #     zapped = arcpy.sa.Plus(nullgard, unsuit)
                    #     zapped.save("zapped%s.tif" % counter)
                    #
                    #     # Clip expanded garden grid by removing unsuitable areas and places where garden currently exists "NODATA"
                    #     clipcounter = arcpy.sa.ExtractByMask(zonecounter, zapped)
                    #     clipcounter.save("clipcounter%s.tif" % counter)
                    #
                    #
                    #     # Find focal mean suitability values, to smooth them assumes a 3x3 window (default of second arg in function below)
                    #     suitcounter = arcpy.sa.FocalStatistics(suit, "#", "MEAN", "#")
                    #     suitcounter.save("suitcounter%s.tif" % counter)
                    #
                    #
                    #     # Find maximum focal suitability value in zone
                    #     maxcounter = arcpy.sa.ZonalStatistics(clipcounter, "VALUE", suitcounter, "MEAN", "#")
                    #     maxcounter.save("maxcounter%s.tif" % counter)
                    #
                    #
                    #
                    #     # Expand garden to the most suitable locations
                    #     garcounter = arcpy.sa.Con(zerocounter == 10000, 10000, Con(maxcounter <= suit, 10000, garcounter))
                    #     garcounter.save('garcounter%s.tif'% counter)
                    #
                    #
                    #
                    #     # Query raster for number of cells attributed 10000
                    #     garcountercursor = arcpy.SearchCursor(garcounter)
                    #     for row in garcountercursor:
                    #         if row.getValue('Value') == 10000:
                    #             currentsize = row.getValue('Count')
                    #             print "This garden is now %d cells large." % currentsize
                    #
                    #     # Break out of loop once garden is maxed out or can't grow anymore, and report back
                    #     if lastsize == currentsize:
                    #         break
                    #
                    #     # Update counter
                    #     counter += 1
                    #     gardenexists = 1
                    #
                    # print "This garden is done at %d cells!" % currentsize
                    # #garden_ok = arcpy.sa.Con(IsNull(garcounter), 0, garcounter)
                    # gardens = garcounter
                    # gardens.save('gardenslast.tif')
                    # # lc1 = arcpy.sa.Con(garden_ok == 10000, 650, lc)
                    # # age1 = arcpy.sa.Con(garden_ok == 10000, 0, age)
                    # garcounter_nonull = arcpy.sa.Con(IsNull(garcounter), 0, garcounter)
                    # lc1 = arcpy.sa.Con(garcounter_nonull == 10000, 650, lc)
                    # age1 = arcpy.sa.Con(garcounter_nonull == 10000, 0, age)
                    # lc = lc1
                    # lc.save('lc%s.tif' % counter)
                    # age = age1

                    # self.population_to_garden_area()
                    # # Grow garden iteratively until threshold is reached
                    # # while self.garden_area < self.garden_area_target:
                    #
                    # local_max = arcpy.GetRasterProperties_management(local_suitability, 'MAXIMUM').getOutput(0)
                    # potential_center = arcpy.sa.SetNull(local_suitability, local_suitability, 'VALUE <> %s' % local_max)
                    # arcpy.RasterToPoint_conversion(in_raster=potential_center,
                    #                                out_point_features=self.temp_point)
                    #
                    # arcpy.CreateRandomPoints_management(out_path=s.TEMP_DIR,
                    #                                     out_name='center.shp',
                    #                                     constraining_feature_class=self.temp_point,
                    #                                     number_of_points_or_field=1)
                    #
                    # arcpy.PointToRaster_conversion(in_features=os.path.join(s.TEMP_DIR, 'center.shp'),
                    #                                out_rasterdataset=os.path.join(self.OUTPUT_DIR, 'center.tif'))
                    #
                    # # while self.garden_area < self.garden_area_target:
                    # center = arcpy.Raster(os.path.join(self.OUTPUT_DIR, 'center.tif'))
                    # self.garden = arcpy.sa.Con(arcpy.sa.IsNull(center) == 0, s.GARDEN_ID)
                    #
                    # self.garden.save(os.path.join(self.OUTPUT_DIR, 'garden.tif'))
                    #
                    # # Expand potential garden by a one cell ring around current garden
                    # zone = arcpy.sa.Expand(self.garden, 1, s.GARDEN_ID)
                    # zone.save(os.path.join(self.OUTPUT_DIR, 'zone.tif'))





                    #     # Expand potential garden grid by one cell
                    #     zone = arcpy.sa.Expand(self.garden, 1, [s.GARDEN_ID])
                    #
                    #     # where zone cells are coincident with unsuitable cells set null
                    #
                    #     # calculate focal mean suitability values, within a rectangular 3x3 window
                    #     mean_suitability = arcpy.sa.FocalStatistics(suitability, "#", "MEAN", "#")
                    #
                    #     # Find maximum mean suitability value in zone
                    #     zone_max = arcpy.sa.ZonalStatistics(clip, "VALUE", mean_suitability, "MEAN", "#")
                    #
                    #     # Expand garden to the most suitable locations
                    #     garden = arcpy.sa.Con(zero == s.GARDEN_ID, s.GARDEN_ID,
                    #                           arcpy.sa.Con(mean_suitability >= zone_max, s.GARDEN_ID, self.ecocommunities))
                    #
                    #     garcounter.save('garcounter%s.tif' % counter)
                    #
                    #     # re-count number of garden cells
                    #     self.get_garden_area()
                    #
                    #     # Break if garden stops expanding before reaching required size
                    #     if last_area == self.garden_area:
                    #         break
                    #
                    #     gardenexists = 1
                    #
                    # print "This garden is done at %d cells!" % currentsize
                    #
                    # gardens = garcounter
                    #
                    # garcounter_nonull = arcpy.sa.Con(arcpy.sa.IsNull(garcounter), 0, garcounter)
                    # lc1 = arcpy.sa.Con(garcounter_nonull == 10000, 650, lc)
                    # age1 = arcpy.sa.Con(garcounter_nonull == 10000, 0, age)
                    # lc = lc1
                    #
                    # age = age1

    def run_year(self):
        """

        :return:
        """
