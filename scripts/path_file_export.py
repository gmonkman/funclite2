"""
Export full directories and files from a root path to a defined csv file.

Notes:
    The root directory is always included in file searches, ignoring wild_dirs

Examples:
    path_file_export C:\temp C:\temp\results.csv -wild_dirs report,paper -wild_files land_use,landuse -extensions .pdf,.doc,docx

"""
# Some command line args for testing etc
# C:/temp C:/temp/path_file_export.csv -wild_dirs hefs,images,pdfs -wild_files nrw,perm,all -extensions .csv,.pdf,.jpg

import argparse
from os import path

import funclite2.iolib as iolib

def _is_match(s, lst):
    """wildcards match our string (string is filename, dir etc"""
    if not lst: return True
    return any([itm.lower() in s.lower() for itm in lst])


def main():
    """main"""
    cmdline = argparse.ArgumentParser(description=__doc__)  # use the module __doc__
    cmdline.add_argument('root', help='root folder to search')
    cmdline.add_argument('outfile', help='output file name')

    f = lambda s: [str(item) for item in s.split(',')]
    cmdline.add_argument('-wild_dirs', '--wild_dirs', type=f, help='comma delimited list of wildcard directory names to match - case insensitive, eg -extensions report,paper', required=False)
    cmdline.add_argument('-wild_files', '--wild_files', type=f, help='comma delimited list of wildcard filenames to match - case insensitive, eg -extensions report,paper', required=False)
    cmdline.add_argument('-extensions', '--extensions', type=f, help='comma delimited list of dotted extensions to match - case insensitive, eg -extensions .jpg,.gif', required=False)
    args = cmdline.parse_args()

    wild_dirs = args.wild_dirs if args.wild_dirs else []
    wild_files = args.wild_files if args.wild_files else []
    extensions = args.extensions if args.extensions else []

    # flds = '\n'.join([path.normpath(f) for f in iolib.folder_generator(args.root])
    flds = [path.normpath(f) for f in iolib.folder_generator(args.root) if not wild_dirs or _is_match(f, wild_dirs)]  # here we filter for wild_dirs
    flds = [path.normpath(args.root), *flds]

    PP = iolib.PrintProgress(maximum=len(flds), init_msg='Walking the directory structure....')
    i = 0
    out = []
    header = 'fld', 'depth', 'file_name', 'ext', 'fqn'
    curfld = ''
    for fld, nm, ext, fqn in iolib.file_list_generator_dfe(flds, wildcards=extensions, recurse=False):  # here we filter for extensions
        # matches wild_files?
        if not _is_match(nm, wild_files):
            if not curfld == fld:
                PP.increment()
                curfld = fld
            continue

        out.append([fld, fld.count('\\'), nm, ext, fqn])
        i += 1

        if not curfld == fld:
            PP.increment()
            curfld = fld

    iolib.writecsv(args.outfile, out, header, inner_as_rows=False)
    print('Done. Found %s matches' % i)
    print('Exported to %s' % args.outfile)


if __name__ == "__main__":
    main()
