__author__ = 'Jesse Moy'

'''
Calculates topographic exposure using grass.
Paths are hardcoded for use on Ash.
To adjust neighborhood radius and angle interval
edit azimuth and distance interval lists
product is as series of topex rasters one for each azimuth interval
The final topex raster must be summed manually
'''

import os
import sys
import subprocess

# START GRASS
# path to the GRASS GIS launch script
# MS Windows
grass7bin_win = r'C:/Program Files (x86)/GRASS GIS 7.0.2/grass70.bat'

# specify grass database directory
gisdb = "E:/grassdata"

# specify (existing) location and mapset
location = "topographic_exposure_300m"
mapset   = "user1"

# check operating system
if sys.platform.startswith('win'):
    grass7bin = grass7bin_win
else:
    raise OSError('Platform not configured.')

# query GRASS 7 itself for its GISBASE
startcmd = [grass7bin, '--config', 'path']

print startcmd
p = subprocess.Popen(startcmd, shell=False,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()
if p.returncode != 0:
    print >>sys.stderr, "ERROR: Cannot find GRASS GIS 7 start script (%s)" % startcmd
    sys.exit(-1)
gisbase = out.strip('\n\r')

# Set GISBASE environment variable
os.environ['GISBASE'] = gisbase

# the following not needed with trunk
os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')

#  add path to GRASS addons
home = os.path.expanduser("~")
os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')

# define GRASS-Python environment
gpydir = os.path.join(gisbase, "etc", "python")
sys.path.append(gpydir)

# Set GISDBASE environment variable
os.environ['GISDBASE'] = gisdb

# import GRASS Python bindings (see also pygrass)
import grass.script as gscript
import grass.script.setup as gsetup

# launch session
gsetup.init(gisbase,
            gisdb, location, mapset)

gscript.message('Current GRASS GIS 7 environment:')
print gscript.gisenv()

# list rasters in environment
gscript.message('Available raster maps:')
for rast in gscript.list_strings(type = 'rast'):
    print rast

# CALCULATE TOPOGRAPHIC EXPOSURE
import math

azimuths = range(0, 360, 30)

distance_intervals = range(20, 320, 20)

mapcalc_formula = {}

def get_position(interval, azimuth):
    value1 = int((math.cos(math.radians(azimuth)) * interval)/5)
    value2 = int((math.sin(math.radians(azimuth)) * interval)/5)
    return value1, value2

print distance_intervals
print azimuths

for a in azimuths:
    print 'topex_%s_%s_m_window = max(' % (a, max(distance_intervals))

for a in azimuths:
    print a
    mapcalc_formula[a] = 'topex_%s_%s_m_window = max(' % (a, max(distance_intervals))
    for i in distance_intervals:
        v1, v2 = get_position(i,a)
        if i == 300:
            mapcalc_formula[a] += ' atan((0.3048 * ((WELKIA_DEM_NO_BATHYMETRY_INT_5m[%r, %r] - WELKIA_DEM_NO_BATHYMETRY_INT_5m))) / (%r)))' % (v1, v2, i)
        else:
            mapcalc_formula[a] += ' atan((0.3048 * ((WELKIA_DEM_NO_BATHYMETRY_INT_5m[%r, %r] - WELKIA_DEM_NO_BATHYMETRY_INT_5m))) / (%r)),' % (v1, v2, i)

for a in mapcalc_formula:
    gscript.mapcalc(mapcalc_formula[a])
