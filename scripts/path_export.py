# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument
__doc__ = ('Export full directories from a root path to a defined csv file.\n'
           'path_export.py <root> <output>\n'
           'Args\n'
           'root: root folder to walk\n'
           'output: output file\n'
           'Example:\n'
           'path_export C:\temp C:\temp\results.csv'
           )

import argparse
from os import path
import funclite2.iolib as iolib


def main():
    """main"""
    cmdline = argparse.ArgumentParser(description=__doc__)  # use the module __doc__
    cmdline.add_argument('root', help='root folder to search')
    cmdline.add_argument('outfile', help='output file name')
    args = cmdline.parse_args()


    # flds = '\n'.join([path.normpath(f) for f in iolib.folder_generator(args.root])
    flds = "\n".join(['%s,%s' % (path.normpath(f), f.count('\\')) for f in iolib.folder_generator(args.root)])

    iolib.write_to_file(flds, open_in_npp=False, full_file_path=args.outfile)
    print('Done. Exported to %s' % args.outfile)



if __name__ == "__main__":
    main()
