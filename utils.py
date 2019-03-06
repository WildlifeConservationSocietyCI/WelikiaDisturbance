import os
import errno
import shutil
import logging
import time
import re
import arcpy
import numpy as np
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
from osgeo import osr
import linecache
# from wmi import WMI


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
def clear_dir(directory):
    if os.path.isdir(directory):
        file_list = os.listdir(directory)
        for file_name in file_list:
            path = os.path.join(directory, file_name)
            if os.path.isfile(path):
                os.remove(path)
            if os.path.isdir(path):
                shutil.rmtree(path)


def clear_dir_by_pattern(directory, pattern):
    for f in os.listdir(directory):
        if re.search(pattern, f):
            os.remove(os.path.join(directory, f))


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
    print(header_text)

    for line in header_text:
        attribute, value = line.split()
        header[attribute] = value

    header['ncols'] = int(header['ncols'])
    header['nrows'] = int(header['nrows'])
    header['cellsize'] = int(header['cellsize'])
    header['xllcorner'] = float(header['xllcorner'])
    header['yllcorner'] = float(header['yllcorner'])

    shape = (header['nrows'], header['ncols'])

    return header, header_text, shape


def get_geo_info(filename):
    source_ds = gdal.Open(filename, GA_ReadOnly)
    geo_t = source_ds.GetGeoTransform()
    projection = osr.SpatialReference()
    projection.ImportFromWkt(source_ds.GetProjectionRef())
    return geo_t, projection


def get_cell_size(filename):
    geo_t, projection = get_geo_info(filename)
    return geo_t[1]


def raster_to_array(in_raster, metadata=False, nodata_to_value=False):
    """
    convert raster to numpy array
    :type in_raster object
    :param metadata flag returns geotransform and projection GDAL objects
    :param nodata_to_value
    """
    src_ds = gdal.Open(in_raster, GA_ReadOnly)
    array = gdal_array.DatasetReadAsArray(src_ds)
    nodata = src_ds.GetRasterBand(1).GetNoDataValue()

    if nodata_to_value is not False:
        array[array == nodata] = nodata_to_value

    if metadata is True:
        geotransform, projection = get_geo_info(in_raster)
        return array, geotransform, projection

    else:
        return array


def array_to_raster(array, out_raster, geotransform, projection, driver='GTiff', dtype=None):
    """
    write numpy array to raster
    :param array:
    :param out_raster:
    :param geotransform:
    :param projection:
    :param driver:
    :param dtype:
    :return:
    """

    y_size, x_size = array.shape

    try:
        dtype_info = np.iinfo(array.dtype)
        nodata = dtype_info.min
    except ValueError:
        nodata = None

    # logging.info('{} nodata: {}'.format(out_raster, nodata))

    # map numpy dtype to GDAL dtype if default arg is used
    if dtype is None:
        dtype = gdal_array.NumericTypeCodeToGDALTypeCode(array.dtype)
        # logging.info('gdal type: {}'.format(dtype))

    output_raster = gdal.GetDriverByName(driver).Create(out_raster, x_size, y_size, 1, dtype)

    # set coordinates
    output_raster.SetGeoTransform(geotransform)

    # set projection
    srs = osr.SpatialReference()
    epsg = int(projection.GetAttrValue("AUTHORITY", 1))
    srs.ImportFromEPSG(epsg)
    output_raster.SetProjection(srs.ExportToWkt())

    # write to array to raster
    if nodata is not None:
        output_raster.GetRasterBand(1).SetNoDataValue(nodata)
    output_raster.GetRasterBand(1).WriteArray(array)


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
