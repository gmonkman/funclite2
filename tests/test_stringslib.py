# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument, unused-variable

"""unit tests for features"""
import unittest


from inspect import getsourcefile as _getsourcefile
import os.path as _path
import funclite2.iolib as iolib

import funclite2.stringslib as stringslib


class Test(unittest.TestCase):
    """unittest for keypoints"""

    def setUp(self):
        """setup variables etc for use in test cases
        """
        self.pth = iolib.get_file_parts2(_path.abspath(_getsourcefile(lambda: 0)))[0]
        self.modpath = _path.normpath(self.pth)



    #@unittest.skip("Temporaily disabled while debugging")
    def test_filteralphanumeric1(self):
        """testfunc"""
        s = 'EVERY FRIDAY - FOURPENCE \nPrinted & published at Newspaper House, Broadway. Peterborougli \n'
        out = stringslib.filter_alphanumeric1(s, remove_single_quote=True, remove_double_quote=True, allow_cr=False, allow_lf=False).strip()
        print(out)

    def test_numbersinstring(self):
        s = '\n12.23'
        out = stringslib.numbers_in_str(s)  # noqa
        s = 'aas 12.23 sdf 12 sf 1'
        out = stringslib.numbers_in_str(s, int)  # noqa

if __name__ == '__main__':
    unittest.main(verbosity=2)





