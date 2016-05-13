import settings as s
import arcpy
import os
import logging
from arcpy import env

# Spatial Inputs

env.workspace = s.TEMP_DIR
env.scratchWorkspace = s.TEMP_DIR
env.overwriteOutput = True

INPUT_DIR = os.path.join(s.ROOT_DIR, '_inputs_full_extent')

DEM = os.path.join(s.ROOT_DIR, '_inputs_full_extent', 'dem.tif')
ECOSYSTEMS = os.path.join(s.ROOT_DIR, '_inputs_full_extent', 'ecocommunities.tif')
SITES = os.path.join(INPUT_DIR, 'GARDEN_SITES.shp')
REGION_BOUNDARIES = os.path.join(INPUT_DIR, 'nybbwi.shp')

# Tabular Inputs
PROXIMITY_RECLASS = os.path.join(s.INPUT_DIR, 'garden', 'tabular', 'proximity_reclass.csv')
SLOPE_RECLASS = os.path.join(s.INPUT_DIR, 'garden', 'tabular', 'slope_reclass2.csv')

GARDEN_SLOPE_SUITABILITY = os.path.join(INPUT_DIR, 'garden_slope_suitability.tif')
PROXIMITY_SUITABILITY = os.path.join(INPUT_DIR, 'proximity_suitability.tif')
STREAM_SUITABILITY = os.path.join(INPUT_DIR, 'stream_suitability.tif')
TRAILS = os.path.join(INPUT_DIR, 'fire_trails.tif')

# first order DEM derived inputs

# dem
logging.info('creating ascii dem')
# arcpy.RasterToASCII_conversion(DEM, os.path.join(INPUT_DIR, 'dem.asc'))

# slope
logging.info('creating ascii dem')
slope = arcpy.sa.Slope(DEM, output_measurement='DEGREE')
# arcpy.RasterToASCII_conversion(slope, os.path.join(INPUT_DIR, 'slope.asc'))

# aspect
logging.info('creating ascii dem')
aspect = arcpy.sa.Aspect(DEM)
# arcpy.RasterToASCII_conversion(slope, os.path.join(INPUT_DIR, 'aspect.asc'))

# flow direction
logging.info('creating ascii dem')
flow_direction = arcpy.sa.FlowDirection(DEM, force_flow='NORMAL')
# flow_direction.save(os.path.join(INPUT_DIR, 'flow_direction.tif'))

# second order DEM derived inputs

# garden slope suitability
logging.info('creating ascii dem')
garden_slope_suitability = arcpy.sa.ReclassByTable(in_raster=slope,
                                                   in_remap_table=SLOPE_RECLASS,
                                                   from_value_field='Field1',
                                                   to_value_field='Field2',
                                                   output_value_field='Field3')

logging.info('creating ascii dem')
# garden_slope_suitability.save(os.path.join(INPUT_DIR, 'garden_slope_suitability.tif'))

# stream suitability
logging.info('creating stream suitability')
stream_suitability = arcpy.sa.Con((ECOSYSTEMS == 616) &
                                  (slope <= 8), 1, 0)

# stream_suitability.save(os.path.join(INPUT_DIR, 'stream_suitability.tif'))

# Other
# proximity suitability
logging.info('creating proximity suitability')
euclidian_distance = arcpy.sa.EucDistance(SITES,
                                          maximum_distance=s.PROXIMITY_BUFFER,
                                          cell_size=s.CELL_SIZE)

proximity_suitability = arcpy.sa.ReclassByTable(euclidian_distance,
                                                in_remap_table=PROXIMITY_RECLASS,
                                                from_value_field='Field1',
                                                to_value_field='Field2',
                                                output_value_field='Field3')

# proximity_suitability.save(os.path.join(INPUT_DIR, 'proximity_suitability.tif'))

env.workspace = INPUT_DIR

rasters = arcpy.ListRasters()

print rasters
cursor = arcpy.SearchCursor(REGION_BOUNDARIES)

for feature in cursor:


    # arcpy.env.extent = feature
    print feature.BoroName
    boro_code = str(feature.BoroCode)
    print boro_code

    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'dem.asc')) is False:
        dem_clip = arcpy.Clip_management(in_raster=DEM,
                                         in_template_dataset=feature.Shape,
                                         clipping_geometry='ClippingGeometry')

        arcpy.RasterToASCII_conversion(dem_clip, os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'dem.asc'))

    dem_ref = os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'dem.asc')
    print dem_ref
    arcpy.env.extent = dem_ref
    arcpy.env.cellSize = dem_ref
    arcpy.env.snapRaster = dem_ref
    arcpy.env.mask = dem_ref
    arcpy.env.outputCoordinateSystem = arcpy.Describe(dem_ref).spatialReference
    arcpy.env.cartographicCoordinateSystem = arcpy.Describe(dem_ref).spatialReference

    ecocommunities = os.path.join(s.INPUT_DIR, '%s_ecocommunities.tif' % boro_code)
    if arcpy.Exists(ecocommunities) is False:

        ecocommunities_clip = arcpy.sa.Con(dem_ref, ECOSYSTEMS)

        ecocommunities_clip.save(ecocommunities)
        # arcpy.Clip_management(in_raster=ECOSYSTEMS,
        #                       out_raster=ecocommunities,
        #                       in_template_dataset=feature.Shape,
        #                       clipping_geometry='ClippingGeometry')

    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'fire_trails.asc')) is False:
        # trail_clip = arcpy.Clip_management(in_raster=TRAILS,
        #                                  in_template_dataset=feature.Shape,
        #                                  clipping_geometry='ClippingGeometry')
        #
        trail_clip = arcpy.sa.Con(dem_ref, TRAILS)

        arcpy.RasterToASCII_conversion(trail_clip, os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'fire_trails.asc'))

    dem = os.path.join(s.INPUT_DIR, 'pond', boro_code, 'dem.tif')
    if arcpy.Exists(dem) is False:
        # arcpy.Clip_management(in_raster=DEM,
        #                       out_raster=dem,
        #                       in_template_dataset=feature.Shape,
        #                       clipping_geometry='ClippingGeometry')
        dem_clip = arcpy.sa.Con(dem_ref, DEM)

        dem_clip.save(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'dem.tif'))

    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'slope.asc')) is False:
        # slope_clip = arcpy.Clip_management(in_raster=slope,
        #                                    in_template_dataset=feature.Shape,
        #                                    clipping_geometry='ClippingGeometry')

        slope_clip = arcpy.sa.Con(dem_ref, slope)

        arcpy.RasterToASCII_conversion(slope_clip, os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'slope.asc'))

    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'aspect.asc')) is False:
        # aspect_clip = arcpy.Clip_management(in_raster=aspect,
        #                                     in_template_dataset=feature.Shape,
        #                                     clipping_geometry='ClippingGeometry')

        aspect_clip = arcpy.sa.Con(dem_ref, aspect)

        arcpy.RasterToASCII_conversion(aspect_clip,
                                       os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'aspect.asc'))

    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'flow_direction.tif')) is False:
        # arcpy.Clip_management(in_raster=flow_direction,
        #                       out_raster=os.path.join(s.INPUT_DIR, 'pond', boro_code, 'flow_direction.tif'),
        #                       in_template_dataset=feature.Shape,
        #                       clipping_geometry='ClippingGeometry')

        flow_direction_clip = arcpy.sa.Con(dem_ref, flow_direction)

        flow_direction_clip.save(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'flow_direction.tif'))

    # garden_slope_suitability = os.path.join(s.INPUT_DIR, 'garden', boro_code, 'slope_suitability.tif')
    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'garden', boro_code, 'slope_suitability.tif')) is False:
        # arcpy.Clip_management(in_raster=GARDEN_SLOPE_SUITABILITY,
        #                       out_raster=garden_slope_suitability,
        #                       in_template_dataset=dem_ref)
        slope_suitability_clip = arcpy.sa.Con(dem_ref, garden_slope_suitability)

        slope_suitability_clip.save(os.path.join(s.INPUT_DIR, 'garden', 'spatial', boro_code, 'slope_suitability.tif'))


    # proximity_suitability = os.path.join(s.INPUT_DIR, 'garden', boro_code, 'proximity_suitability.tif')
    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'garden', 'spatial', boro_code, 'proximity_suitability.tif')) is False:
        # print 'clipping proximity suitability to %s' % feature.BoroName
        # arcpy.Clip_management(in_raster=PROXIMITY_SUITABILITY,
        #                       out_raster=proximity_suitability,
        #                       in_template_dataset=dem_ref,
        #                       )
        proximity_suitability_clip = arcpy.sa.Con(dem_ref, proximity_suitability)
        proximity_suitability_clip.save(os.path.join(s.INPUT_DIR, 'garden', boro_code, 'proximity_suitability.tif'))

    garden_sites = os.path.join(s.INPUT_DIR, 'garden', boro_code, 'garden_sites.shp')
    if arcpy.Exists(garden_sites) is False:
        arcpy.Clip_analysis(in_features=SITES,
                            clip_features=feature.Shape,
                            out_feature_class=garden_sites)

    # stream_suitability = os.path.join(s.INPUT_DIR, 'pond', boro_code, 'stream_suitability.tif')
    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'stream_suitability.tif')) is False:
        # arcpy.Clip_management(in_raster=STREAM_SUITABILITY,
        #                       in_template_dataset=feature.Shape,
        #                       out_raster=stream_suitability,
        #                       clipping_geometry='ClippingGeometry')
        stream_suitability_clip = arcpy.sa.Con(dem_ref, stream_suitability)

        stream_suitability_clip.save(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'stream_suitability.tif'))

    arcpy.env.extent = None
    arcpy.env.cellSize = None
    arcpy.env.snapRaster = None
    arcpy.env.mask = None
    arcpy.env.outputCoordinateSystem = None
    arcpy.env.cartographicCoordinateSystem = None