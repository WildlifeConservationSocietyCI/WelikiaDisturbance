import settings as s
import arcpy
import os
import logging

# Spatial Inputs
INPUT_DIR = os.path.join(s.ROOT_DIR, '_inputs_full_extent')

DEM = os.path.join(s.ROOT_DIR, '_inputs_full_extent', 'dem.tif')
ECOSYSTEMS = os.path.join(s.ROOT_DIR, '_inputs_full_extent', 'ecocommunities.tif')
SITES = os.path.join(INPUT_DIR, 'GARDEN_SITES.shp')
borough_boundaries = os.path.join(INPUT_DIR, 'nybbwi.shp')
BOROS = ['si', 'bx', 'm', 'bk', 'q']

# Tabular Inputs
PROXIMITY_RECLASS = os.path.join(s.INPUT_DIR, 'garden', 'proximity_reclass.csv')
SLOPE_RECLASS = os.path.join(s.INPUT_DIR, 'garden', 'slope_reclass2.csv')

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
garden_slope_suitability = arcpy.sa.ReclassByTable(slope,
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


cursor = arcpy.SearchCursor(borough_boundaries)

for feature in cursor:
    print feature.BoroName
    boro_code = str(feature.BoroCode)

    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'farsite', boro_code, 'dem.asc')) is False:
        dem_clip = arcpy.Clip_management(in_raster=DEM,
                                         in_template_dataset=feature.Shape,
                                         clipping_geometry='ClippingGeometry')

        arcpy.RasterToASCII_conversion(dem_clip, os.path.join(s.INPUT_DIR, 'fire', 'farsite', boro_code, 'dem.asc'))

    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'farsite', boro_code, 'slope.asc')) is False:
        slope_clip = arcpy.Clip_management(in_raster=slope,
                                           in_template_dataset=feature.Shape,
                                           clipping_geometry='ClippingGeometry')

        arcpy.RasterToASCII_conversion(slope_clip, )

    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'farsite', boro_code, 'aspect.asc')) is False:
        aspect_clip = arcpy.Clip_management(in_raster=aspect,
                                            in_template_dataset=feature.Shape,
                                            clipping_geometry='ClippingGeometry')

        arcpy.RasterToASCII_conversion(aspect_clip, os.path.join(s.INPUT_DIR, 'fire', 'farsite', boro_code, 'aspect.asc'))

    if arcpy.Exists(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'flow_direction.tif')) is False:
        flow_direction_clip = arcpy.Clip_management(in_raster=flow_direction,
                                                    out_raster=os.path.join(s.INPUT_DIR, 'pond', boro_code, 'flow_direction.tif'),
                                                    in_template_dataset=feature.Shape,
                                                    clipping_geometry='ClippingGeometry')

        # flow_direction_clip.save(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'flow_direction.tif'))

    if arcpy.Exists(os.path.join(INPUT_DIR, 'garden', boro_code, 'garden_slope_suitability.tif')) is False:
        garden_slope_suitability_clip = arcpy.Clip_management(in_raster=garden_slope_suitability,
                                                              out_raster= os.path.join(INPUT_DIR, 'garden', boro_code, 'garden_slope_suitability.tif'),
                                                              in_template_dataset=feature.Shape,
                                                              clipping_geometry='ClippingGeometry')

        # garden_slope_suitability_clip.save(os.path.join(INPUT_DIR, 'garden', boro_code, 'garden_slope_suitability.tif'))

    if arcpy.Exists(os.path.join(INPUT_DIR, 'pond', boro_code, 'stream_suitability.tif')) is False:
        stream_suitability_clip = arcpy.Clip_management(in_raster=stream_suitability,
                                                        out_raster=os.path.join(INPUT_DIR, 'pond', boro_code, 'stream_suitability.tif'),
                                                              in_template_dataset=feature.Shape,
                                                              clipping_geometry='ClippingGeometry')

        # stream_suitability_clip.save(os.path.join(INPUT_DIR, 'pond', boro_code, 'stream_suitability.tif'))

    if arcpy.Exists(os.path.join(INPUT_DIR, 'garden', boro_code, 'proximity_suitability.tif')) is False:
        proximity_suitability_clip = arcpy.Clip_management(in_raster=proximity_suitability,
                                                           out_raster=os.path.join(INPUT_DIR, 'garden', boro_code, 'proximity_suitability.tif'),
                                                              in_template_dataset=feature.Shape,
                                                              clipping_geometry='ClippingGeometry')

        # proximity_suitability_clip.save(os.path.join(INPUT_DIR, 'garden', boro_code, 'proximity_suitability.tif'))
