import os
import arcpy
import shutil
import settings as s

INPUT_DIR = os.path.join(s.ROOT_DIR, 'inputs')
OUTPUT_DIR = os.path.join(s.ROOT_DIR, 'outputs')

REGION_BOUNDARIES = os.path.join(s.ROOT_DIR, '_inputs_full_extent', 'nybbwi_14b_av', 'nybbwi.shp')

regions = []

cursor = arcpy.SearchCursor(REGION_BOUNDARIES)
for feature in cursor:
    region_code = int(feature.BoroCode)
    regions.append(region_code)

print regions

disturbance_types = ['fire', 'pond', 'garden']


def mkdir(path):
    if os.path.isdir(path) is False:
        os.mkdir(path)


# create input directory
mkdir(INPUT_DIR)

for i in disturbance_types:
    mkdir(os.path.join(INPUT_DIR, '%s' % i))

mkdir(os.path.join(INPUT_DIR, 'fire', 'spatial'))
mkdir(os.path.join(INPUT_DIR, 'fire', 'tabular'))
mkdir(os.path.join(INPUT_DIR, 'garden', 'spatial'))
mkdir(os.path.join(INPUT_DIR, 'garden', 'tabular'))

# create output directory
mkdir(OUTPUT_DIR)
for region in regions:
    mkdir(os.path.join(OUTPUT_DIR, '%s' % region))
    for i in disturbance_types:
        mkdir(os.path.join(OUTPUT_DIR, '%s' % region,'%s' % i))
        if i == 'fire':
            mkdir(os.path.join(OUTPUT_DIR, '%s' % region, '%s' % i, 'burn_rasters'))

for region in regions:
    mkdir(os.path.join(INPUT_DIR, 'fire', 'spatial', '%s' % region))
    mkdir(os.path.join(INPUT_DIR, 'garden', 'spatial', '%s' % region))
    mkdir(os.path.join(INPUT_DIR, 'pond', '%s' % region))

mkdir(os.path.join(s.ROOT_DIR, 'temp'))

# move files from full extent inputs