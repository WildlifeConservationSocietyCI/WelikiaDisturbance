__author__ = "Jesse Moy"

'''
population.py assigns population sizes from a total pool to a set of points
'''

import arcpy
import numpy as np

TOTAL_POPULATION = 2000

candidate_sites = ('E:/_data/welikia/WelikiaDisturbance/population/SUITABILITY_GARDENING/GARDENING_SITES.shp')

fields = ["RASTERVALU", "population"]

print
cursor = arcpy.UpdateCursor(candidate_sites)

# population distribution
population_size_distribution = np.random.normal(loc=50,
                                                scale=10,
                                                size=100)


def assign_population(total, distribution):
    site_pop = int(np.random.choice(population_size_distribution))
    if (total - site_pop) > 0:
        return site_pop

# candidate_sites = range(0, 40, 1)
#
# site_populations = {}
#
# for site in candidate_sites:
#     site_pop = assign_population(TOTAL_POPULATION, population_size_distribution)
#     site_populations[site] = site_pop
#     TOTAL_POPULATION -= site_pop
#
# t = 0
# for s in site_populations:
#     t += site_populations[s]
#     # print s, site_populations[s]

for site in cursor:
    suitability = site.getValue(fields[0])
    if suitability == 1 or suitability == 2:
        site_pop = assign_population(TOTAL_POPULATION, population_size_distribution)
        # row[fields[1]] = site_pop
        site.setValue(fields[1], site_pop)
        cursor.updateRow(site)
        TOTAL_POPULATION -= site_pop


print TOTAL_POPULATION