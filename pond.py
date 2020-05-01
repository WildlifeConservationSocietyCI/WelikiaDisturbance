import os
import arcpy
import numpy as np
import logging

import utils
import settings as s
import disturbance as d


class PondDisturbance(d.Disturbance):
    INPUT_DIR = os.path.join(s.INPUT_DIR, 'pond')
    OUTPUT_DIR = os.path.join(s.OUTPUT_DIR, 'pond')
    DEM = s.dem
    FLOW_DIRECTION = s.flow_direction
    SUITABLE_STREAMS = s.stream_suitability

    def __init__(self, year):
        super(PondDisturbance, self).__init__(year)

        self._region_group = None
        self._pond_point_file = "pond_points.shp"
        self.initial_flag = False
        self.time_since_disturbance = None
        self.land_cover = None
        self.pond_count = 0
        self.new_ponds = None
        self.coordinate_list = None
        self.suitability_points = os.path.join(s.TEMP_DIR, 'suitability_points.shp')
        self.pond_points = os.path.join(s.TEMP_DIR, self._pond_point_file)
        self.temp_point_pond = os.path.join(s.TEMP_DIR, 'temp_point_pond.shp')
        self.pond_list = []
        self.new_pond_area = 0
        self.upland_area = 0

        # self.ecocommunities.save(os.path.join(s.OUTPUT_DIR, 'com_start_%s.tif' % self.year))
        self.set_upland_area()
        self.carrying_capacity = int(s.DENSITY * self.upland_area)
        self.set_time_since_disturbance()

    @staticmethod
    def reset_temp(filename):
        if arcpy.Exists(filename):
            arcpy.Delete_management(filename)

    def assign_pond_locations(self):
        """
        This method assigns random locations for each pond that fall within the bounds of
        suitable habitat.
        :return:
        """
        num_points = int(s.DENSITY * self.upland_area) - self.pond_count
        logging.info('num points: {}'.format(num_points))
        # constraint is the area of all suitable locations for new_ponds
        # num_points is the maximum number of new_ponds that should be assigned
        arcpy.CreateRandomPoints_management(out_path=s.TEMP_DIR,
                                            out_name=self._pond_point_file,
                                            constraining_feature_class=self.suitability_points,
                                            number_of_points_or_field=num_points,
                                            minimum_allowed_distance=s.MINIMUM_DISTANCE)

    def dam_points_coordinates(self):
        """
        take points shp and convert to X Y coordinate tuples, this intermediate format
        is needed to create pour points for the watershed tool.
        :return: coordinate_list
        """
        cursor = arcpy.da.SearchCursor(self.pond_points, "SHAPE@XY")

        coordinate_list = []
        for point in cursor:
            coordinate_list.append((point[0][0], point[0][1]))

        self.coordinate_list = coordinate_list
        logging.info('coordinate list: {}'.format(self.coordinate_list))
        del cursor

    def flood_pond(self, coordinates):
        """
        create a raster with a single pond using watershed tool and dam height.
        The location of the pond is specified by the temp_point argument. DEM must be hydrologicaly
        conditioned to use this method.
        :param coordinates:
        :return:
        """
        pour_point = arcpy.Point(coordinates[0], coordinates[1])

        arcpy.CopyFeatures_management(in_features=arcpy.PointGeometry(pour_point),
                                      out_feature_class=self.temp_point_pond)

        pour_point_elevation = arcpy.sa.ExtractByPoints(points=pour_point,
                                                        in_raster=self.DEM)

        dam_height = pour_point_elevation.maximum + s.DAM_HEIGHT

        watershed = arcpy.sa.Watershed(in_flow_direction_raster=self.FLOW_DIRECTION,
                                       in_pour_point_data=self.temp_point_pond)

        # calculate flooded area
        pond = arcpy.sa.Con(watershed == 0, arcpy.sa.Con((arcpy.Raster(self.DEM) <= dam_height), dam_height, 0))
        pond = arcpy.sa.Con(arcpy.sa.IsNull(pond), 0, pond)

        return pond

    def create_ponds(self):
        # calculate suitability using existing new_ponds
        self.reset_temp(self.suitability_points)
        self.calculate_suitability()

        # select pond locations
        # logging.info('selecting pond locations')
        self.reset_temp(self.pond_points)
        # logging.info(self.pond_points, type(self.pond_points))
        self.assign_pond_locations()

        # convert pond points feature to list of longitude latitude coordinates
        # logging.info('converting pond points to coordinate list')
        self.dam_points_coordinates()
        # logging.info(self.coordinate_list)
        if len(self.coordinate_list) > 0:
            # create new_ponds
            for p, i in zip(self.coordinate_list, range(len(self.coordinate_list))):
                # logging.info('calculating pond %s' % i)
                self.reset_temp(self.temp_point_pond)
                pond = self.flood_pond(coordinates=p)
                self.pond_list.append(pond)

            self.new_ponds = arcpy.sa.CellStatistics(self.pond_list, 'SUM')
            self.new_ponds.save(os.path.join(self.OUTPUT_DIR, 'ponds_%s.tif' % self.year))
            self.new_ponds = arcpy.sa.Con(self.new_ponds != 0, s.ACTIVE_BEAVER_POND_ID, 0)

            # update canopy and forest age based on the position of new ponds
            new_ponds_array = arcpy.RasterToNumPyArray(self.new_ponds)
            self.canopy[new_ponds_array == s.ACTIVE_BEAVER_POND_ID] = 0
            self.forest_age[new_ponds_array == s.ACTIVE_BEAVER_POND_ID] = 0
            self.dbh[new_ponds_array == s.ACTIVE_BEAVER_POND_ID] = 0

    def calculate_territory(self):
        """
        calculate territory creates a euclidean distance buffer using the global DISTANCE
        parameter. The returned raster is used to exclude areas from the set of points used
        to create new_ponds, ensuring that pond density does not exceed the threshold
        specified in the settings file.
        :rtype: object
        :return: exclude_territory
        """
        land_cover_set_null = arcpy.sa.SetNull(self.ecocommunities != s.ACTIVE_BEAVER_POND_ID, 1)

        territory = arcpy.sa.EucDistance(in_source_data=land_cover_set_null,
                                         maximum_distance=s.MINIMUM_DISTANCE,
                                         cell_size=s.CELL_SIZE)

        exclude_territory = arcpy.sa.IsNull(territory)

        return exclude_territory

    def set_region_group(self, in_raster):
        hist = utils.hist(self.ecocommunities)

        if s.ACTIVE_BEAVER_POND_ID in hist:
            sum_ponds_set_null = arcpy.sa.SetNull(in_raster != s.ACTIVE_BEAVER_POND_ID, 1)
            # sum_ponds_set_null.save(os.path.join(s.TEMP_DIR, 'ponds_set_null_%s.tif' % self.year))

            self._region_group = arcpy.sa.RegionGroup(in_raster=sum_ponds_set_null,
                                                      number_neighbors='EIGHT',
                                                      zone_connectivity='CROSS')
            # self._region_group.save(os.path.join(s.TEMP_DIR, 'region_group_%s.tif' % self.year))

        else:
            logging.info('no active ponds in landscape')

    def count_ponds(self):
        """
        Count_ponds calculates and assigns the class attribute pond_count.
        This method takes a binary pond raster (pond = 1, background = 0), and uses a region group function
        to assigns unique identifiers to each patch/pond.
        :return:
        """

        if self._region_group is None:
            self.pond_count = 0
        else:
            pond_count = arcpy.GetRasterProperties_management(in_raster=self._region_group,
                                                              property_type='UNIQUEVALUECOUNT')

            pond_count = int(pond_count.getOutput(0))

            # logging.info('pond count: %s' % pond_count)
            self.pond_count = pond_count

    def calculate_suitability(self):
        """
        calculate set of suitability points to constrain the potential locations of new_ponds.
        new_ponds can only be placed on cells that meet the following conditions:
            1) outside the bounds existing beaver territory
            2) on mapped streams with gradients <= 8 degrees
            3) above the highest tidal influence
        :return:
        """
        # TODO what other conditions need to be met, make sure the correct stream types are used
        # TODO recalculate suitable streams with new landcover

        if type(self.SUITABLE_STREAMS) == str:
            self.SUITABLE_STREAMS = arcpy.Raster(self.SUITABLE_STREAMS)

        # calculate current territories
        exclude_territory = self.calculate_territory()

        # intersect un-colonized parts of the landscape with suitable streams
        suitability_surface = exclude_territory * self.SUITABLE_STREAMS

        suitability_surface_set_null = arcpy.sa.SetNull(suitability_surface == 0, suitability_surface)

        # convert suitable cells to points for random selection and watershed pour point
        arcpy.RasterToPoint_conversion(in_raster=suitability_surface_set_null,
                                       out_point_features=self.suitability_points)

    def update_time_since_disturbance(self):
        """
        This method incorporates newly created new_ponds into the time_since_disturbance raster.
        Cells in the time since disturbance raster that are coincident with new pond cells
        (value = 1) are reset to 0.
        :return:
        """

        self.time_since_disturbance = arcpy.sa.Con(self.new_ponds == s.ACTIVE_BEAVER_POND_ID, 1,
                                                   self.time_since_disturbance)

    def abandon_ponds(self):
        # get raster attributes
        lower_left = arcpy.Point(self.ecocommunities.extent.XMin, self.ecocommunities.extent.YMin)
        cell_size = self.ecocommunities.meanCellWidth

        # convert community raster to array
        com_array = arcpy.RasterToNumPyArray(self.ecocommunities)

        hist = utils.hist(com_array)

        if s.ACTIVE_BEAVER_POND_ID in hist:
            # identify individual ponds using region group
            ponds = arcpy.sa.SetNull(self.ecocommunities != s.ACTIVE_BEAVER_POND_ID, s.ACTIVE_BEAVER_POND_ID)

            region_group = arcpy.sa.RegionGroup(in_raster=ponds,
                                                number_neighbors='EIGHT',
                                                zone_connectivity='CROSS',
                                                )
            # region_group.save(os.path.join(s.OUTPUT_DIR, 'region_group_%s.tif' % self.year))

            # create region group array
            group_array = arcpy.RasterToNumPyArray(region_group, nodata_to_value=-9999)
            pond_list = np.unique(group_array)
            logging.info(pond_list)
            for i in pond_list[1:]:
                if np.random.randint(0, 100) <= s.POND_ABANDONMENT_PROBABILITY:
                    logging.info('***********abandon pond')
                    com_array[group_array == i] = s.SHALLOW_EMERGENT_MARSH_ID

            self.ecocommunities = arcpy.NumPyArrayToRaster(com_array, lower_left, cell_size)

            self.ecocommunities.save(os.path.join(s.OUTPUT_DIR, 'com_after_abandon_%s.tif' % self.year))

    def set_time_since_disturbance(self):
        this_year_time_since_disturbance = os.path.join(self.OUTPUT_DIR,
                                                        'time_since_disturbance_%s.tif' % (self.year - 1))

        if os.path.isfile(this_year_time_since_disturbance):
            self.time_since_disturbance = arcpy.Raster(this_year_time_since_disturbance)

        else:
            self.time_since_disturbance = arcpy.sa.Con(self.ecocommunities == s.ACTIVE_BEAVER_POND_ID, 1, 30)

    def set_pond_area(self):
        hist = utils.hist(self.time_since_disturbance)

        if 1 in hist:
            self.new_pond_area = hist[1]
        else:
            self.new_pond_area = 0

    def run_year(self):
        if s.DEBUG_MODE:
            logging.info('incrementing time since disturbance')

        if self.year > min(s.RUN_LENGTH):
            self.time_since_disturbance += 1

        if s.DEBUG_MODE:
            logging.info('abandoning ponds')

        self.abandon_ponds()

        self.set_region_group(self.ecocommunities)

        self.count_ponds()
        if s.DEBUG_MODE:
            logging.info('counting number of active ponds')
            logging.info('count: %s' % self.pond_count)
            logging.info('carrying capacity: %s' % self.carrying_capacity)

        if self.pond_count < self.carrying_capacity:
            self._region_group = None
            logging.info('number of active ponds [%s] is below carrying capacity [%s], creating new ponds'
                         % (self.pond_count, self.carrying_capacity))

            logging.info('creating new [%s] ponds' % (self.carrying_capacity - self.pond_count))
            self.create_ponds()

            logging.info('updating time since disturbance')
            self.update_time_since_disturbance()

            logging.info('add new ponds to ecocommunites')
            self.ecocommunities = arcpy.sa.Con(self.new_ponds == s.ACTIVE_BEAVER_POND_ID,
                                               s.ACTIVE_BEAVER_POND_ID, self.ecocommunities)

            self.ecocommunities.save(os.path.join(s.TEMP_DIR, '%s_ecocommunities.tif' % self.year))

        self.time_since_disturbance.save(os.path.join(self.OUTPUT_DIR, 'time_since_disturbance_%s.tif' % self.year))
        self.ecocommunities.save(os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year))

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

        self.set_pond_area()
        self.ecocommunities = None
        del self.ecocommunities
