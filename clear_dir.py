import os
import shutil
import settings as s


def clear_dir(directory):
    file_list = os.listdir(directory)
    for file_name in file_list:
        path = os.path.join(directory, file_name)
        if os.path.isfile(path):
            os.remove(path)
        # if os.path.isdir(path):
        #     shutil.rmtree(path)

clear_dir(s.OUTPUT_DIR)
clear_dir(os.path.join(s.OUTPUT_DIR, 'garden'))
clear_dir(os.path.join(s.OUTPUT_DIR, 'fire'))
clear_dir(os.path.join(s.OUTPUT_DIR, 'fire', 'burn_rasters'))
clear_dir(os.path.join(s.OUTPUT_DIR, 'pond'))

# remove canopy, forest age, fuel and time since disturbance from the input dir
rasters = ['canopy.asc', 'forest_age.tif', 'fuel.asc', 'time_since_disturbance.tif']
for i in rasters:
    path = os.path.join(s.INPUT_DIR_REGION, 'fire', 'spatial', s.REGION, i)
    if os.path.isfile(path):
        os.remove(path)
