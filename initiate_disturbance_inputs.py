import settings as s
import arcpy
import pandas as pd
import numpy as np
import os
import logging
from arcpy import env
import sys
import utils

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
ECOCOMMUNITIES = os.path.join(s.ROOT_DIR, '_inputs_full_extent', 'Welikia_Ecocommunities', 'Welikia_Ecocommunities_int.tif')
SITES = os.path.join(INPUT_DIR, 'garden_sites', 'GARDEN_SITES.shp')
BUFFER = os.path.join(INPUT_DIR, 'garden_sites', 'SITE_BUFFER.shp')
TRAILS = os.path.join(INPUT_DIR, 'trails', 'fire_trails.tif')
HUNTING = os.path.join(INPUT_DIR, 'hunting_sites', 'hunting_sites.tif')
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
set_arc_env(ECOCOMMUNITIES)

if arcpy.Exists(os.path.join(INPUT_DIR, 'ecocommunities.tif')) is False:
    logging.info('creating communities')
    ecocommunities_fe = arcpy.Raster(ECOCOMMUNITIES)
    lenape_sites = arcpy.PolygonToRaster_conversion(in_features=BUFFER,
                                                    value_field='RASTERVALU',
                                                    cellsize=s.CELL_SIZE)
    ecocommunities_fe = arcpy.sa.Con((ecocommunities_fe), arcpy.sa.Con((arcpy.sa.IsNull(lenape_sites) == 0), 65400, ecocommunities_fe))

    ecocommunities_fe.save(os.path.join(INPUT_DIR, 'ecocommunities.tif'))

else:
    ecocommunities_fe = os.path.join(INPUT_DIR, 'ecocommunities.tif')

# dem
if arcpy.Exists(os.path.join(INPUT_DIR, 'dem.tif')) is False:
    logging.info('creating ascii dem')
    dem = arcpy.sa.ExtractByMask(DEM, ECOCOMMUNITIES)
    dem.save(os.path.join(INPUT_DIR, 'dem.tif'))
else:
    dem = arcpy.Raster(os.path.join(INPUT_DIR, 'dem.tif'))

# slope
if arcpy.Exists(os.path.join(INPUT_DIR, 'slope.tif')) is False:
    logging.info('calculating slope')
    slope = arcpy.sa.Slope(dem, output_measurement='DEGREE')
    slope.save(os.path.join(INPUT_DIR, 'slope.tif'))
else:
    slope = arcpy.Raster(os.path.join(INPUT_DIR, 'slope.tif'))

# aspect
if arcpy.Exists(os.path.join(INPUT_DIR, 'aspect.tif')) is False:
    logging.info('creating ascii aspect')
    aspect = arcpy.sa.Aspect(dem)
    slope.save(os.path.join(INPUT_DIR, 'aspect.tif'))
else:
    aspect = arcpy.Raster(os.path.join(INPUT_DIR, 'aspect.tif'))

# flow direction
if arcpy.Exists(os.path.join(INPUT_DIR, 'flow_direction.tif')) is False:
    logging.info('creating flow direction raster')
    flow_direction = arcpy.sa.FlowDirection(dem, force_flow='NORMAL')
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
    ECOCOMMUNITIES = arcpy.Raster(ECOCOMMUNITIES)

    logging.info('creating stream suitability')
    stream_suitability = arcpy.sa.Con((ECOCOMMUNITIES == 61801) |
                                      (ECOCOMMUNITIES == 61802) |
                                      (ECOCOMMUNITIES == 61803) |
                                      (ECOCOMMUNITIES == 61804) |
                                      (ECOCOMMUNITIES == 62000) |
                                      (ECOCOMMUNITIES == 61701) |
                                      (ECOCOMMUNITIES == 61702) &
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

arcpy.env.workspace = INPUT_DIR

rasters = arcpy.ListRasters()

print rasters
cursor = arcpy.SearchCursor(REGION_BOUNDARIES)

for feature in cursor:
        arcpy.env.extent = None
        arcpy.env.snapRaster = s.ecocommunities
        print feature.BoroName
        region = str(int(feature.BoroCode))

        #  region output paths
        ecocommunities = os.path.join(s.INPUT_DIR, '%s_ecocommunities_int.tif' % region)
        reference_raster_region = os.path.join(s.INPUT_DIR, 'reference_grid_%s.tif' % region)
        reference_ascii_region = os.path.join(s.INPUT_DIR, 'reference_grid_%s.asc' % region)
        dem_ascii_region = os.path.join(s.INPUT_DIR, 'fire', 'spatial', region, 'dem.asc')
        aspect_ascii_region = os.path.join(s.INPUT_DIR, 'fire', 'spatial', region, 'aspect.asc')
        slope_ascii_region = os.path.join(s.INPUT_DIR, 'fire', 'spatial', region, 'slope.asc')
        trails_region = os.path.join(s.INPUT_DIR, 'fire', 'spatial', region, 'trails.tif')
        hunting_sites_region = os.path.join(s.INPUT_DIR, 'fire', 'spatial', region, 'hunting_sites.tif')

        dem_region = os.path.join(s.INPUT_DIR, 'pond', region, 'dem.tif')
        flow_direction_region = os.path.join(s.INPUT_DIR, 'pond', region, 'flow_direction.tif')
        stream_suitability_region = os.path.join(s.INPUT_DIR, 'pond', region, 'stream_suitability.tif')

        slope_suitability_region = os.path.join(s.INPUT_DIR, 'garden', 'spatial', region, 'slope_suitability.tif')
        proximity_suitability_region = os.path.join(s.INPUT_DIR, 'garden', 'spatial', region, 'proximity_suitability.tif')
        garden_sites_region = os.path.join(s.INPUT_DIR, 'garden', 'spatial', region, 'garden_sites.shp')


        if arcpy.Exists(ecocommunities) is False:
            arcpy.Clip_management(in_raster=ecocommunities_fe,
                                  out_raster=ecocommunities,
                                  in_template_dataset=feature.Shape,
                                  clipping_geometry='ClippingGeometry')

        # set environment extent
        if arcpy.Exists(reference_raster_region) is False:
            # create reference raster (GeoTif) for region (extent, cellsize, shape)
            ref = arcpy.sa.SetNull(arcpy.sa.IsNull(ecocommunities) == 0, ecocommunities)
            ref.save(reference_raster_region)

        arcpy.env.extent = reference_raster_region

        # FIRE INPUTS

        # set resolution for FARSITE inputs
        arcpy.env.cellSize = s.FARSITE_RESOLUTION

        if arcpy.Exists(dem_ascii_region) is False:
            dem_clip = arcpy.sa.ExtractByMask(dem, ecocommunities)
            dem_temp = os.path.join(s.TEMP_DIR, "dem.tif")
            arcpy.Resample_management(dem_clip, dem_temp, s.FARSITE_RESOLUTION, "BILINEAR")
            arcpy.RasterToASCII_conversion(dem_temp, dem_ascii_region)

        # create reference ascii raster for region (extent, cell size, shape)
        if arcpy.Exists(reference_ascii_region) is False:
            dem_temp = os.path.join(s.TEMP_DIR, "dem.tif")
            ref = arcpy.sa.SetNull(arcpy.sa.IsNull(dem_temp) == 0, dem_temp)
            arcpy.RasterToASCII_conversion(ref, reference_ascii_region)

        if arcpy.Exists(slope_ascii_region) is False:
            slope_clip = arcpy.sa.ExtractByMask(slope, ecocommunities)
            slope_temp = os.path.join(s.TEMP_DIR, "slope.tif")
            arcpy.Resample_management(slope_clip, slope_temp, s.FARSITE_RESOLUTION, "BILINEAR")
            arcpy.RasterToASCII_conversion(slope_temp, slope_ascii_region)

        if arcpy.Exists(aspect_ascii_region) is False:
            aspect_clip = arcpy.sa.ExtractByMask(aspect, ecocommunities)
            aspect_temp = os.path.join(s.TEMP_DIR, "aspect.tif")
            arcpy.Resample_management(aspect_clip, aspect_temp, s.FARSITE_RESOLUTION, "BILINEAR")
            arcpy.RasterToASCII_conversion(aspect_temp, aspect_ascii_region)

        # rest cell resolution to reference raster
        arcpy.env.cellSize = reference_raster_region

        if arcpy.Exists(trails_region) is False:
            trail_clip = arcpy.sa.ExtractByMask(TRAILS, ecocommunities)
            trail_clip.save(trails_region)

        if arcpy.Exists(hunting_sites_region) is False:
            hunting_sites_clip = arcpy.sa.ExtractByMask(HUNTING, ecocommunities)
            hunting_sites_clip.save(hunting_sites_region)

        # POND INPUTS

        if arcpy.Exists(dem_region) is False:
            dem_clip = arcpy.sa.ExtractByMask(dem, ecocommunities)
            dem_clip.save(dem_region)

        if arcpy.Exists(flow_direction_region) is False:
            flow_direction_clip = arcpy.sa.ExtractByMask(flow_direction, ecocommunities)
            flow_direction_clip.save(flow_direction_region)

        if arcpy.Exists(stream_suitability_region) is False:
            stream_suitability_clip = arcpy.sa.ExtractByMask(stream_suitability, ecocommunities)
            stream_suitability_clip.save(stream_suitability_region)

        # GARDEN INPUTS

        if arcpy.Exists(slope_suitability_region) is False:
            slope_suitability_clip = arcpy.sa.ExtractByMask(slope_suitability, ecocommunities)
            slope_suitability_clip.save(slope_suitability_region)


        if arcpy.Exists(proximity_suitability_region) is False:
            proximity_suitability_clip = arcpy.sa.ExtractByMask(proximity_suitability, ecocommunities)
            proximity_suitability_clip.save(proximity_suitability_region)


        if arcpy.Exists(garden_sites_region) is False:
            arcpy.Clip_analysis(in_features=SITES,
                                clip_features=feature.Shape,
                                out_feature_class=garden_sites_region)

