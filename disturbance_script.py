import settings as s
import posixpath as os
import pond
import fire

# assign s.ecocommunities to starting raster

for year in s.RUN_LENGTH:


    # horticulture

    # fire

    # beaver pond
    pond.run(year)



f = fire.FireDisturbance()

f.get_translation_table()
f.get_climate_years()
f.get_drought()

print f.translation_table
print f.climate_years
print f.drought