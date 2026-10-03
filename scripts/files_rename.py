# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument
"""rename files
"""

import os.path as path
import funclite2.iolib as iolib
import os

# ROOT = 'S:/Quality Assurance/Laboratories/Graham/CSW21_NetZero_Chemical cores'



def get_name_netzero(fname):
    if len(fname) > 21: return fname
    n = fname.replace('NETZ_', '')
    n = n.replace('.JPG', '')
    n = n.replace('_', '')
    n = n.replace(' ', '')
    s = 'CSW21 %s.JPG' % n
    return s


def get_cs21(fname):
    n = fname.replace('UKSC_', '')
    n = n.replace('.JPG', '')
    n = n.replace(' ', '')
    s = 'CS21 %s.JPG' % n
    return s


def oneoff():
    root = 'S:/Quality Assurance/Laboratories/Graham/CS21 Chemical cores'
    rename_in_place = True

    i = sum([1 for _ in iolib.file_list_generator_dfe(root, '*.JPG', recurse=False)])
    PP = iolib.PrintProgress(i)

    for d, f, e, ffn in iolib.file_list_generator_dfe(root, '*.JPG', recurse=False):
        # directory basename
        renamed_fld = path.normpath('%s/renamed' % d)
        iolib.create_folder(renamed_fld)

        # bn = '%s%s' % (path.basename(d), e)

        if 'NetZero' in root:
            new_file_name = get_name_netzero(f)
        elif 'CS21' in root:
            new_file_name = get_cs21(f)
        else:
            raise ValueError

        fnew = path.normpath('%s/%s' % (renamed_fld, new_file_name))

        if rename_in_place:
            os.rename(ffn, fnew)
        else:
            if iolib.file_exists(fnew):
                raise ValueError('%s exists' % fnew)
            iolib.file_copy(ffn, fnew)
        PP.increment()

    print('Done')


def fix_sketch_maps():
    root = r'//nerctbctdb/shared/shared/PROJECTS/WG ERAMMP2 (06810)/2 Field Survey/Data Management/Processed Datasets/Veg plots/images/sketch_maps'
    rename_in_place = True

    if not rename_in_place:
        renamed_fld = path.normpath('%s/renamed' % root)
        iolib.create_folder(renamed_fld)

    i = sum([1 for _ in iolib.file_list_generator_dfe(root, '*.JPG', recurse=False)])
    PP = iolib.PrintProgress(i)

    for d, f, e, ffn in iolib.file_list_generator_dfe(root, '*.JPG', recurse=False):
        if 'plot' in f and 'ATT' in f:
            new_file_name = f[f.index('_')+1:].replace('plot', 'sketch')
        else:
            continue

        if rename_in_place:
            fnew = path.normpath('%s/%s' % (root, new_file_name))
            os.rename(ffn, fnew)
        else:
            fnew = path.normpath('%s/%s' % (renamed_fld, new_file_name))  # noqa
            if iolib.file_exists(fnew):
                raise ValueError('%s exists' % fnew)
            iolib.file_copy(ffn, fnew)
        PP.increment()

    print('Done')


def fix_ATT_images(root: str, rename_in_place=True):

    if not rename_in_place:
        renamed_fld = path.normpath('%s/renamed' % root)
        iolib.create_folder(renamed_fld)

    i = sum([1 for _ in iolib.file_list_generator_dfe(root, ('*.JPG', '*.PNG'), recurse=False)])
    PP = iolib.PrintProgress(i)

    for d, f, e, ffn in iolib.file_list_generator_dfe(root, ('*.JPG', '*.PNG'), recurse=False):
        if f[0:3] == 'ATT':
            new_file_name = f[f.index('_')+1:]
        else:
            PP.increment()
            continue

        if rename_in_place:
            fnew = path.normpath('%s/%s' % (root, new_file_name))
            n = 0
            while True:
                if iolib.file_exists(fnew):
                    n += 1
                    d, f, e = iolib.get_file_parts(fnew)
                    s = '%s_%s%s' % (f, n, e)
                    fnew = iolib.fixp(d, s)
                else:
                    break

            os.rename(ffn, fnew)
        else:
            fnew = path.normpath('%s/%s' % (renamed_fld, new_file_name))  # noqa
            if iolib.file_exists(fnew):
                raise ValueError('%s exists' % fnew)
            iolib.file_copy(ffn, fnew)
        PP.increment()


def replace(root: str, match: str, replace_with: str, rename_in_place: bool = True):
    """
    Case sensitive replace.

    Args:
        root ():
        match ():
        replace_with ():
        rename_in_place ():

    Returns:
        None
    """
    if not rename_in_place:
        renamed_fld = path.normpath('%s/renamed' % root)
        iolib.create_folder(renamed_fld)

    i = sum([1 for _ in iolib.file_list_generator_dfe(root, ('*.JPG', '*.PNG'), recurse=False)])
    PP = iolib.PrintProgress(i)

    for d, f, e, ffn in iolib.file_list_generator_dfe(root, ('*.JPG', '*.PNG'), recurse=False):
        if match in f:
            new_file_name = f.replace(match, replace_with)
        else:
            PP.increment()
            continue

        if rename_in_place:
            fnew = path.normpath('%s/%s' % (root, new_file_name))
            n = 0
            while True:
                if iolib.file_exists(fnew):
                    n += 1
                    d, f, e = iolib.get_file_parts(fnew)
                    s = '%s_%s%s' % (f, n, e)
                    fnew = iolib.fixp(d, s)
                else:
                    break

            os.rename(ffn, fnew)
        else:
            fnew = path.normpath('%s/%s' % (renamed_fld, new_file_name))  # noqa
            if iolib.file_exists(fnew):
                raise ValueError('%s exists' % fnew)
            iolib.file_copy(ffn, fnew)
        PP.increment()


if __name__ == '__main__':
    replace('//nerctbctdb/shared/shared/PROJECTS/WG ERAMMP2 (06810)/2 Field Survey/Data Management/Processed Datasets/Veg plots/images/sketch_maps', '_plot_', '_sketch_')
