import arcpy
import numpy as np
import sys

# Environment Setting
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.AddMessage("Checking out Spatial")
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Unable to get spatial analyst extension")
    arcpy.AddMessage(arcpy.GetMessages(0))
    sys.exit(0)

arcpy.env.overwriteOutput = True

candidate_sites = r'F:\_data\Welikia\WelikiaDisturbance\_inputs_full_extent\garden_sites\GARDEN_SITES.shp'

TOTAL_POPULATION = 2000
NUM_SITES = float(arcpy.GetCount_management(candidate_sites).getOutput(0))
MEAN = TOTAL_POPULATION / NUM_SITES
MIN = 15
MAX = 70
REQUIRED_AREA = 40

#
# population distribution
population_size_distribution = np.random.normal(loc=MEAN,
                                                scale=10,
                                                size=10000)

# truncate distribution using minimum and maximum population sizes
population_size_distribution = [i for i in population_size_distribution if MIN < i < MAX]


def assign_population(total, distribution):
    site_pop = int(np.random.choice(population_size_distribution))
    if (total - site_pop) > 0:
        return site_pop


fields = ["RASTERVALU", "population"]
cursor = arcpy.UpdateCursor(candidate_sites)

# select start pop from normal distribution around mean
for site in cursor:
    suitability = site.getValue(fields[0])
    if suitability == 1:
        site_pop = assign_population(TOTAL_POPULATION, population_size_distribution)
        print site_pop
        site.setValue(fields[1], site_pop)
        cursor.updateRow(site)
        TOTAL_POPULATION -= site_pop
print 'remaining total: %s' % TOTAL_POPULATION


# allocate remaining individuals uniformly
while TOTAL_POPULATION != 0:

    fields = ["RASTERVALU", "population"]
    cursor = arcpy.UpdateCursor(candidate_sites)

    for site in cursor:
        if TOTAL_POPULATION > 0:
            pop = site.getValue(fields[1])
            print pop
            print pop + 1
            site.setValue(fields[1], (pop + 1))
            cursor.updateRow(site)
            TOTAL_POPULATION -= 1
        else:
            break
    print "total population: %s" % TOTAL_POPULATION


# calculate buffer distance based on area requirement
fields = ["RASTERVALU", "population", 'buffer']
cursor = arcpy.UpdateCursor(candidate_sites)

for site in cursor:
    site_pop = site.getValue(fields[1])
    buffer = int(np.sqrt(site_pop * REQUIRED_AREA / np.pi) + 0.5)
    site.setValue(fields[2], buffer)
    cursor.updateRow(site)

site_polygon = arcpy.Buffer_analysis(in_features=candidate_sites,
                                     out_feature_class=r'F:\_data\Welikia\WelikiaDisturbance\_inputs_full_extent\garden_sites\SITE_BUFFER.shp',
                                     buffer_distance_or_field=('buffer')
                                     )