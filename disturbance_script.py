import settings as s
import posixpath as os
# import pond
import fire

# assign s.ecocommunities to starting raster

for year in s.RUN_LENGTH:


    # horticulture

    # fire
    f = fire.FireDisturbance(year)

    f.get_translation_table()
    f.get_climate_years()
    f.get_drought()
    f.select_climate_records()
    f.set_weather_file()
    f.select_duration()
    f.run_farsite()

    # print f.translation_table
    # print f.climate_years
    # print f.drought


    # beaver pond
    # pond_dis = pond.PondDisturbance(year)
    # pond_dis.run_year()
