import os
import arcpy

ROOT_DIR = os.path.join('D:\\', '_data', 'Welikia', 'WelikiaDisturbance')
INPUT_DIR = os.path.join(ROOT_DIR, 'inputs')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs')

REGION_BOUNDARIES = os.path.join(ROOT_DIR, '_inputs_full_extent', 'nybbwi.shp')

regions = []

cursor = arcpy.SearchCursor(REGION_BOUNDARIES)
for feature in cursor:
    region_code = feature.BoroCode
    regions.append(region_code)

print regions

disturbance_types = ['fire', 'pond', 'garden']


def mkdir(path):
    if os.path.isdir(path) is False:
        os.mkdir(path)

mkdir(INPUT_DIR)

for i in disturbance_types:
    mkdir(os.path.join(INPUT_DIR, '%s' % i))

mkdir(os.path.join(INPUT_DIR, 'fire', 'spatial'))
mkdir(os.path.join(INPUT_DIR, 'fire', 'tabular'))
mkdir(os.path.join(INPUT_DIR, 'garden', 'spatial'))
mkdir(os.path.join(INPUT_DIR, 'garden', 'tabular'))

mkdir(OUTPUT_DIR)

for i in disturbance_types:
    mkdir(os.path.join(OUTPUT_DIR, '%s' % i))

for region in regions:
    mkdir(os.path.join(INPUT_DIR, 'fire', 'spatial', '%s' % region))
    mkdir(os.path.join(INPUT_DIR, 'garden', 'spatial', '%s' % region))
    mkdir(os.path.join(INPUT_DIR, 'pond', '%s' % region))
