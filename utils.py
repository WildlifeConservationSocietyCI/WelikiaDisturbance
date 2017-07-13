import os
import numpy as np
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
from osgeo import osr
import linecache
from wmi import WMI


def mkdir(path):
    if os.path.isdir(path) is False:
        os.mkdir(path)


def absoluteFilePaths(directory):
   for dirpath,_,filenames in os.walk(directory):
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

    shape = (header['nrows'], header['ncols'])

    return header, header_text, shape


def get_geo_info(FileName):
    sourceDS = gdal.Open(FileName, GA_ReadOnly)
    geoT = sourceDS.GetGeoTransform()
    projection = osr.SpatialReference()
    projection.ImportFromWkt(sourceDS.GetProjectionRef())
    return geoT, projection


def get_cell_size(FileName):
    geoT, projection = get_geo_info(FileName)
    return geoT[1]


def raster_to_array(in_raster, metadata=False, nodata_to_value=False):
    """
    convert raster to numpy array
    metadata flag returns geotransform and projection GDAL objects
    :type in_raster object
    """
    # print in_ascii
    src_ds = gdal.Open(in_raster, GA_ReadOnly)
    array = gdal_array.DatasetReadAsArray(src_ds)
    nodata = src_ds.GetRasterBand(1).GetNoDataValue()

    if nodata_to_value is not False:
        # print nodata
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

    # get array dimensions
    y_size, x_size = array.shape

    # map numpy dtype to GDAL dtype if default arg is used
    if dtype is None:
        dtype = gdal_array.NumericTypeCodeToGDALTypeCode(array.dtype)
        print(dtype)

    output_raster = gdal.GetDriverByName(driver).Create(out_raster, x_size, y_size, 1, dtype)

    # set coordinates
    output_raster.SetGeoTransform(geotransform)

    # set projection
    srs = osr.SpatialReference()
    epsg = int(projection.GetAttrValue("AUTHORITY", 1))
    srs.ImportFromEPSG(epsg)
    output_raster.SetProjection(srs.ExportToWkt())

    # write to array to raster
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
