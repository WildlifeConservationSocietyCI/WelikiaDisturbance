import os
import arcpy
import settings as s
import errno

REGION_BOUNDARIES = os.path.join(s.INPUT_DIR_FULL, 'region_boundaries', 'disturbance_regions.shp')
disturbance_types = ['fire', 'pond', 'garden']

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

for i in disturbance_types:
    mkdir(os.path.join(s.INPUT_DIR_REGION, '%s' % i))

mkdir(os.path.join(s.INPUT_DIR_REGION, 'fire', 'spatial'))
mkdir(os.path.join(s.INPUT_DIR_REGION, 'fire', 'tabular'))
mkdir(os.path.join(s.INPUT_DIR_REGION, 'garden', 'spatial'))
mkdir(os.path.join(s.INPUT_DIR_REGION, 'garden', 'tabular'))
mkdir(os.path.join(s.INPUT_DIR_REGION, 'pond'))

# create output directory, creates folders in outputs labeled "burn_rasters"
for i in disturbance_types:
    mkdir(os.path.join(s.OUTPUT_DIR, '%s' % i))
    if i == 'fire':
        mkdir(os.path.join(s.OUTPUT_DIR, '%s' % i, 'burn_rasters'))

mkdir(os.path.join(s.ROOT_DIR, 'temp'))
