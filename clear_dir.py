import os
import shutil
import settings as s

def clear_dir(directory):
    file_list = os.listdir(directory)
    for file_name in file_list:
        path = (os.path.join(directory, file_name))
        if os.path.isfile(path):
            os.remove(path)
        # if os.path.isdir(path):
        #     shutil.rmtree(path)

clear_dir(s.OUTPUT_DIR)
clear_dir(os.path.join(s.OUTPUT_DIR, 'garden'))