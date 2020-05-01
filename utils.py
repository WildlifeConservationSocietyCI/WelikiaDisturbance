import os
import errno
import shutil
import logging
import time
import re
import random
import arcpy
import numpy as np
# from osgeo import gdal
# from osgeo.gdalconst import *
# from osgeo import gdal_array
# from osgeo import osr
import linecache
# from wmi import WMI
import settings as s


# create dir (including parents if necessary) if it doesn't exist
def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# remove contents of dir (but not dir itself)
def clear_dir(directory, pattern=None, ignore_errors=True):
    if os.path.isdir(directory):
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            try:
                if os.path.isfile(path):
                    if pattern:
                        if re.search(pattern, filename):
                            os.remove(path)
                    else:
                        os.remove(path)
                if os.path.isdir(path):
                    shutil.rmtree(path)
            except:
                if ignore_errors:
                    pass


def set_arc_env(in_raster):
    arcpy.env.extent = in_raster
    arcpy.env.cellSize = in_raster
    arcpy.env.snapRaster = in_raster
    arcpy.env.mask = in_raster
    arcpy.env.outputCoordinateSystem = arcpy.Describe(in_raster).spatialReference
    arcpy.env.cartographicCoordinateSystem = arcpy.Describe(in_raster).spatialReference


def wait_for_lock(schema):
    while not arcpy.TestSchemaLock(schema):
        print('{} locked'.format(schema))
        time.sleep(1)
    print('{} not locked'.format(schema))
    return True


def absolute_file_paths(directory):
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))


def format_str(text):
    text = unicode(text).strip()
    text = text.replace(' ', '_')
    text = text.replace('-', '_')
    text = text.replace(u'\u2014', '')
    text = text.replace('(', '')
    text = text.replace(')', '')
    text = text.replace(':', '')
    text = text.replace('/', '')
    text = text.replace('_and_', '_')
    text = text.replace('_by_', '_')
    text = text.replace('_of_', '_')
    text = text.replace('_a_', '_')
    text = text.replace('_/_', '_')
    text = text.replace('___', '_')
    return text.encode('utf-8')


def get_ascii_header(ascii_raster):
    """
    :param ascii_raster:
    :return:
    """

    header_text = [linecache.getline(ascii_raster, i) for i in range(1, 7)]
    header = {}

    for line in header_text:
        attribute, value = line.split()
        header[attribute] = value

    header['ncols'] = int(header['ncols'])
    header['nrows'] = int(header['nrows'])
    header['cellsize'] = int(header['cellsize'])
    header['xllcorner'] = float(header['xllcorner'])
    header['yllcorner'] = float(header['yllcorner'])
    header['NODATA_value'] = int(header['NODATA_value'])

    shape = (header['nrows'], header['ncols'])

    return header, header_text, shape


# def get_geo_info(filename):
#     source_ds = gdal.Open(filename, GA_ReadOnly)
#     geo_t = source_ds.GetGeoTransform()
#     projection = osr.SpatialReference()
#     projection.ImportFromWkt(source_ds.GetProjectionRef())
#     return geo_t, projection


# def get_cell_size(filename):
#     geo_t, projection = get_geo_info(filename)
#     return geo_t[1]


# def raster_to_array(in_raster, metadata=False, nodata_to_value=False):
#     """
#     convert raster to numpy array
#     :type in_raster object
#     :param metadata flag returns geotransform and projection GDAL objects
#     :param nodata_to_value
#     """
#     src_ds = gdal.Open(in_raster, GA_ReadOnly)
#     array = gdal_array.DatasetReadAsArray(src_ds)
#     nodata = src_ds.GetRasterBand(1).GetNoDataValue()
#
#     if nodata_to_value is not False:
#         array[array == nodata] = nodata_to_value
#
#     if metadata is True:
#         geotransform, projection = get_geo_info(in_raster)
#         return array, geotransform, projection
#
#     else:
#         return array
#
#
# def array_to_raster(array, out_raster, geotransform, projection, driver='GTiff', dtype=None):
#     """
#     write numpy array to raster
#     :param array:
#     :param out_raster:
#     :param geotransform:
#     :param projection:
#     :param driver:
#     :param dtype:
#     :return:
#     """
#
#     y_size, x_size = array.shape
#
#     try:
#         dtype_info = np.iinfo(array.dtype)
#         nodata = dtype_info.min
#     except ValueError:
#         nodata = None
#
#     # logging.info('{} nodata: {}'.format(out_raster, nodata))
#
#     # map numpy dtype to GDAL dtype if default arg is used
#     if dtype is None:
#         dtype = gdal_array.NumericTypeCodeToGDALTypeCode(array.dtype)
#         # logging.info('gdal type: {}'.format(dtype))
#
#     output_raster = gdal.GetDriverByName(driver).Create(out_raster, x_size, y_size, 1, dtype)
#
#     # set coordinates
#     output_raster.SetGeoTransform(geotransform)
#
#     # set projection
#     srs = osr.SpatialReference()
#     epsg = int(projection.GetAttrValue("AUTHORITY", 1))
#     srs.ImportFromEPSG(epsg)
#     output_raster.SetProjection(srs.ExportToWkt())
#
#     # write to array to raster
#     if nodata is not None:
#         output_raster.GetRasterBand(1).SetNoDataValue(nodata)
#     output_raster.GetRasterBand(1).WriteArray(array)


def array_to_ascii(out_ascii_path, array, header, fmt="%4i"):
    """
    write numpy array to ascii raster
    :rtype: object
    """
    out_asc = open(out_ascii_path, 'w')
    for attribute in header:
        out_asc.write(attribute)

    np.savetxt(out_asc, array, fmt=fmt)
    out_asc.close()


def array_area(array, cell_size=1, nodata_value=None):
    # count = np.count_nonzero(~np.isnan(array))
    # TODO: this next line looks wrong -- (array != nodata_value) is a boolean. population_density not used anywhere.
    count = (array != nodata_value).sum()
    area = count * (cell_size ** 2)
    return area


def population_density(array, cell_size):
    area = array_area(array, cell_size)
    population = population_count(array)
    density = population / area
    return density


def non_zero_area(array, cell_size=1):
    count = np.count_nonzero(array)
    area = count * (cell_size ** 2)
    return area


def population_count(array):
    array = array[array > 0]
    population = np.sum(array)
    return population


def hist(a):
    if type(a) is np.ndarray:
        values, counts = np.unique(a, return_counts=True)
    else:
        values, counts = np.unique(arcpy.RasterToNumPyArray(a, nodata_to_value=-9999), return_counts=True)
    return dict(zip(values, counts))


def get_raster_area(in_raster, value):
    """
    return count of cells with given value in raster (e.g. # of garden cells in community raster)
    :return:
    """
    count = 0
    histogram = hist(in_raster)
    if value in histogram:
        count = histogram[value]

    return count


def smart_buffer(raster, raster_value, suitability, label, start_area=0, target_area=0):
    """
    Expand input raster using a suitability surface until it reaches target
    E.g.: Create a new garden, based on Mannahatta AML script.
    Note this does not "look ahead," but rather expands 1 cell at a time
    :return:
    """

    counter = 0
    raster_area = start_area
    while raster_area < target_area:
        zero = nullgard = zone = zapped = clip = ring_suitability = new_cells = None
        # self.wipe_locks()
        counter += 1
        if s.DEBUG_MODE:
            logging.info('%s smart_buffer %s counter: %s area: %s target: %s' %
                         (label, raster_value, counter, raster_area, target_area))

        # Set nodata values in garden grid to 0
        zero = arcpy.sa.Con(arcpy.sa.IsNull(raster) == 1, 0, raster)
        # if s.DEBUG_MODE:
        #     zero.save(os.path.join(s.TEMP_DIR, "zero_%s.tif" % counter))

        # Create another grid where current garden is NODATA and all other values = 0
        nullgard = arcpy.sa.SetNull(zero == raster_value, 0)
        # if s.DEBUG_MODE:
        #     nullgard.save(os.path.join(s.TEMP_DIR, "nullgard_%s.tif" % counter))

        # Expand potential garden grid by one cell
        zone = arcpy.sa.Expand(raster, 1, raster_value)
        # if s.DEBUG_MODE:
        #     zone.save(os.path.join(s.TEMP_DIR, "zone_%s.tif" % counter))

        # Create a clipping raster for gardens
        zapped = arcpy.sa.Plus(nullgard, suitability)
        # if s.DEBUG_MODE:
        #     zapped.save(os.path.join(s.TEMP_DIR, "zapped_%s.tif" % counter))

        # Clip expanded garden grid by removing unsuitable areas and places where garden currently exists
        clip = arcpy.sa.ExtractByMask(zone, zapped)
        array = arcpy.RasterToNumPyArray(clip)
        unique_values = np.unique(array, return_counts=True)
        value_dict = dict(zip(unique_values[0], unique_values[1]))
        if raster_value not in value_dict.keys():
            logging.info('no new cells can be added')
            break

        # if s.DEBUG_MODE:
        #     clip.save(os.path.join(s.TEMP_DIR, 'clip_%s.tif' % counter))

        ring_suitability = arcpy.sa.Con(clip, suitability)
        # if s.DEBUG_MODE:
        #     ring_suitability.save(os.path.join(s.TEMP_DIR, 'ring_suitability_%s.tif' % counter))

        new_cells = arcpy.sa.Con(ring_suitability == ring_suitability.maximum, raster_value)
        # if s.DEBUG_MODE:
        #     new_cells.save(os.path.join(s.TEMP_DIR, 'new_cells_%s.tif' % counter))

        new_cells_area = get_raster_area(new_cells, raster_value)

        if (new_cells_area + raster_area) <= target_area:
            raster = arcpy.sa.Con(zero == raster_value, raster_value,
                                  arcpy.sa.Con(new_cells == raster_value, raster_value, raster))

        else:
            randrast = arcpy.sa.CreateRandomRaster(345, suitability, suitability)
            random_cells = arcpy.sa.Con(new_cells, randrast)
            array = arcpy.RasterToNumPyArray(random_cells)
            random_values = np.unique(array).tolist()
            random.shuffle(random_values)

            while raster_area < target_area:
                r = random_values.pop()
                new_cell = arcpy.sa.Con(random_cells == r, raster_value)

                raster = arcpy.sa.Con(arcpy.sa.IsNull(new_cell) == 0, new_cell, raster)

                raster_area = get_raster_area(raster, raster_value)
                # if s.DEBUG_MODE:
                #     new_cell.save(os.path.join(s.TEMP_DIR, 'new_cell_%s.tif' % counter))

        raster_area = get_raster_area(raster, raster_value)
        del zero, zone, zapped, nullgard, clip, ring_suitability, new_cells
        # utils.clear_dir_by_pattern(s.TEMP_DIR, '.cpg')
        # utils.clear_dir_by_pattern(self.OUTPUT_DIR, '.cpg')
        # if s.DEBUG_MODE:
        #     logging.info('finished smart_buffer {}'.format(counter))

    return raster, raster_area
