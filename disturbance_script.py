import settings as s
import posixpath as os
import pond
import fire

# assign s.ecocommunities to starting raster

for year in s.RUN_LENGTH:


    # horticulture

    # fire

    # beaver pond
    pond_dis = pond.PondDisturbance(year)
    pond_dis.run_year()

#
# pond_dis = pond.PondDisturbance(2)
# print pond_dis.time_since_disturbance
# pond_dis.succession()
# pond_dis.ecocommunities.save(os.join(pond_dis.OUTPUT_DIR, pond_dis._ecocommunities_filename % pond_dis.year))
# f = fire.FireDisturbance()
#
# f.get_translation_table()
# f.get_climate_years()
# f.get_drought()
#
# print f.translation_table
# print f.climate_years
# print f.drought