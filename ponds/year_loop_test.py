from create_ponds import *

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

# Paths
suitability_points = os.join(input_dir, 'suitability_points.shp')

pond_points = os.join(output_dir, 'pond_points.shp')

time_since_disturbance = ""

# Model Parameters
CARRYING_CAPACITY = 115
MINIMUM_DISTANCE = 1000
for year in range(1, 5):

    print 'year %s trial start' % year

    print 'incrementing time since disturbance'
    time_since_disturbance = os.join(output_dir, 'time_since_last_disturbance_%s.tif' % (year - 1))
    time_since_disturbance = arcpy.Raster(time_since_disturbance)

    # increment time since disturbance
    time_since_disturbance += 1
    # time_since_disturbance.save(os.join(output_dir, 'time_since_last_disturbance_%s.tif' % year))

    print 'updating landcover'
    landcover = succession(time_since_disturbance)
    landcover.save(os.join(output_dir, 'landcover_%s.tif' % year))

    print 'counting ponds...'
    pond_count, region_group = count_ponds(landcover, year)
    print 'number of active ponds: %s' % pond_count

    if pond_count < CARRYING_CAPACITY:
        print 'number of active ponds is below carrying capacity, creating new ponds'
        # calculate number of new ponds to create
        new_ponds = CARRYING_CAPACITY - pond_count

        print 'calculating suitable points'
        # delete suitability_points before recalculating suitability
        if arcpy.Exists(suitability_points):
            arcpy.Delete_management(suitability_points)

        # calculate suitability using existing ponds
        calculate_suitability(landcover=landcover,
                              streams=suitable_streams,
                              suitability_points=suitability_points)

        # choose pond locations
        print 'selecting pond locations'

        if arcpy.Exists(pond_points):
            arcpy.Delete_management(pond_points)

        assign_pond_locations(constraint=suitability_points,
                              num_points=new_ponds)

        # convert pond points feature to list of longitude latitude coordinates
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

        # sum pond list
        ponds = arcpy.sa.Con(arcpy.sa.CellStatistics(pond_list, 'SUM') > 0, 1, 0)

        ponds.save(os.join(output_dir, 'ponds_%s.tif' % year))

        time_since_disturbance = update_time_since_disturbance(time_since_disturbance, ponds)

        time_since_disturbance.save(os.join(output_dir, 'time_since_last_disturbance_%s.tif' % year))

landcover = succession(time_since_disturbance)
landcover.save(os.join(output_dir, 'landcover_final.tif'))