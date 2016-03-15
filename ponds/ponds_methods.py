# Import system modules
import arcpy
from arcpy import env
import sys
import random
import posixpath as os

# checkout spatial analyst
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to get spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)

# input_dir = 'E:/_data/welikia/beaver_ponds'
#
# # environment settings
# env.overWriteOutput = True

# Inputs
# streams = "E:/_data/welikia/beaver_ponds/WELIKIA_STREAMS_SYNTHESIS_NO_CREEKS/WELIKIA_STREAMS_SYNTHESIS_NO_CREEKS.shp"
# DENSITY = 2.0
#
#
# '''
# Calculate number of ponds in landscape
# '''
# def number_of_ponds(density, streams):
#     cursor = arcpy.SearchCursor(streams)
#
#     total_stream_length = 0
#
#     for row in cursor:
#         total_stream_length += row.getValue('length')
#
#     return int(total_stream_length / 1000 * density)
#
#
# ponds = .4 * 1214
#
#


#
# assign_pond_locations(constraint=streams, num_points=ponds)

# PARAMETERS
DISTANCE = 800
CELL_SIZE = 5
DAM_HEIGHT = 9


def assign_pond_locations(constraint, num_points):
    """
    This method assigns random locations for each pond that fall within the bounds of
    suitable habitat.
    :param constraint:
    :param num_points:
    :return:
    """


    # constraint is the area of all suitable loacations for ponds
    # num_points is the maximum number of ponds that should be assigned
    arcpy.CreateRandomPoints_management(out_path="E:/_data/welikia/beaver_ponds/_test/outputs/",
                                        out_name="pond_points.shp",
                                        constraining_feature_class=constraint,
                                        number_of_points_or_field=num_points,
                                        minimum_allowed_distance=1000)


def dam_points_coordinates(points):
    """
    take points shp and convert to X Y coordinate tuples, this intermediate is needed to
    create pour points for the watershed tool.
    :param points:
    :return: coordinate_list
    """

    cursor = arcpy.da.SearchCursor(points, 'SHAPE@XY')

    coordinate_list = []
    for point in cursor:
        # print point[0]
        coordinate_list.append((point[0][0], point[0][1]))

    return coordinate_list


def create_pond(dem, flow_direction, coordinates, temp_point):
    """
    create a raster with a single pond using watershed tool and conditional statement.
    The location of the pond is specified by the temp_point argument. DEM must be hydrologicaly
    conditioned to use this method.
    :param dem:
    :param flow_direction:
    :param coordinates:
    :param temp_point:
    :return:
    """

    pour_point = arcpy.Point(coordinates[0], coordinates[1])

    arcpy.CopyFeatures_management(in_features=arcpy.PointGeometry(pour_point),
                                  out_feature_class=temp_point)

    # print type(pour_point)
    # get pour point elevation
    pour_point_elevation = arcpy.sa.ExtractByPoints(points=pour_point,
                                                    in_raster=dem)
    # print pour_point_elevation.maximum

    # set dam height
    dam_height = pour_point_elevation.maximum + DAM_HEIGHT
    # print dam_height

    # calculate watershed for dam
    watershed = arcpy.sa.Watershed(in_flow_direction_raster=flow_direction,
                                   in_pour_point_data=temp_point)

    # calculate flooded area
    pond = arcpy.sa.Con(watershed == 0, arcpy.sa.Con((arcpy.Raster(dem) <= dam_height), dam_height, 0))

    pond = arcpy.sa.Con(arcpy.sa.IsNull(pond), 0, pond)

    return pond


def calculate_territory(landcover):
    """
    calculate territory creates a euclidean distance buffer using the global DISTANCE
    parameter. The returned raster is used to exclude areas from the set of points used
    to create new ponds, ensuring that pond density does not exceed the specified threshold.
    :param landcover:
    :return: exclude_territory
    """

    landcover_set_null = arcpy.sa.SetNull((landcover == 2) | (landcover == 3), 1)

    territory = arcpy.sa.EucDistance(in_source_data=landcover_set_null,
                                     maximum_distance=DISTANCE,
                                     cell_size=CELL_SIZE)

    exclude_territory = arcpy.sa.IsNull(territory)

    return exclude_territory


def count_ponds(ponds):

    """
    count_ponds takes a binary pond raster (pond = 1, no-pond = 0) and uses a region group
    function to count the number of ponds in the extent. This method returns the number of
    ponds as an integer and the region_group product as a raster object.
    :param ponds:
    :return: pond_count, region_group
    """

    # sum_ponds = arcpy.Raster(in_raster)
    print 'setting null'
    sum_ponds_set_null = arcpy.sa.SetNull(ponds != 1, 1)
    # sum_ponds_set_null.save('E:/_data/welikia/beaver_ponds/_test/outputs/ponds_set_null_%s.tif' % year)

    print 'region grouping'
    region_group = arcpy.sa.RegionGroup(in_raster=sum_ponds_set_null,
                                        number_neighbors='EIGHT',
                                        zone_connectivity='CROSS')

    # region_group.save('E:/_data/welikia/beaver_ponds/_test/outputs/region_group_%s.tif' % year)
    print 'getting count'
    pond_count = arcpy.GetRasterProperties_management(in_raster=region_group,
                                                      property_type='UNIQUEVALUECOUNT')

    pond_count = int(pond_count.getOutput(0))

    return pond_count, region_group


def calculate_suitability(streams, landcover, suitability_points):
    """
    calculate set of suitability points to constrain the potential locations of new ponds.
    new ponds can only be placed:
        1) outside the bounds existing beaver territory
        2) on mapped streams with gradients lower than 15%
        3) above the highest tidal influence
    :param streams:
    :param landcover:
    :param suitability_points:
    :return:
    """

    if type(streams) == str:
        streams = arcpy.Raster(streams)

    if type(landcover) == str:
        landcover = arcpy.Raster(landcover)

    exclude_territory = calculate_territory(landcover)

    suitability_surface = exclude_territory * streams

    suitability_surface_set_null = arcpy.sa.SetNull(suitability_surface, suitability_surface, "VALUE = 0")

    arcpy.RasterToPoint_conversion(in_raster=suitability_surface_set_null,
                                   out_point_features=suitability_points)


def initial_time_since_disturbance(in_raster, landcover):
    """
    This method returns an initial time_since_disturbance raster. time_since_disturbance
    cells that are coincident with new ponds are assigned random values between 0 and 9,
    all other cells are iniated with a value of 30.
    :param in_raster:
    :param landcover:
    :return: 0_time_since_disturbance
    """

    pond_count = in_raster

    arcpy.AddField_management(in_table=pond_count,
                              field_name='age',
                              field_type='SHORT')

    cursor = arcpy.UpdateCursor(pond_count)

    for row in cursor:
        age = random.randint(0,9)
        row.setValue("age", age)
        cursor.updateRow(row)

    age = arcpy.sa.Lookup(in_raster=pond_count,
                          lookup_field="age")

    start_age = arcpy.sa.Con((arcpy.sa.IsNull(pond_count) == 1) & (landcover), 30,
                             arcpy.sa.Con(pond_count, age))

    return start_age


def update_time_since_disturbance(time_since_disturbance, new_ponds):
    """
    This method incorporates newly created ponds into the time_since_disturbance raster.
    Cells in the time since disturbance raster that are coincident with new pond cells
    (value = 1) are reset to 0.
    :param time_since_disturbance:
    :param new_ponds:
    :return: time_since_disturbance
    """
    time_since_disturbance = arcpy.sa.Con(new_ponds == 1, 0, time_since_disturbance)

    return time_since_disturbance


def succession(time_since_disturbance):
    """
    succession: this method uses a nested conditional statement
    to convert the time_since disturbance raster in to a simple community raster.
    Transition thresholds are based on Logofet et al. 2015
    :param time_since_disturbance:
    :return:
    """

    landcover = arcpy.sa.Con(time_since_disturbance >= 30, 3, (arcpy.sa.Con(time_since_disturbance >= 10, 2, 1)))

    return landcover

