import settings as s
from settings import arcpy
from settings import os
import random
import time
import logging
from arcpy import env


class PondDisturbance(s.Disturbance):
    # CLASS VARIABLES
    year = None
    ecocommunities = None

    # PRIVATE VARIABLES
    _region_group = None
    _suitpoints = 'suitability_points.shp'
    _ecocommunities_filename = 'ecocommunities_%s.tif'
    # CONSTANTS

    # Pond Directories
    INPUT_DIR = os.path.join(s.INPUT_DIR, 'pond')
    OUTPUT_DIR = os.path.join(s.OUTPUT_DIR, 'pond')

    # Pond Parameters
    CARRYING_CAPACITY = s.CARRYING_CAPACITY
    MINIMUM_DISTANCE = s.MINIMUM_DISTANCE
    CELL_SIZE = s.CELL_SIZE
    DAM_HEIGHT = s.DAM_HEIGHT

    # Constant Inputs
    DEM = os.path.join(INPUT_DIR, 'UPLAND_DEM_BURNED_STREAMS_5m_FILL_bk_q.tif')
    FLOW_DIRECTION = os.path.join(INPUT_DIR, 'flow_direction_bk_q.tif')
    SUITABLE_STREAMS = os.path.join(INPUT_DIR, 'suitability_surface_bk_q.tif')

    def __init__(self, year):
        self.year = year
        self.time_since_disturbance = None
        self.land_cover = None
        self.pond_count = 0
        self.new_ponds = None
        self.suitability_points = os.path.join(s.TEMP_DIR, self._suitpoints)
        self.coordinate_list = None
        self.pond_points = os.path.join(s.TEMP_DIR, 'pond_points.shp')
        self.temp_point = os.path.join(s.TEMP_DIR, 'temp_point.shp')
        self.pond_list = []

        this_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % year)
        last_year_ecocomms = os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % (year - 1))
        if os.path.isfile(this_year_ecocomms):
            print this_year_ecocomms
            self.ecocommunities = arcpy.Raster(this_year_ecocomms)
        elif os.path.isfile(last_year_ecocomms):
            self.ecocommunities = arcpy.Raster(last_year_ecocomms)
        else:
            print 'initial run'
            self.ecocommunities = arcpy.Raster(s.ecocommunities)

        self.set_time_since_disturbance()

    def reset_temp(self, filename):
        if arcpy.Exists(filename):
            arcpy.Delete_management(filename)

    def assign_pond_locations(self):
        """
        This method assigns random locations for each pond that fall within the bounds of
        suitable habitat.
        :return:
        """
        num_points = s.CARRYING_CAPACITY - self.pond_count

        # constraint is the area of all suitable loacations for new_ponds
        # num_points is the maximum number of new_ponds that should be assigned
        arcpy.CreateRandomPoints_management(out_path=s.TEMP_DIR,
                                            out_name="pond_points.shp",
                                            constraining_feature_class=self.suitability_points,
                                            number_of_points_or_field=num_points,
                                            minimum_allowed_distance=s.MINIMUM_DISTANCE)

    def dam_points_coordinates(self):
        """
        take points shp and convert to X Y coordinate tuples, this intermediate is needed to
        create pour points for the watershed tool.
        :return: coordinate_list
        """

        cursor = arcpy.da.SearchCursor(self.pond_points, "SHAPE@XY")

        coordinate_list = []
        for point in cursor:
            # print point[0]
            coordinate_list.append((point[0][0], point[0][1]))

        self.coordinate_list = coordinate_list

    def flood_pond(self, coordinates):
        """
        create a raster with a single pond using watershed tool and conditional statement.
        The location of the pond is specified by the temp_point argument. DEM must be hydrologicaly
        conditioned to use this method.
        :param coordinates:
        :return:
        """

        pour_point = arcpy.Point(coordinates[0], coordinates[1])

        arcpy.CopyFeatures_management(in_features=arcpy.PointGeometry(pour_point),
                                      out_feature_class=self.temp_point)

        # get pour point elevation
        pour_point_elevation = arcpy.sa.ExtractByPoints(points=pour_point,
                                                        in_raster=self.DEM)

        # set dam height
        dam_height = pour_point_elevation.maximum + s.DAM_HEIGHT

        # calculate watershed for dam
        watershed = arcpy.sa.Watershed(in_flow_direction_raster=self.FLOW_DIRECTION,
                                       in_pour_point_data=self.temp_point)

        # calculate flooded area
        pond = arcpy.sa.Con(watershed == 0, arcpy.sa.Con((arcpy.Raster(self.DEM) <= dam_height), dam_height, 0))

        pond = arcpy.sa.Con(arcpy.sa.IsNull(pond), 0, pond)

        return pond

    def create_ponds(self):

        # calculate suitability using existing new_ponds
        self.reset_temp(self.suitability_points)
        self.calculate_suitability()

        # choose pond locations
        print 'selecting pond locations'
        self.reset_temp(self.pond_points)
        print self.pond_points, type(self.pond_points)
        self.assign_pond_locations()

        # convert pond points feature to list of longitude latitude coordinates
        print 'converting pond points to coordinate list'
        self.dam_points_coordinates()
        print self.coordinate_list

        # create new_ponds
        for p, i in zip(self.coordinate_list, range(len(self.coordinate_list))):
            print 'calculating pond %s' % i
            self.reset_temp(self.temp_point)
            pond = self.flood_pond(coordinates=p)
            self.pond_list.append(pond)

        self.new_ponds = arcpy.sa.Con(arcpy.sa.CellStatistics(self.pond_list, 'SUM') > 0, 622, 0)
        self.new_ponds.save('E:/_data/welikia/WelikiaDisturbance/outputs/pond/ponds_%s.tif' % self.year)

    def calculate_territory(self):
        """
        calculate territory creates a euclidean distance buffer using the global DISTANCE
        parameter. The returned raster is used to exclude areas from the set of points used
        to create new new_ponds, ensuring that pond density does not exceed the specified threshold.
        :rtype: object
        :return: exclude_territory
        """

        land_cover_set_null = arcpy.sa.SetNull(self.ecocommunities, 1, 'VALUE <> 622')

        territory = arcpy.sa.EucDistance(in_source_data=land_cover_set_null,
                                         maximum_distance=s.MINIMUM_DISTANCE,
                                         cell_size=s.CELL_SIZE)

        exclude_territory = arcpy.sa.IsNull(territory)

        return exclude_territory

    def set_region_group(self, in_raster):
        """
        :param in_raster:
        :rtype: object
        """

        # print 'setting null'
        sum_ponds_set_null = arcpy.sa.SetNull(in_raster != 622, 1)

        # print 'sum_ponds_set_null:', type(sum_ponds_set_null)
        sum_ponds_set_null.save(os.path.join(s.TEMP_DIR, 'ponds_set_null_%s.tif' % self.year))

        # print 'region grouping'
        self._region_group = arcpy.sa.RegionGroup(in_raster=sum_ponds_set_null,
                                                  number_neighbors='EIGHT',
                                                  zone_connectivity='CROSS')

        self._region_group.save(os.path.join(s.TEMP_DIR, 'region_group_%s.tif' % self.year))

    def count_ponds(self):

        """
        count_ponds takes a binary pond raster (pond = 1, no-pond = 0) and uses a region group
        function to count the number of new_ponds in the extent. This method returns the number of
        new_ponds as an integer and the region_group product as a raster object.
        :return:
        """
        # print type(self._region_group)
        # if self._region_group is None:
        #     print "set region group"
        #     self.set_region_group(self.ecocommunities)

        # print type(self._region_group)

        print 'getting count'
        pond_count = arcpy.GetRasterProperties_management(in_raster=self._region_group,
                                                          property_type='UNIQUEVALUECOUNT')

        pond_count = int(pond_count.getOutput(0))

        self.pond_count = pond_count

    def calculate_suitability(self):
        """
        calculate set of suitability points to constrain the potential locations of new new_ponds.
        new new_ponds can only be placed:
            1) outside the bounds existing beaver territory
            2) on mapped streams with gradients lower than 15%
            3) above the highest tidal influence
        :return:
        """

        if type(self.SUITABLE_STREAMS) == str:
            self.SUITABLE_STREAMS = arcpy.Raster(self.SUITABLE_STREAMS)

        exclude_territory = self.calculate_territory()

        # forest = arcpy.sa.Con((self.ecocommunities == 644) |
        #                       (self.ecocommunities == 629) |
        #                       (self.ecocommunities == 647), 1, 0)

        suitability_surface = exclude_territory * self.SUITABLE_STREAMS

        suitability_surface_set_null = arcpy.sa.SetNull(suitability_surface, suitability_surface, "VALUE = 0")

        arcpy.RasterToPoint_conversion(in_raster=suitability_surface_set_null,
                                       out_point_features=self.suitability_points)

    def initial_time_since_disturbance(self):
        """
        This method returns an initial time_since_disturbance raster. time_since_disturbance
        cells that are coincident with new new_ponds are assigned random values between 0 and 9,
        all other cells are initiated with a value of 30.
        :return:
        """
        print 'creating initial time since disturbance raster'
        self.create_ponds()

        self.set_region_group(self.new_ponds)

        arcpy.AddField_management(in_table=self._region_group,
                                  field_name='age',
                                  field_type='SHORT')

        cursor = arcpy.UpdateCursor(self._region_group)

        for row in cursor:
            age = random.randint(0, 9)
            row.setValue("age", age)
            cursor.updateRow(row)

        age = arcpy.sa.Lookup(in_raster=self._region_group,
                              lookup_field="age")

        # where new ponds exist return an random age else where there are no ponds within the original extent return 30
        self.time_since_disturbance = arcpy.sa.Con((arcpy.sa.IsNull(self._region_group) == 1) & self.ecocommunities, 30,
                                                   arcpy.sa.Con(self._region_group, age))

        self.time_since_disturbance.save(os.path.join(self.OUTPUT_DIR,
                                                      'time_since_disturbance_%s.tif' % self.year))

    def update_time_since_disturbance(self):
        """
        This method incorporates newly created new_ponds into the time_since_disturbance raster.
        Cells in the time since disturbance raster that are coincident with new pond cells
        (value = 1) are reset to 0.
        :return:
        """
        self.time_since_disturbance = arcpy.sa.Con(self.new_ponds == 622, 0, self.time_since_disturbance)

    def succession(self):
        """
        succession: this method uses a nested conditional statement
        to convert the time_since disturbance raster in to a simple community raster.
        Transition thresholds are based on Logofet et al. 2015
        :return:
        """

        self.land_cover = arcpy.sa.Con(self.ecocommunities,
                                       arcpy.sa.Con(self.time_since_disturbance >= 30, self.ecocommunities,
                                                    (arcpy.sa.Con((self.time_since_disturbance < 30) &
                                                                  (self.time_since_disturbance >= 10), 625,
                                                                  arcpy.sa.Con((self.time_since_disturbance < 10) &
                                                                               (self.time_since_disturbance >= 0),
                                                                               622, )))))

        # print 'succession calculation finished'
        self.land_cover.save(os.path.join(s.OUTPUT_DIR, self._ecocommunities_filename % self.year))

    def set_time_since_disturbance(self):
        this_year_time_since_disturbance = os.path.join(self.OUTPUT_DIR,
                                                        'time_since_disturbance_%s.tif' % (self.year - 1))
        if os.path.isfile(this_year_time_since_disturbance):
            self.time_since_disturbance = arcpy.Raster(this_year_time_since_disturbance)
            print this_year_time_since_disturbance, type(self.time_since_disturbance)
        else:
            self.initial_time_since_disturbance()
            self.time_since_disturbance = arcpy.Raster(
                os.path.join(self.OUTPUT_DIR, 'time_since_disturbance_%s.tif' % self.year))

    def run_year(self):

        start_time = time.time()

        print 'YEAR: %s' % self.year

        print 'incrementing time since disturbance'
        self.time_since_disturbance = arcpy.sa.Con(self.time_since_disturbance, self.time_since_disturbance + 1)

        print 'calculating land_cover'
        self.succession()

        self.set_region_group(self.land_cover)

        print 'counting number of active ponds'
        self.count_ponds()

        if self.pond_count < self.CARRYING_CAPACITY:
            self._region_group = None
            print 'number of active ponds [%s] is below carrying capacity [%s], creating new ponds' \
                  % (self.pond_count, s.CARRYING_CAPACITY)

            self.create_ponds()

            self.new_ponds.save(os.path.join(self.OUTPUT_DIR, 'ponds_%s.tif' % self.year))

            self.update_time_since_disturbance()

        self.time_since_disturbance.save(os.path.join(self.OUTPUT_DIR, 'time_since_disturbance_%s.tif' % self.year))

        end_time = time.time()
        logging.info('run time: %s' % ((end_time - start_time) / 60))
