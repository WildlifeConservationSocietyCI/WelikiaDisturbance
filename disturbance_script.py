import settings as s
import posixpath as os
landcover = ''

for year in s.RUN_LENGTH:

    # horticulture

    # fire

    # beaver pond

    landcover.save(os.join(s.OUTPUT_DIR, 'landcover_%s.tif' % year))


