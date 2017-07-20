import settings as s
import arcpy
import os
import logging
from arcpy import env
import sys

# ArcGIS Extensions

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to get spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)

# Spatial Inputs

env.workspace = s.TEMP_DIR
env.scratchWorkspace = s.TEMP_DIR
env.overwriteOutput = True

INPUT_DIR = os.path.join(s.ROOT_DIR, '_inputs_full_extent')

DEM = os.path.join(s.ROOT_DIR, '_inputs_full_extent', 'dem', 'WELIKIA_DEM_5m_BURNED_STREAMS_10ft_CLIP.tif')
ECOSYSTEMS = os.path.join(s.ROOT_DIR, '_inputs_full_extent', 'Welikia_Ecocommunities', 'Welikia_Ecocommunities_int.tif')
SITES = os.path.join(INPUT_DIR, 'garden_sites', 'GARDEN_SITES.shp')
BUFFER = os.path.join(INPUT_DIR, 'garden_sites', 'SITE_BUFFER.shp')
TRAILS = os.path.join(INPUT_DIR, 'trails', 'fire_trails.asc')
HUNTING = os.path.join(INPUT_DIR, 'hunting_sites', 'hunting_sites.asc')
REGION_BOUNDARIES = os.path.join(INPUT_DIR, 'region_boundaries', 'disturbance_regions.shp')

# Tabular Inputs
PROXIMITY_RECLASS = os.path.join(s.INPUT_DIR, 'garden', 'tabular', 'proximity_reclass.txt')
SLOPE_RECLASS = os.path.join(s.INPUT_DIR, 'garden', 'tabular', 'slope_reclass.txt')

GARDEN_SLOPE_SUITABILITY = os.path.join(INPUT_DIR, 'slope_suitability.tif')
PROXIMITY_SUITABILITY = os.path.join(INPUT_DIR, 'proximity_suitability.tif')
STREAM_SUITABILITY = os.path.join(INPUT_DIR, 'stream_suitability.tif')


def set_arc_env(in_raster):
    arcpy.env.extent = in_raster
    arcpy.env.cellSize = in_raster
    arcpy.env.snapRaster = in_raster
    arcpy.env.mask = in_raster
    arcpy.env.outputCoordinateSystem = arcpy.Describe(in_raster).spatialReference
    arcpy.env.cartographicCoordinateSystem = arcpy.Describe(in_raster).spatialReference


def reset_arc_env():
    arcpy.env.extent = None
    arcpy.env.cellSize = None
    arcpy.env.snapRaster = None
    arcpy.env.mask = None
    arcpy.env.outputCoordinateSystem = None
    arcpy.env.cartographicCoordinateSystem = None

# create full extent products
set_arc_env(DEM)

# dem
if arcpy.Exists(os.path.join(INPUT_DIR, 'dem.asc')) is False:
    logging.info('creating ascii dem')
    arcpy.RasterToASCII_conversion(DEM, os.path.join(INPUT_DIR, 'dem.asc'))

if arcpy.Exists(os.path.join(INPUT_DIR, 'ecocommunities.tif')) is False:
    logging.info('creating communities')
    ecocommunities_fe = arcpy.Raster(ECOSYSTEMS)
    lenape_sites = arcpy.PolygonToRaster_conversion(in_features=BUFFER,
                                                    value_field='RASTERVALU',
                                                    cellsize=s.CELL_SIZE)
    ecocommunities_fe = arcpy.sa.Con((ecocommunities_fe), arcpy.sa.Con((arcpy.sa.IsNull(lenape_sites) == 0), 65400, ecocommunities_fe))

    ecocommunities_fe.save(os.path.join(INPUT_DIR, 'ecocommunities.tif'))

else:
    ecocommunities_fe = os.path.join(INPUT_DIR, 'ecocommunities.tif')

# slope
if arcpy.Exists(os.path.join(INPUT_DIR, 'slope.asc')) is False:
    logging.info('creating ascii slope')
    slope = arcpy.sa.Slope(DEM, output_measurement='DEGREE')
    slope.save(os.path.join(INPUT_DIR, 'slope.tif'))
    arcpy.RasterToASCII_conversion(slope, os.path.join(INPUT_DIR, 'slope.asc'))
else:
    slope = arcpy.Raster(os.path.join(INPUT_DIR, 'slope.asc'))

# aspect
if arcpy.Exists(os.path.join(INPUT_DIR, 'aspect.asc')) is False:
    logging.info('creating ascii aspect')
    aspect = arcpy.sa.Aspect(DEM)
    arcpy.RasterToASCII_conversion(aspect, os.path.join(INPUT_DIR, 'aspect.asc'))
else:
    aspect = arcpy.Raster(os.path.join(INPUT_DIR, 'aspect.asc'))

# flow direction
if arcpy.Exists(os.path.join(INPUT_DIR, 'flow_direction.tif')) is False:
    logging.info('creating flow direction raster')
    flow_direction = arcpy.sa.FlowDirection(DEM, force_flow='NORMAL')
    flow_direction.save(os.path.join(INPUT_DIR, 'flow_direction.tif'))
else:
    flow_direction = arcpy.Raster(os.path.join(INPUT_DIR, 'flow_direction.tif'))

# garden slope suitability
if arcpy.Exists(os.path.join(INPUT_DIR, 'slope_suitability.tif')) is False:
    logging.info('creating slope suitability raster')
    slope_suitability = arcpy.sa.ReclassByTable(in_raster=slope,
                                                in_remap_table=SLOPE_RECLASS,
                                                from_value_field='Field1',
                                                to_value_field='Field2',
                                                output_value_field='Field4')

    slope_suitability.save(os.path.join(INPUT_DIR, 'slope_suitability.tif'))
else:
    slope_suitability = arcpy.Raster(os.path.join(INPUT_DIR, 'slope_suitability.tif'))

# stream suitability
if arcpy.Exists(os.path.join(INPUT_DIR, 'stream_suitability.tif')) is False:
    ECOSYSTEMS = arcpy.Raster(ECOSYSTEMS)

    logging.info('creating stream suitability')
    stream_suitability = arcpy.sa.Con((ECOSYSTEMS == 61801) |
                                      (ECOSYSTEMS == 61802) |
                                      (ECOSYSTEMS == 61803) |
                                      (ECOSYSTEMS == 61804) |
                                      (ECOSYSTEMS == 62000) |
                                      (ECOSYSTEMS == 61701) |
                                      (ECOSYSTEMS == 61702) &
                                      (slope <= 8), 1, 0)

    stream_suitability.save(os.path.join(INPUT_DIR, 'stream_suitability.tif'))
else:
    stream_suitability = arcpy.Raster(os.path.join(INPUT_DIR, 'stream_suitability.tif'))

# proximity suitability
if arcpy.Exists(os.path.join(INPUT_DIR, 'proximity_suitability.tif')) is False:
    logging.info('creating proximity suitability')
    euclidian_distance = arcpy.sa.EucDistance(SITES,
                                              maximum_distance=s.PROXIMITY_BUFFER,
                                              cell_size=s.CELL_SIZE)

    proximity_suitability = arcpy.sa.ReclassByTable(euclidian_distance,
                                                    in_remap_table=PROXIMITY_RECLASS,
                                                    from_value_field='Field1',
                                                    to_value_field='Field2',
                                                    output_value_field='Field4')

    proximity_suitability.save(os.path.join(INPUT_DIR, 'proximity_suitability.tif'))
else:
    proximity_suitability = arcpy.Raster(os.path.join(INPUT_DIR, 'proximity_suitability.tif'))

env.workspace = INPUT_DIR

rasters = arcpy.ListRasters()

print rasters
cursor = arcpy.SearchCursor(REGION_BOUNDARIES)

for feature in cursor:
        reset_arc_env()
        print feature.BoroName
        boro_code = str(int(feature.BoroCode))

        ecocommunities = os.path.join(s.INPUT_DIR, '%s_ecocommunities_int.tif' % boro_code)
        if arcpy.Exists(ecocommunities) is False:
            arcpy.Clip_management(in_raster=ecocommunities_fe,
                                  out_raster=ecocommunities,
                                  in_template_dataset=feature.Shape,
                                  clipping_geometry='ClippingGeometry')

            # ecocommunities_clip.save(ecocommunities)

        # set environment
        arcpy.env.extent = ecocommunities
        # arcpy.env.mask = ecocommunities
        # set_arc_env(ecocommunities)


        # FIRE INPUTS
        arcpy.env.cellSize = s.FARSITE_RESOLUTION

        if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'dem.asc')) is False:
            dem_clip = arcpy.sa.ExtractByMask(DEM, ecocommunities)
            dem_temp = os.path.join(s.TEMP_DIR, "dem.tif")
            arcpy.Resample_management(dem_clip, dem_temp, s.FARSITE_RESOLUTION, "BILINEAR")

            arcpy.RasterToASCII_conversion(dem_temp, os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'dem.asc'))

        if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'slope.asc')) is False:
            slope_clip = arcpy.sa.ExtractByMask(slope, ecocommunities)
            slope_temp = os.path.join(s.TEMP_DIR, "slope.tif")
            arcpy.Resample_management(slope_clip, slope_temp, s.FARSITE_RESOLUTION, "BILINEAR")

            arcpy.RasterToASCII_conversion(slope_temp, os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'slope.asc'))

        if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'aspect.asc')) is False:
            aspect_clip = arcpy.sa.ExtractByMask(aspect, ecocommunities)
            aspect_temp = os.path.join(s.TEMP_DIR, "aspect.tif")
            arcpy.Resample_management(aspect_clip, aspect_temp, s.FARSITE_RESOLUTION, "BILINEAR")

            arcpy.RasterToASCII_conversion(aspect_temp, os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'aspect.asc'))

        arcpy.cellSize = ecocommunities

        if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'fire_trails.asc')) is False:

            trail_clip = arcpy.sa.Con(ecocommunities, TRAILS)

            arcpy.RasterToASCII_conversion(trail_clip, os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'fire_trails.asc'))

        if arcpy.Exists(os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'hunting_sites.asc')) is False:

            trail_clip = arcpy.sa.Con(ecocommunities, HUNTING)

            arcpy.RasterToASCII_conversion(trail_clip, os.path.join(s.INPUT_DIR, 'fire', 'spatial', boro_code, 'hunting_sites.asc'))

        # POND INPUTS
        if arcpy.Exists(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'dem.tif')) is False:
            dem_clip = arcpy.sa.ExtractByMask(DEM, ecocommunities)
            dem_clip.save(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'dem.tif'))

        if arcpy.Exists(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'flow_direction.tif')) is False:

            flow_direction_clip = arcpy.sa.Con(ecocommunities, flow_direction)

            flow_direction_clip.save(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'flow_direction.tif'))

        # stream_suitability = os.path.join(s.INPUT_DIR, 'pond', boro_code, 'stream_suitability.tif')
        if arcpy.Exists(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'stream_suitability.tif')) is False:

            stream_suitability_clip = arcpy.sa.Con(ecocommunities, stream_suitability)

            stream_suitability_clip.save(os.path.join(s.INPUT_DIR, 'pond', boro_code, 'stream_suitability.tif'))

        # slope_suitability = os.path.join(s.INPUT_DIR, 'garden', boro_code, 'slope_suitability.tif')
        if arcpy.Exists(os.path.join(s.INPUT_DIR, 'garden', boro_code, 'slope_suitability.tif')) is False:

            slope_suitability_clip = arcpy.sa.Con(ecocommunities, slope_suitability)

            slope_suitability_clip.save(os.path.join(s.INPUT_DIR, 'garden', 'spatial', boro_code, 'slope_suitability.tif'))

        # GARDEN INPUTS
        # proximity_suitability = os.path.join(s.INPUT_DIR, 'garden', boro_code, 'proximity_suitability.tif')
        prx_path = os.path.join(s.INPUT_DIR, 'garden', 'spatial', boro_code, 'proximity_suitability.tif')
        if arcpy.Exists([prx_path]) is False:

            proximity_suitability_clip = arcpy.sa.Con(ecocommunities, proximity_suitability)

            proximity_suitability_clip.save(prx_path)

        garden_sites = os.path.join(s.INPUT_DIR, 'garden', 'spatial', boro_code, 'garden_sites.shp')
        if arcpy.Exists(garden_sites) is False:
            arcpy.Clip_analysis(in_features=SITES,
                                clip_features=feature.Shape,
                                out_feature_class=garden_sites)

        # reset env for next region
        reset_arc_env()