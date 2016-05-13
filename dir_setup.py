import os


ROOT_DIR = os.path.join('C:\\', 'Users', 'Jesse Moy','Documents', 'WelikiaDisturbance')
INPUT_DIR = os.path.join(ROOT_DIR, 'inputs')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs')

regions = [1, 2, 3, 4]
dis = ['fire', 'pond', 'garden']


def mkdir(path):
    if os.path.isdir(path) is False:
        os.mkdir(path)

mkdir(INPUT_DIR)

for i in dis:
    mkdir(os.path.join(INPUT_DIR, '%s' % i))

mkdir(os.path.join(INPUT_DIR, 'fire', 'farsite'))
mkdir(os.path.join(INPUT_DIR, 'fire', 'script'))

mkdir(OUTPUT_DIR)

for i in dis:
    mkdir(os.path.join(OUTPUT_DIR, '%s' % i))

for region in regions:
    mkdir(os.path.join(INPUT_DIR, 'fire', 'farsite', '%s' % region))
    mkdir(os.path.join(INPUT_DIR, 'fire', 'script', '%s' % region))
    mkdir(os.path.join(INPUT_DIR, 'garden', '%s' % region))
    mkdir(os.path.join(INPUT_DIR, 'pond', '%s' % region))
