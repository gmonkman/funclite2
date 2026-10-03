# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument
"""rename files with their folder name
"""

import os.path as path
import funclite2.iolib as iolib
import os

ROOT = 'C:/Users/gramon/OneDrive - UKCEH/Desktop/INSPIRE'


for d, f, e, ffn in iolib.file_list_generator_dfe(ROOT, '*.gml', recurse=True):
    bn = '%s%s' % (path.basename(d), e)
    fnew = path.normpath('%s/%s' % (d, bn))
    os.rename(ffn, fnew)

print('Done')