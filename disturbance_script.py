import settings as s
import os
import pond
import fire
import garden
import arcpy
import shutil

# assign s.ecocommunities to starting raster
arcpy.env.extent = s.ecocommunities
arcpy.env.cellSize = s.ecocommunities
arcpy.env.snapRaster = s.ecocommunities
arcpy.env.outputCoordinateSystem = arcpy.Describe(s.ecocommunities).spatialReference
arcpy.env.cartographicCoordinateSystem = arcpy.Describe(s.ecocommunities).spatialReference
print arcpy.Describe(s.ecocommunities).spatialReference
print arcpy.env.outputCoordinateSystem


def clear_dir(directory):

    file_list = os.listdir(directory)
    for file_name in file_list:
        path = (os.path.join(directory, file_name))
        if os.path.isfile(path):
            os.remove(path)
        if os.path.isdir(path):
            shutil.rmtree(path)

clear_dir(os.path.join(s.INPUT_DIR, 'fire', 'script', 'burn_rasters'))

clear_dir(s.TEMP_DIR)


for year in s.RUN_LENGTH:

    print'___________YEAR: %s' % year

    # horticulture

    # fire
    fire_dis = fire.FireDisturbance(year)
    fire_dis.run_year()

    # garden
    garden_dis = garden.GardenDisturbance(year)
    garden_dis.run_year()

    # beaver pond
    pond_dis = pond.PondDisturbance(year)
    pond_dis.run_year()


