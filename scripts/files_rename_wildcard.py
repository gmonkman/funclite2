# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument
"""rename files
"""

import os.path as path
import funclite2.iolib as iolib
import os


import argparse

def getname(d, f, find, replace):
    s = f.replace(find, replace)
    return path.normpath('%s/%s' % (d, s))

def main():
    """main"""
    cmdline = argparse.ArgumentParser(description=__doc__)  # use the module __doc__

    # positional: e.g. scipt.py c:/temp
    # args.folder == 'c:/temp'
    cmdline.add_argument('folder', help='folder')

    # named: eg script.py -part head
    cmdline.add_argument('-match', '--match', help='filename to contain this string', required=False)

    # named: eg script.py -part head
    cmdline.add_argument('-replace', '--replace', help='The text to replace', required=True)

    # named: eg script.py -part head
    cmdline.add_argument('-new', '--new', help='The new text', required=True)
    args = cmdline.parse_args()

    files = []
    new_names = []
    fld = path.normpath(args.folder)
    for d, f, e, ffn in iolib.file_list_generator_dfe(fld, None, recurse=False):
        if args.match:
            if args.match in f:
                files.append(ffn)
                new_names.append(getname(d, f, args.replace, args.new))
        else:
            files.append(ffn)
            new_names.append(getname(d, f, args.replace, args.new))

    PP = iolib.PrintProgress(iter_=files)

    for idx, fname in enumerate(files):
        # directory basename
        os.rename(fname, new_names[idx])
        PP.increment()
    print('Done, renamed %s files.' % (PP.iteration - 1))


if __name__ == '__main__':
    main()
