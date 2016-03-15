from create_ponds import *
from arcpy import env
import posixpath as os


env.overWriteOutput = True

# Directories
root_dir = 'E:/_data/welikia/beaver_ponds/_test'
input_dir = os.join(root_dir, 'inputs')
output_dir = os.join(root_dir, 'outputs')

# Environment Setting
env.workspace = root_dir
print env.workspace
env.scratchWorkspace = os.join(root_dir, 'Scratch_Geodatabase.gdb')
print env.scratchWorkspace
env.overWriteOutput = True

# Inputs
DEM = os.join(input_dir, 'UPLAND_DEM_BURNED_STREAMS_5m_FILL.tif')

flow_direction = os.join(input_dir, 'flow_direction.tif')

suitable_streams = os.join(input_dir, 'suitability_surface.tif')

landcover = os.join(input_dir, 'landcover.tif')


# Model Parameters
CARRYING_CAPACITY = 10
MINIMUM_DISTANCE = 1000

# Initate trial
print 'initiating trial'

# calculate suitability points
print 'calculating suitable points'
suitability_points = os.join(input_dir, 'suitability_points_initial_00.shp')

if arcpy.Exists(suitability_points):
    arcpy.Delete_management(suitability_points)

calculate_suitability(landcover=landcover,
                      streams=suitable_streams,
                      suitability_points=suitability_points)

# choose pond locations
print 'selecting pond locations'
pond_points = os.join(output_dir, 'pond_points.shp')

if arcpy.Exists(pond_points):
    arcpy.Delete_management(pond_points)

assign_pond_locations(constraint=suitability_points,
                      num_points=CARRYING_CAPACITY)

# convert pond points feature to coordinate list
print 'converting pond points to coordinate list'

coordinate_list = dam_points_coordinates(pond_points)

# create ponds
pond_list = []
for p, i in zip(coordinate_list, range(len(coordinate_list))):
    print 'calculating pond %s' % i
    temp_point = os.join(output_dir, 'temp_point.shp')

    if arcpy.Exists(temp_point):
        arcpy.Delete_management(temp_point)

    pond = create_pond(dem=DEM,
                       flow_direction=flow_direction,
                       coordinates=p,
                       temp_point=temp_point)

    pond_list.append(pond)

print 'summing ponds and reclassify as binary'
ponds = arcpy.sa.Con(arcpy.sa.CellStatistics(pond_list, 'SUM') > 0, 1, 0)

ponds.save(os.join(output_dir, 'ponds_00.tif'))

pond_count, region_group = count_ponds(ponds)

time_since_disturbance = initial_time_since_disturbance(region_group, landcover)

time_since_disturbance.save(os.join(output_dir, 'time_since_last_disturbance_00.tif'))

