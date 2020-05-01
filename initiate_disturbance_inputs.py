# initiate_disturbance_inputs: regenerate disturbance scenario directory and inputs
# If running new scenario and want to preserve existing: change REGION/TRIAL_NAME and run this
# If running existing scenario and have changed input data or paths, do NOT change REGION/TRIAL_NAME, just run this
# If running existing scenario and have changed only scenario settings, don't run this

import os
import sys
import shutil
import logging
import random
import arcpy
import settings as s
import utils

logging.basicConfig(filename=s.LOGFILE,
                    filemode='w',
                    format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S')

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to get spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)

arcpy.env.workspace = s.TEMP_DIR
arcpy.env.scratchWorkspace = s.TEMP_DIR
arcpy.env.overwriteOutput = True
utils.set_arc_env(s.ECOCOMMUNITIES_FE)

utils.clear_dir(s.TRIAL_DIR)
utils.mkdir(os.path.join(s.INPUT_DIR, 'fire'))
utils.mkdir(os.path.join(s.INPUT_DIR, 'garden'))
utils.mkdir(os.path.join(s.INPUT_DIR, 'pond'))
utils.clear_dir(s.TEMP_DIR)
utils.mkdir(s.TEMP_DIR)


ecocommunities_fe = arcpy.Raster(s.ECOCOMMUNITIES_FE)

logging.info('creating full extent dem')
dem = arcpy.sa.ExtractByMask(s.DEM_FE, ecocommunities_fe)
dem.save(os.path.join(s.TEMP_DIR, 'dem.tif'))

logging.info('calculating full extent slope')
slope = arcpy.sa.Slope(dem, output_measurement='DEGREE')
slope.save(os.path.join(s.TEMP_DIR, 'slope.tif'))

logging.info('creating full extent aspect')
aspect = arcpy.sa.Aspect(dem)
slope.save(os.path.join(s.TEMP_DIR, 'aspect.tif'))

logging.info('creating full extent flow direction raster')
flow_direction = arcpy.sa.FlowDirection(dem, force_flow='NORMAL')
flow_direction.save(os.path.join(s.TEMP_DIR, 'flow_direction.tif'))

logging.info('creating full extent slope suitability raster')
slope_suitability = arcpy.sa.ReclassByTable(in_raster=slope,
                                            in_remap_table=s.SLOPE_RECLASS,
                                            from_value_field='FROM_',
                                            to_value_field='TO',
                                            output_value_field='OUT')
slope_suitability.save(os.path.join(s.TEMP_DIR, 'slope_suitability.tif'))

logging.info('creating full extent stream suitability')
stream_suitability = arcpy.sa.Con((ecocommunities_fe == 61801) |
                                  (ecocommunities_fe == 61802) |
                                  (ecocommunities_fe == 61803) |
                                  (ecocommunities_fe == 61804) |
                                  (ecocommunities_fe == 62000) |
                                  (ecocommunities_fe == 61701) |
                                  (ecocommunities_fe == 61702) &
                                  (slope <= 8), 1, 0)
stream_suitability.save(os.path.join(s.TEMP_DIR, 'stream_suitability.tif'))

logging.info('creating full extent proximity suitability')
euclidian_distance = arcpy.sa.EucDistance(s.GARDEN_SITES_FE,
                                          maximum_distance=s.PROXIMITY_BUFFER,
                                          cell_size=s.CELL_SIZE)
proximity_suitability = arcpy.sa.ReclassByTable(euclidian_distance,
                                                in_remap_table=s.PROXIMITY_RECLASS,
                                                from_value_field='FROM_',
                                                to_value_field='TO',
                                                output_value_field='OUT')
proximity_suitability.save(os.path.join(s.TEMP_DIR, 'proximity_suitability.tif'))

habsites_path = os.path.join(s.TEMP_DIR, 'habsites.tif')
if not arcpy.Exists(habsites_path):
    logging.info('creating full extent upland suitability raster')
    upland_suitability = arcpy.sa.ReclassByTable(ecocommunities_fe, s.COMMUNITY_TABLE,
                                                 from_value_field='Field1',
                                                 to_value_field='Field1',
                                                 output_value_field='upland',
                                                 missing_values='NODATA')
    upland_suitability.save(os.path.join(s.TEMP_DIR, 'upland_suitability.tif'))
    habitation_suitability = arcpy.sa.Con(upland_suitability > 0, (upland_suitability +
                                                                   slope_suitability))
    habitation_suitability.save(os.path.join(s.TEMP_DIR, 'habitation_suitability.tif'))

    logging.info('calculating Lenape habitation sites')
    point_cursor = arcpy.da.SearchCursor(s.HABITATION_SITES_FE, ["FID", "Population"])
    point_layer = arcpy.MakeFeatureLayer_management(s.HABITATION_SITES_FE, "habsite_layer")
    hab_buffer = os.path.join(s.TEMP_DIR, 'hab_buffer.shp')
    habsite_rasters = []
    for point in point_cursor:
        pointid = point[0]
        population = point[1] or 0
        if s.DEBUG_MODE:
            logging.info("Calculating site %s pop %s" % (pointid, population))
        arcpy.env.extent = ecocommunities_fe
        # thisisabsurd = random.randint(0, 1000000)
        var = random.choice(s.POPULATION_VARIATION)
        site_area_target = int((population + var) * s.PER_CAPITA_SITE_AREA / (s.CELL_SIZE ** 2))
        arcpy.SelectLayerByAttribute_management("habsite_layer", "NEW_SELECTION", ' "FID" = {}'.format(pointid))

        if arcpy.Exists(hab_buffer):
            arcpy.Delete_management(hab_buffer)
        arcpy.Buffer_analysis(in_features="habsite_layer",
                              out_feature_class=hab_buffer,
                              buffer_distance_or_field=s.PROXIMITY_BUFFER)
        arcpy.env.extent = hab_buffer

        habsite_center = os.path.join(s.TEMP_DIR, 'habsite_center_{}.tif'.format(pointid))
        arcpy.PointToRaster_conversion(in_features="habsite_layer",
                                       value_field='FID',
                                       out_rasterdataset=habsite_center,
                                       cellsize=s.CELL_SIZE)
        habsite = arcpy.Raster(habsite_center)
        habsite_siteid = arcpy.sa.Con(habsite == pointid, s.LENAPE_SITE_ID, habsite)
        # habsite_siteid.save(os.path.join(s.TEMP_DIR, "habsite_prebuffer_{}_{}.tif".format(pointid, thisisabsurd)))
        habsite_area_start = utils.get_raster_area(habsite_siteid, s.LENAPE_SITE_ID)
        habsite_buffered, habsite_area = utils.smart_buffer(
            habsite_siteid,
            s.LENAPE_SITE_ID,
            habitation_suitability,
            "site",
            habsite_area_start,
            site_area_target,
        )
        # arcpy.env.extent = ecocommunities_fe
        # arcpy.Mosaic_management([habsite_buffered], ecocommunities_fe)
        # habsite_rasters.append(habsite_buffered)
        # ecocommunities_fe = arcpy.sa.Con(ecocommunities_fe,
        #                                  arcpy.sa.Con(arcpy.sa.IsNull(habsite_buffered) == 0, habsite_buffered,
        #                                               ecocommunities_fe))
        # time.sleep(1)
        habsite_path = os.path.join(s.TEMP_DIR, "habsite_{}.tif".format(pointid))
        habsite_buffered.save(habsite_path)
        habsite_rasters.append(habsite_path)
        del habsite, habsite_center, habsite_buffered

    arcpy.env.extent = ecocommunities_fe
    arcpy.MosaicToNewRaster_management(habsite_rasters, s.TEMP_DIR, 'habsites.tif', number_of_bands=1, pixel_type="1_BIT")
    utils.clear_dir(s.TEMP_DIR, r"habsite_\S*")

habsites = arcpy.Raster(habsites_path)
ecocommunities_fe = arcpy.sa.Con(
    arcpy.sa.IsNull(habsites) == 1,
    ecocommunities_fe,
    arcpy.sa.Con(habsites == 1, s.LENAPE_SITE_ID, ecocommunities_fe)
)
# Correcting for weird 0/nodata banding in preceding. Relies on no eco id = 0.
ecocommunities_fe = arcpy.sa.SetNull(ecocommunities_fe, ecocommunities_fe, "VALUE = 0")
ecocommunities_fe.save(os.path.join(s.TEMP_DIR, 'ecocommunities_fe.tif'))

# TODO: tweak site point locations based on how they creep upslope (?)
# TODO: check that the altered ecocommunities_fe doesn't result in
#  points from garden_sites.shp overlapping habitation sites
# TODO: does this logic mean we lose cells if two site centers start out close to each other?
# TODO: reinstate real ecocommunities
# TODO: check garden disturbance still works


arcpy.MakeFeatureLayer_management(s.REGION_BOUNDARIES, "regionlyr")
arcpy.SelectLayerByAttribute_management("regionlyr", where_clause=' "BoroCode" = {} '.format(s.REGION))
cursor = arcpy.SearchCursor(s.REGION_BOUNDARIES)
for feature in cursor:
    region = int(feature.BoroCode)
    if region == s.REGION:
        arcpy.env.extent = None
        logging.info('region name: {}'.format(feature.BoroName))

        # OVERALL INPUTS
        logging.info('creating region {} overall inputs'.format(region))

        arcpy.Clip_management(in_raster=ecocommunities_fe,
                              out_raster=s.ecocommunities,
                              in_template_dataset=feature.Shape,
                              clipping_geometry='ClippingGeometry')

        utils.set_arc_env(s.ecocommunities)

        # FIRE INPUTS
        logging.info('creating region {} fire inputs'.format(region))
        # set resolution for FARSITE inputs
        arcpy.env.cellSize = s.FARSITE_RESOLUTION

        dem_clip = arcpy.sa.ExtractByMask(dem, s.ecocommunities)
        dem_temp = os.path.join(s.TEMP_DIR, "dem_farsite.tif")
        arcpy.Resample_management(dem_clip, dem_temp, s.FARSITE_RESOLUTION, "BILINEAR")
        arcpy.RasterToASCII_conversion(dem_temp, s.dem_ascii)

        # create reference ascii raster for region (extent, cell size, shape)
        ref = arcpy.sa.SetNull(arcpy.sa.IsNull(dem_temp) == 0, dem_temp)
        arcpy.RasterToASCII_conversion(ref, s.reference_ascii)
        slope_clip = arcpy.sa.ExtractByMask(slope, s.ecocommunities)
        slope_temp = os.path.join(s.TEMP_DIR, "slope_farsite.tif")
        arcpy.Resample_management(slope_clip, slope_temp, s.FARSITE_RESOLUTION, "BILINEAR")
        arcpy.RasterToASCII_conversion(slope_temp, s.slope_ascii)

        aspect_clip = arcpy.sa.ExtractByMask(aspect, s.ecocommunities)
        aspect_temp = os.path.join(s.TEMP_DIR, "aspect_farsite.tif")
        arcpy.Resample_management(aspect_clip, aspect_temp, s.FARSITE_RESOLUTION, "BILINEAR")
        arcpy.RasterToASCII_conversion(aspect_temp, s.aspect_ascii)

        # Copy custom fire files from inputs_full_extent to input fire directory.
        files = [
            os.path.join(s.INPUT_DIR_FULL, 'tables', 'fire', 'custom_fuel.fmd'),
            os.path.join(s.INPUT_DIR_FULL, 'tables', 'fire', 'fuel_adjustment.adj'),
            os.path.join(s.INPUT_DIR_FULL, 'tables', 'fire', 'fuel_moisture.fms'),
            os.path.join(s.INPUT_DIR_FULL, 'tables', 'fire', 'weather.wtr'),
            os.path.join(s.INPUT_DIR_FULL, 'tables', 'fire', 'wind.wnd')
        ]
        for f in files:
            shutil.copy(f, s.FIRE_DIR)

        # Rename dem.asc to fuel.asc and canopy.asc. Header will now have the appropriate data for specified region.
        shutil.copyfile(s.dem_ascii, s.fuel_ascii)
        shutil.copyfile(s.dem_ascii, s.canopy_ascii)

        # set cell resolution back to reference raster
        # trails and hunting sites will be converted to a point shapefile, therefore full resolution is needed
        arcpy.env.cellSize = s.ecocommunities

        trail_clip = arcpy.sa.ExtractByMask(s.TRAILS_FE, s.ecocommunities)
        trail_clip.save(s.trails)

        hunting_sites_clip = arcpy.sa.ExtractByMask(s.HUNTING_FE, s.ecocommunities)
        hunting_sites_clip.save(s.hunting_sites)

        # POND INPUTS
        logging.info('creating region {} pond inputs'.format(region))

        dem_clip = arcpy.sa.ExtractByMask(dem, s.ecocommunities)
        dem_clip.save(s.dem)

        flow_direction_clip = arcpy.sa.ExtractByMask(flow_direction, s.ecocommunities)
        flow_direction_clip.save(s.flow_direction)

        stream_suitability_clip = arcpy.sa.ExtractByMask(stream_suitability, s.ecocommunities)
        stream_suitability_clip.save(s.stream_suitability)

        # GARDEN INPUTS
        logging.info('creating region {} garden inputs'.format(region))

        slope_suitability_clip = arcpy.sa.ExtractByMask(slope_suitability, s.ecocommunities)
        slope_suitability_clip.save(s.slope_suitability)

        proximity_suitability_clip = arcpy.sa.ExtractByMask(proximity_suitability, s.ecocommunities)
        proximity_suitability_clip.save(s.proximity_suitability)

        arcpy.Clip_analysis(in_features=s.GARDEN_SITES_FE,
                            clip_features=feature.Shape,
                            out_feature_class=s.garden_sites)
