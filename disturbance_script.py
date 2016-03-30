import settings as s
import pond
import fire
import arcpy
# assign s.ecocommunities to starting raster

arcpy.env.extent = s.ecocommunities
arcpy.env.cellSize = s.ecocommunities
arcpy.env.snapRaster = s.ecocommunities
# arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(s.ecocommunities)

for year in s.RUN_LENGTH:


    # horticulture

    # fire
    fire_dis = fire.FireDisturbance(year)
    # f.climax_communities = f.ascii_to_array(f.EC_CLIMAX_ascii)
    # print f.climax_communities.shape
    fire_dis.run_year()
    # f.get_translation_table()
    # f.get_climate_years()
    # f.get_drought()
    # f.select_climate_records()
    # f.set_weather_file()
    # f.select_duration()
    # f.write_wnd()

    # print f.translation_table
    # print f.climate_years
    # print f.drought


    # beaver pond
    pond_dis = pond.PondDisturbance(year)
    pond_dis.run_year()
