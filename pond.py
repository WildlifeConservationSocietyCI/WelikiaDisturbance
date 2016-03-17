import settings as s
from settings import arcpy
from settings import os
import random


class PondDisturbance(s.Disturbance):

    # CLASS VARIABLES
    year = None
    ecocommunities = None

    # PRIVATE VARIABLES
    _region_group = None
    _suitpoints = 'suitability_points.shp'
    _ecocommunities_filename = 'ecocommunities%s.tif'
    # CONSTANTS

    # Pond Directories
    INPUT_DIR = os.join(s.INPUT_DIR, 'pond')
    OUTPUT_DIR = os.join(s.OUTPUT_DIR, 'pond')

    # Pond Parameters
    CARRYING_CAPACITY = s.CARRYING_CAPACITY
    MINIMUM_DISTANCE = s.MINIMUM_DISTANCE
    CELL_SIZE = s.CELL_SIZE
    DAM_HEIGHT = s.DAM_HEIGHT

    # Constant Inputs
    DEM = os.join(INPUT_DIR, 'UPLAND_DEM_BURNED_STREAMS_5m_FILL.tif')
    FLOW_DIRECTION = os.join(INPUT_DIR, 'flow_direction.tif')
    SUITABLE_STREAMS = os.join(INPUT_DIR, 'suitability_surface.tif')

    def __init__(self, year):
        self.year = year
        self.time_since_disturbance = arcpy.Raster(os.join(self.OUTPUT_DIR, 'time_since_disturbance_%s.tif' % (year - 1)))
        self.land_cover = None
        self.pond_count = None
        self.suitability_points = os.join(s.TEMP_DIR, self._suitpoints)
        self.coordinate_list = None
        self.pond_points = os.join(s.TEMP_DIR, 'pond_points.shp')
        self.temp_point = os.join(s.TEMP_DIR, 'temp_point.shp')
        self.pond_list = []

        this_year_ecocomms = os.join(self.OUTPUT_DIR, self._ecocommunities_filename % year)
        last_year_ecocomms = os.join(self.OUTPUT_DIR, self._ecocommunities_filename % (year - 1))
        if os.isfile(this_year_ecocomms):
            self.ecocommunities = arcpy.Raster(this_year_ecocomms)
        elif os.isfile(last_year_ecocomms):
            self.ecocommunities = arcpy.Raster(last_year_ecocomms)
        else:
            self.ecocommunities = arcpy.Raster(s.ecocommunities)

    def assign_pond_locations(self):
        """
        This method assigns random locations for each pond that fall within the bounds of
        suitable habitat.
        :return:
        """

        num_points = s.CARRYING_CAPACITY - self.pond_count

        # constraint is the area of all suitable loacations for ponds
        # num_points is the maximum number of ponds that should be assigned
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

    def create_pond(self, coordinates):
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

    def calculate_territory(self):
        """
        calculate territory creates a euclidean distance buffer using the global DISTANCE
        parameter. The returned raster is used to exclude areas from the set of points used
        to create new ponds, ensuring that pond density does not exceed the specified threshold.
        :rtype: object
        :return: exclude_territory
        """

        land_cover_set_null = arcpy.sa.SetNull((self.land_cover == 2) | (self.land_cover == 3), 1)

        territory = arcpy.sa.EucDistance(in_source_data=land_cover_set_null,
                                         maximum_distance=s.MINIMUM_DISTANCE,
                                         cell_size=s.CELL_SIZE)

        exclude_territory = arcpy.sa.IsNull(territory)

        return exclude_territory


    def set_region_group(self):
        # sum_ponds = arcpy.Raster(in_raster)
        print 'setting null'
        sum_ponds_set_null = arcpy.sa.SetNull(self.land_cover != 1, 1)
        # sum_ponds_set_null.save('E:/_data/welikia/beaver_ponds/_test/outputs/ponds_set_null_%s.tif' % year)

        print 'region grouping'
        self._region_group = arcpy.sa.RegionGroup(in_raster=sum_ponds_set_null,
                                            number_neighbors='EIGHT',
                                            zone_connectivity='CROSS')

        # region_group.save('E:/_data/welikia/beaver_ponds/_test/outputs/region_group_%s.tif' % year)


    def count_ponds(self):

        """
        count_ponds takes a binary pond raster (pond = 1, no-pond = 0) and uses a region group
        function to count the number of ponds in the extent. This method returns the number of
        ponds as an integer and the region_group product as a raster object.
        :return:
        """
        self.set_region_group()

        print 'getting count'
        pond_count = arcpy.GetRasterProperties_management(in_raster=self._region_group,
                                                          property_type='UNIQUEVALUECOUNT')

        pond_count = int(pond_count.getOutput(0))

        self.pond_count = pond_count

    def calculate_suitability(self):
        """
        calculate set of suitability points to constrain the potential locations of new ponds.
        new ponds can only be placed:
            1) outside the bounds existing beaver territory
            2) on mapped streams with gradients lower than 15%
            3) above the highest tidal influence
        :return:
        """

        if type(self.SUITABLE_STREAMS) == str:
            self.SUITABLE_STREAMS = arcpy.Raster(self.SUITABLE_STREAMS)

        exclude_territory = self.calculate_territory()

        suitability_surface = exclude_territory * self.SUITABLE_STREAMS

        suitability_surface_set_null = arcpy.sa.SetNull(suitability_surface, suitability_surface, "VALUE = 0")

        arcpy.RasterToPoint_conversion(in_raster=suitability_surface_set_null,
                                       out_point_features=self.suitability_points)

    def initial_time_since_disturbance(self):
        """
        This method returns an initial time_since_disturbance raster. time_since_disturbance
        cells that are coincident with new ponds are assigned random values between 0 and 9,
        all other cells are initiated with a value of 30.
        :return: 0_time_since_disturbance
        """

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

        start_age = arcpy.sa.Con((arcpy.sa.IsNull(self._region_group) == 1) & self.ecocommunities, 30,
                                 arcpy.sa.Con(self._region_group, age))

        return start_age

    def update_time_since_disturbance(self, new_ponds):
        """
        This method incorporates newly created ponds into the time_since_disturbance raster.
        Cells in the time since disturbance raster that are coincident with new pond cells
        (value = 1) are reset to 0.
        :param new_ponds:
        :return: time_since_disturbance
        """
        self.time_since_disturbance = arcpy.sa.Con(new_ponds == 1, 0, self.time_since_disturbance)

    def succession(self):
        """
        succession: this method uses a nested conditional statement
        to convert the time_since disturbance raster in to a simple community raster.
        Transition thresholds are based on Logofet et al. 2015
        :return:
        """

        self.land_cover = arcpy.sa.Con(self.time_since_disturbance >= 30, 3,
                                       (arcpy.sa.Con(self.time_since_disturbance >= 10, 2, 1)))

    def run_year(self):
        self.time_since_disturbance += 1
        self.time_since_disturbance += 1

        self.succession()

        self.count_ponds()

        self.land_cover.save(os.join(self.OUTPUT_DIR, 'land_cover_%s.tif' % self.year))

        if self.pond_count < self.CARRYING_CAPACITY:
            print 'number of active ponds is below carrying capacity, creating new ponds'
            # calculate number of new ponds to create
            new_ponds = self.CARRYING_CAPACITY - self.pond_count

            # calculate suitability using existing ponds
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

            # create ponds
            for p, i in zip(self.coordinate_list, range(len(self.coordinate_list))):
                print 'calculating pond %s' % i
                self.reset_temp(self.temp_point)
                pond = self.create_pond(coordinates=p)
                self.pond_list.append(pond)

            ponds = arcpy.sa.Con(arcpy.sa.CellStatistics(self.pond_list, 'SUM') > 0, 1, 0)
            ponds.save(os.join(self.OUTPUT_DIR, 'ponds_%s.tif' % self.year))

            self.update_time_since_disturbance(ponds)

            self.time_since_disturbance.save(os.join(self.OUTPUT_DIR, 'time_since_disturbance_%s.tif' % self.year))

    def reset_temp(self, filename):
        if arcpy.Exists(filename):
            arcpy.Delete_management(filename)

