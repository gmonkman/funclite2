# pylint: disable=C0302, dangerous-default-value, no-member,
# expression-not-assigned, locally-disabled, not-context-manager,
# redefined-builtin, consider-using-set-comprehension
"""My file input and output library, e.g. for _csv handling.
Also for general IO to the console"""
from __future__ import print_function as _print_function
from warnings import warn as _warn
from enum import Enum as _Enum
import inspect as _inspect
import stat as _stat
import pathlib as _pathlib
import os as _os
import os.path as _path
import shutil as _shutil

import errno as _errno
import csv as _csv
import glob as _glob
import itertools as _itertools
import time as _time

import string as _string
import tempfile as _tempfile
import subprocess as _subprocess
import sys as _sys
import datetime as _datetime
import pickle as _pickle
import copy as _copy
import platform as _platform
from contextlib import contextmanager as _contextmanager

import numpy as _numpy
import fuckit as _fuckit

import funclite2.stringslib as _stringslib
from funclite2.stringslib import pretty_date_now, pretty_date_time_now, pretty_date  # noqa useful for generating file names when using funcs in this module
from funclite2.stringslib import get_splits as filename_get_splits  # noqa

from funclite2.numericslib import round_normal as _rndnorm
from funclite2.stopwatch import StopWatch as _StopWatch
import funclite2.baselib as _baselib



_NOTEPADPP_PATH = 'C:\\Program Files (x86)\\Notepad++\\notepad++.exe'


def _var_get_name(var):
    """(Any)->str
    Get name of var as string

    Parameters
    var: Any variable
    Example:
    >>> _var_get_name(var)
    'var'
    """
    #  see https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string
    callers_local_vars = _inspect.currentframe().f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]


class CSVIo:
    """class for reading/writing _csv objects
    can work standalone or as the backbone for CSVMatch"""

    def __init__(self, filepath):
        """init"""
        self.filepath = filepath
        self.values = []
        self.rows = []

        self.read()

    def read(self, val_funct=lambda val: val):
        """use val_funct to operate on all the values before as they are read in"""
        with open(self.filepath, 'rU', encoding='utf-8') as f:
            raw_csv = _csv.DictReader(f)
            for row in raw_csv:
                row = {key: val_funct(val) for key, val in row.items()}
                self.rows.append(row)
                self.values += row.values()
            return

    def save(self, filepath=None):
        """save"""
        if not filepath:
            filepath = self.filepath
        with open(filepath, 'w', encoding='utf-8') as f:
            writer = _csv.DictWriter(f, self.rows[0].keys())  # noqa
            writer.writeheader()
            for row in self.rows:
                writer.writerow(row)
            return


class CSVMatch(CSVIo):
    """CSVMatch class"""

    def row_for_value(self, key, value):
        """returns a list of matching rows
        key = the column name on the _csv
        value = the value to match in that column

        Returns None if no match
        """
        if value or not value not in self.values:
            return None

        match = None
        for row in self.rows:
            if row[key] == value:
                if match:
                    raise MultipleMatchError()
                match = row
        return match

    def row_for_object(self, match_function, obj):
        """
        like row_for_value, but allows for a more complicated match.
        match_function takes three parameters (vals, row, object) and return true/false

        Returns:
            None if no match, else the returns the row
        """
        for row in self.rows:
            if match_function(row, obj):
                return row
        return None


class MultipleMatchError(RuntimeError):
    """helper"""
    pass


class FileProcessTracker:
    """Manages recording of the processing status
    of files. This can be used in processing
    pipelines to skip files that have already
    been processed.

    It stores each file along with a status and
    error message (if applicable) in a list which
    is pickled to the file defined at instance creation.

    A single status record is a 3-list:
    list[0] = image path
    list[1] = status (eProgressStatus value)
    list[2] = error message (if relevant)

    Args:
        files_folder (str): folder with the files

    Examples:
        >>> T = FileProcessTracker('C:/temp', 'C:/temp/tracker.lst')  # noqa
    """

    # print('Initialising ProgressStatus...')

    class eFileProcessStatus(_Enum):
        """progress status"""
        NotProcessed = 0
        Errored = 1
        Success = 2
        FileDoesNotExist = 3

    class eListIndex(_Enum):
        """list index for progressstatus list"""
        file_path = 0
        status = 1
        error = 2

    def __init__(self, files_folder, pickle_file_path):
        self.files_folder = _path.normpath(files_folder)
        self._pickle_file_path = _path.normpath(pickle_file_path)
        try:
            if file_exists(self._pickle_file_path):
                self._status_list = unpickle(self._pickle_file_path)
            else:
                self._status_list = []
        except Exception as _:
            _warn('Failed to load status file %s' % pickle_file_path)

    def __repr__(self):
        """repr"""
        return 'Status tracker for folder: %s\nStatus File:%s\n%s files tracked' % (self.files_folder, self._pickle_file_path, len(self._status_list) if self._status_list else 'None')

    def save(self):
        """save status_list to the file system"""
        pickle(self._status_list, self._pickle_file_path)

    def get_file_status(self, file_path):
        """(str) -> Enum:FileProcessTracker.eFileProcessStatus

        Get status of the file defined by file_path.
        """
        files = [f[FileProcessTracker.eListIndex.file_path.value] for f in self._status_list]
        if _path.normpath(file_path) in files:
            return FileProcessTracker.eFileProcessStatus(self._status_list[files.index(file_path)][FileProcessTracker.eListIndex.status.value])
        return FileProcessTracker.eFileProcessStatus.NotProcessed

    def status_add(self, file_path, status=eFileProcessStatus.Success, err='', ignore_item_exists=False, save_=True):
        """(str, Enum, bool, bool) -> void
        Add status for the file defined by file_path

        Parameters:
            file_path (str): file path
            ignore_item_exists: adds the status to the list
            status: The status to set
            err: error to add (if required)
            ignore_item_exists: raises ValueError if the item already exists and this is false
            save_: picke the list after item added
        """
        file_path = _path.normpath(file_path)
        if self.get_file_status(file_path) == FileProcessTracker.eFileProcessStatus.NotProcessed:
            self._status_list.append([file_path, status.value, err])
            if save_:
                self.save()
        else:
            if ignore_item_exists:
                pass
            else:
                raise ValueError('Image "%s" is already in the processed list' % file_path)

    def status_edit(self, file_path, status=eFileProcessStatus.Success, err='', ignore_no_item=True):
        """record image file as processed"""
        file_path = _path.normpath(file_path)
        files = [f[FileProcessTracker.eListIndex.file_path.value] for f in self._status_list]
        i = None
        if ignore_no_item:
            try:
                i = files.index(file_path)
            except ValueError as _:
                pass
        else:
            i = files.index(file_path)  # noqa

        files[i] = [file_path, status.value, err]

    def status_del(self, file_path, ignore_no_item=True):
        """delete a status

        Parameters:
            file_path: the file to set
            ignore_no_item: suppress erros if file_path not in the status list
        """
        file_path = _path.normpath(file_path)
        files = [f[self.eListIndex.file_path.value] for f in self._status_list]
        if ignore_no_item:
            i = files.index(file_path) if file_path in files else None
            if i:
                del self._status_list[i]
        else:
            i = files.index(file_path)
            del self._status_list[i]

    def clean(self, save=True):
        """(bool) -> void
        Cleans the in-memory list of files
        which are in the list, but not present
        in the folder

        Parameters:
            save: save the in-memory list to disk
        """
        new_lst = [s for s in self._status_list if file_exists(s[FileProcessTracker.eListIndex.file_path.value])]
        self._status_list = new_lst
        if save:
            self.save()


class PickleHelper:
    """Pickle and unpickle an individual variable to the file system.
    Instantiate a PickleHelper instance for each variable.

    If the var is None, will attempt to load var from the file system

    Args:
        root (str): root folder to save pickle
        pkl_file_name (str): filename of the pickle file (e.g. myfile.pkl)
        var (any): the variable to handle
        type_ (object): A type, used to check if the pkl has loaded (e.g. str, int, list, Pandas.DataFrame)
        force_load_from_pkl (bool): force loading from the pickle even if var is not None
        err_if_none (bool): raise an error if we couldn't get var, and var was none in the first place

    Raises:
        ValueError: If the variable to pickle is None and err_if_none == True

    Notes:
        Works on a deepcopy of var

    Examples:
        >>> lst = list([1,2,3])
        >>> P = PickleHelper('c:/temp', 'list.pkl', lst)
        >>> print(P.var)
    """

    def __init__(self, root: str, pkl_file_name: str, var: any, type_, force_load_from_pkl: bool = False, err_if_none: bool = False):
        self._root = root
        self._pkl_file_name = pkl_file_name
        self.var = _copy.deepcopy(var)
        self._force_load = force_load_from_pkl
        self._type = type_
        self._dump_fqn = _path.normpath(_path.join(self._root, pkl_file_name))

        self._load()
        if err_if_none and self.var is None:
            raise ValueError('PickleHelper variable was None and you asked to raise an error')

    def _load(self):
        """load the var"""
        if (self._force_load or self.var is None) and file_exists(self._dump_fqn):
            self.var = unpickle(self._dump_fqn)
            if not isinstance(self.var, self._type) and not self.var:  # noqa
                self.var = self._type()  # noqa

        self.loaded = isinstance(self.var, self._type)  # noqa

    def delete_pkl(self):
        """delete the pickle"""
        file_delete(self._dump_fqn)

    def dump(self, var=None):
        """Pickle the var to root/pkl_file_name.

        Args:
            var (any): Pickle the passed var instead of self.var

        Raises:
            ValueError: If self.type_ does not match the type of var (or self.var). So make sure you pass the right type when creating an instance.

        Examples:
            >>> lst = list([1,2,3])
            >>> P = PickleHelper('c:/temp', 'list.pkl', lst)
            >>> P.var.append(4)  # add a 4 to P.var
            >>> P.dump()  # dump out P.var (i.e. [1,2,3,4] to c:/temp/list.pkl)
        """

        if var is not None:
            if not isinstance(var, self._type) and self._type is not None:  # noqa
                raise ValueError('Expected variable var to have type %s, got %s' % (type(self._type), type(var)))
            self.var = var
        pickle(self.var, self._dump_fqn)


# region _csv IO
def write_to_eof(filename, thetext):
    """(_string,_string) ->void
    Write thetext to the end of the file given in filename.
    """
    try:
        with open(filename, 'a+', encoding='utf-8') as fid:
            fid.write(thetext)
    except Exception as _:
        pass


def readcsv_as_dict(filename, first_row_as_key=True, error_on_dup_key=False):
    """(str,bool) -> dict
    read a csv file as a dict
    
    filename: file path

    first_row_as_key: 
        True: first row contains dict keys. Subsequent rows are the values
        False: the first column  contains keys, subsequent columns contain values, no header row is assumed.
                if the key column (first) contains duplicate values, rows containing the duplicate key
                will be skipped


    Example:
    """
    result = {}
    filename = _path.normpath(filename)
    with open(filename, encoding='utf-8') as csvfile:
        reader = _csv.DictReader(csvfile, skipinitialspace=True)
        if first_row_as_key:

            if error_on_dup_key and len(reader.fieldnames) > len(set(reader.fieldnames)):
                raise ValueError('First row had duplicate values, which is a duplicate key condition')

            result = {name: [] for name in reader.fieldnames}
            for row in reader:
                for name in reader.fieldnames:
                    result[name].append(row[name])
        else:
            csv_list = [[val.strip() for val in r.split(",")] for r in csvfile.readlines()]
            (_, *header), *data = csv_list
            for row in data:
                key, *values = row
                if key not in result:
                    result[key] = {key: value for key, value in zip(header, values)}
                else:
                    if error_on_dup_key: raise ValueError('First column had duplicate values, which is a duplicate key condition')
    return result


def readcsv(filename, cols=1, startrow=0, numericdata=False, error_on_no_file=True):
    """(string, int, bool, int, bool, bool) -> list
    Reads a _csv file into a list.
    
    cols:Number of columns to retrieve, DOES NOT support any fancy indexing
    start_row: row to start reading from. 0 is the first row
    numericdata: force all data to be a number, raises error if any non-numeric encountered
    error_on_no_file: Raise error if file filename does not exist, else return empty list

    Example:
    a,  b,  c
    1,  2,  3
    10, 11, 12
    readcsv(fname, 1, 1)
    [[1, 10]]

    a,  b,  c
    1,  2,  3
    10, 11, 12
    readcsv(fname, 2, 0)
    [[a, 1, 10], [b, 2, 11]]
    """
    filename = _path.normpath(filename)
    if not file_exists(filename) and not error_on_no_file:
        return []

    data = [0] * cols
    for i in range(cols):
        data[i] = []  # noqa
    if _sys.version_info.major == 2:
        with open(filename, 'rb') as csvfile:  # open the file, and iterate over its data
            csvdata = _csv.reader(csvfile)  # tell python that the file is a _csv
            for i in range(0, startrow):  # skip to the startrow
                next(csvdata)
            for row in csvdata:  # iterate over the rows in the _csv
                # Assign the cols of each row to a variable
                for items in range(cols):  # read in the text values as floats in the array
                    if numericdata:
                        data[items].append(float(row[items]))  # noqa
                    else:
                        data[items].append(row[items])  # noqa
    elif _sys.version_info.major == 3:
        with open(filename, newline='', encoding='utf-8') as csvfile:  # open the file, and iterate over its data
            csvdata = _csv.reader(csvfile)  # tell python that the file is a _csv
            for i in range(0, startrow):  # skip to the startrow
                next(csvdata)
            for row in csvdata:  # iterate over the rows in the _csv
                # Assign the cols of each row to a variable
                for items in range(cols):  # read in the text values as floats in the array
                    if numericdata:
                        data[items].append(float(row[items]))  # noqa
                    else:
                        data[items].append(row[items])  # noqa
    else:
        _sys.stderr.write('You need to use python 2* or 3* \n')
        exit()
    return data


def readcsv_by_row(fname: str, skip_first_n: int = 0) -> list:
    """read a csv file into a list of lists
    where list item is a row

    Args:
        fname (str): filename
        skip_first_n (int): skip first n rows

    Returns:
        2n list of lists

    Examples:
            a,  b,  c
            1,  2,  3
            10, 11, 12

        Basic read
        >>> readcsv_by_row('c:/my.csv')
        [[a, b, c], [1,2,3], [10,11,12]]

        Skip first row
        >>> readcsv_by_row('c:/my.csv', skip_first_n=1)
        [[a, b, c], [1,2,3], [10,11,12]]
    """
    fname = _path.normpath(fname)
    with open(fname, newline='') as f:
        reader = _csv.reader(f)
        data = list(reader)
    return data[skip_first_n:]


def writecsv(filename, datalist, header=(), inner_as_rows=True, append=False, skip_first_row_if_file_exists=False) -> None:
    """
    Writes a list to filename.

    Think of inner_as_rows=False as a vstack of the nested lists (see examples)

    Args:
        filename (str): Filename to export csv to
        datalist (list, tuple): the list of lists
        header (list, tuple): header row
        inner_as_rows (bool): vstack or hstack the nested list (see exmaples)
        append (bool): Append datalist to filename, or overwrite existing csv
        skip_first_row_if_file_exists (bool): if filename exists, skip the first row from datalist (to test)

    Returns:
        None

    Examples:
        >>> lst = [[1,'a'],[2,'b']]
        >>> writecsv('c:\my.log', lst, inner_as_row=True)
        1,2
        a,b

        >>> writecsv('c:\my.log', lst, header=('cola', 'colb') inner_as_row=False)
        cola,colb
        1,a
        2,b
    """
    csvfile = []  # noqa
    useheader = False
    exists = file_exists(filename)
    if not append:
        exists = False

    try:
        if append:
            csvfile = open(filename, 'a', newline='', encoding='utf-8')
        else:
            csvfile = open(filename, 'w', newline='', encoding='utf-8')
    except FileNotFoundError as _:
        print("Could not create file %s, check the file's folder exists." % filename)
        return
    except Exception as e:
        raise e

    # if user passed a numpy array, convert it
    if isinstance(datalist, _numpy.ndarray):
        datalist = datalist.T
        datalist = datalist.tolist()
    # if there is no data, close the file
    if len(datalist) < 1:
        csvfile.close()
        return
    # check to see if datalist is a single list or list of lists
    is_listoflists = False  # noqa
    list_len = 0  # noqa
    num_lists = 0  # noqa
    if isinstance(datalist[0], (list, tuple)):  # check the first element in datalist
        is_listoflists = True
        list_len = len(datalist[0])
        num_lists = len(datalist)
    else:
        is_listoflists = False
        list_len = len(datalist)
        num_lists = 1

    # if a list then make sure everything is the same length
    if is_listoflists:
        for list_index in range(1, len(datalist)):
            if len(datalist[list_index]) != list_len:
                _sys.stderr.write('All lists in datalist must be the same length \n')
                csvfile.close()
                return

    # if header is present, make sure it is the same length as the number of
    # cols
    if header:
        if len(header) != list_len:
            _sys.stderr.write('Header length did not match the number of columns, ignoring header.\n')
        else:
            useheader = True

    # now that we've checked the inputs, loop and write outputs
    writer = _csv.writer(csvfile,
                         delimiter=',',
                         quotechar='|',
                         quoting=_csv.QUOTE_MINIMAL)  # Create writer object
    if useheader:
        writer.writerow(header)
    if inner_as_rows:
        for i, row in enumerate(range(0, list_len)):
            if i == 0 and skip_first_row_if_file_exists and exists:
                pass
            else:
                thisrow = []
                if num_lists > 1:
                    for col in range(0, num_lists):
                        thisrow.append(datalist[col][row])
                else:
                    thisrow.append(datalist[row])
                writer.writerow(thisrow)
    else:
        for i, row in enumerate(datalist):
            if i == 0 and skip_first_row_if_file_exists and exists:
                pass
            else:
                writer.writerow(row)
    csvfile.close()


# endregion


# region file system
def temp_folder(subfolder=''):
    """Returns a folder in the users temporary space.
    subfolder:
        if !== '': create the defined subfolder
        otherwise uses a datetime stamp
    """
    fld = datetime_stamp() if subfolder == '' else subfolder
    return _path.normpath(_path.join(_tempfile.gettempdir(), fld))


def datetime_stamp(datetimesep=''):
    """(str) -> str
    Returns clean date-_time stamp for file names etc
    e.g 01 June 2016 11:23 would be 201606011123
    str is optional seperator between the date and _time
    """
    fmtstr = '%Y%m%d' + datetimesep + '%H%m%S'
    return _time.strftime(fmtstr)


def exit():  # noqa
    """override exit to detect platform"""
    if get_platform() == 'windows':
        _os.system("pause")
    else:
        _os.system('read -s -n 1 -p "Press any key to continue..."')
    _sys.exit()


def get_platform() -> str:
    """
    Get platform/os name as string.

    Returns:
         str: Platform, IN ['windows', 'mac', 'linux']
    """
    s = _sys.platform.lower()
    if s in ("linux", "linux2"):
        return 'linux'
    if s == "darwin":
        return 'mac'
    if s in ("win32", "windows"):
        return 'windows'
    return 'linux'


def get_file_count(paths: (str, list), recurse: bool = False) -> int:
    """
    Get file count in a folder or list of folders.

    Args:
        paths (str, list): Path or list of paths
        recurse (bool): Recurse paths

    Returns:
        int: file count

    Notes:
        Left here to not break other code.
        See file_count and file_count2 which support matching

    Examples:
        >>> get_file_count('C:/TEMP', False)
        5
    """
    cnt = 0

    if isinstance(paths, str):
        paths = [paths]

    for ind, val in enumerate(paths):
        paths[ind] = _path.normpath(val)

    if recurse:
        for thedir in paths:
            cnt += sum((len(f) for _, _, f in _os.walk(thedir)))
    else:
        for thedir in paths:
            cnt += len([item for item in _os.listdir(thedir)
                        if _path.isfile(_path.join(thedir, item))])
    return cnt


def file_count_to_list(pth, out='', match='.*'):
    """
    Get a list 2-deep list of file counts in a root directory

    Args:
        pth: root folder to count
        out: Optional file to dume csv results to
        match: iterable of starred matches, e.g. ('*.jpg','*.gif')

    Examples:
        >>> file_count_to_list('c:/temp','c:/out.csv', match=('.jpg','.gif'))  # noqa
        [['c:/temp',10],['c:/temp/subfld',12]]
    """
    # TODO Debug this, might be issues with the wildcarding
    R = []
    for d, _, _ in folder_generator(_path.normpath(pth)):
        i = file_count2(d, match=match)
        R.append([d, i])
    if out:
        out = _path.normpath(out)
        writecsv(out, R, inner_as_rows=False, header=['dir', 'n'])
    return R


def hasext(path, ext):
    """(str, str|iter)->bool
    Does the file have extension ext
    ext can be a list of extensions
    """
    if isinstance(ext, str):
        return get_file_parts2(path)[2] == ext

    return get_file_parts2(path)[2] in ext


def hasdir(path, fld):
    """(str, str|list)->bool
    Is the file in folder fld.
    fld can be a list of folders (strings)
    """
    if isinstance(path, str):
        return get_file_parts2(path)[0] == fld

    return get_file_parts2(path)[0] in fld


def hasfile(path, fname):
    """(str, str|list)->bool
    Does path contain the filename fname.

    path:
        full path name to a file
    fname:
        the file name

    Example:
    >>>hasfile('c:/tmp/myfile.txt', 'myfile.txt')
    True

    Returns:
        true if fname is the file in path.

    """
    if isinstance(path, str):
        return get_file_parts2(path)[1] == fname

    return get_file_parts2(path)[1] in fname


def drive_get_uuid(drive='C:', strip=('-',), return_when_unidentified='??'):
    """get uuid of drive"""
    proc = _os.popen('vol %s' % drive)

    try:
        drive = proc.readlines()[1].split()[-1]
        if not drive:
            drive = return_when_unidentified

        for char in strip:
            drive = drive.replace(char, '')
    except Exception as _:
        pass
    finally:
        try:
            proc.close()
        except:
            pass
        # work

    return drive


def get_file_parts(filepath: str) -> list:
    """
    Given path to a file, split it into path,
    file part and extension.

    Args:
        filepath (str): full path to a file.

    Returns:
        list: [folder, filename sans extension, extension]

    Examples:
        >>> get_file_parts('c:/temp/myfile.txt')
        'c:/temp', 'myfile', '.txt'
    """
    filepath = _path.normpath(filepath)
    folder, fname = _path.split(filepath)
    fname, ext = _path.splitext(fname)
    return [folder, fname, ext]


def get_file_parts2(filepath: str) -> list:
    """
    Split a full file path into path, file name with extension and dotted extension.

    Args:
        filepath (str): full path to a file.

    Returns:
        list: [folder, file name with extension, dotted extension]

    Examples:

        >>> get_file_parts2('c:/temp/myfile.txt')
        'c:/temp', 'myfile.txt', '.txt'
    """
    folder, fname = _path.split(filepath)
    ext = _path.splitext(fname)[1]
    return [folder, fname, ext]


def folder_has_files(fld: str, ext_dotted: tuple[str] = ()) -> bool:
    """(str, str|list) -> bool
    Does the folder contain files, optionally matching
    extensions. Extensions are dotted.

    This checks in subfolders. So even if fld has no files, True will be returned if any subdir has files

    fld: folder path
    ext_dotted: list of extensions to match

    Returns:
        False if the folder does not exist, else True.

    Examples:

    >>> folder_has_files('C:/windows')
    True


    specify file extensions

    >>> folder_has_files('C:/windows', ['.dll'])
    True
    """
    if isinstance(ext_dotted, str):
        ext_dotted = [ext_dotted]

    for _, _, files in _os.walk(_path.normpath(fld)):
        if files and not ext_dotted:
            return True

        for fname in files:
            for ext in ext_dotted:
                if fname.endswith(ext):
                    return True

    return False


def get_available_drives(strip=('-',), return_when_unidentified='??'):
    """->dictionary
    gets a list of available drives as the key, with uuids as the values
    eg. {'c:':'abcd1234','d:':'12345678'}
    """
    drives = [
        '%s:' % d for d in _string.ascii_uppercase if _path.exists('%s:' % d)]
    uuids = [drive_get_uuid(drv, strip, return_when_unidentified)
             for drv in drives]
    return dict(zip(drives, uuids))


def get_available_drive_uuids(strip=('-',), return_when_unidentified='??'):
    """->dictionary
    gets a list of available drives with uuids as the key
    eg. {'c:':'abcd1234','d:':'12345678'}
    """

    s = _string.ascii_uppercase
    drives = ['%s:' % d for d in s if _path.exists('%s:' % d)]
    uuids = [drive_get_uuid(drv, strip, return_when_unidentified)
             for drv in drives]
    return dict(zip(uuids, drives))


def get_drive_from_uuid(uuid, strip=('-',)):
    """str, str iterable, bool->str | None
    given a uuid get the drive letter
    uuid is expected to be lower case

    Returns None if not found
    """

    for char in strip:
        uuid = uuid.replace(char, '')

    # first val is drive, second is the uuid
    drives = get_available_drive_uuids(strip)
    if uuid in drives:
        return drives[uuid]
    if uuid.lower() in drives:
        return drives[uuid]
    return None


def folder_copy(src: str, dest: str, ignore: (list, tuple) = (), raise_error: bool = False) -> None:
    """
    Recursive copy of folder src to folder dest.
    This copies all files and folders BELOW dest

    Args:
          src (str): Source folder
          dest (str): Dest folder
          ignore (list, tuple): ignore these patterns (see shutil.ignore_patterns)
          raise_error (bool): Raise an error if it occurs

    Returns:
        None

    Notes:
        Will fail if dest already exists.

    Examples:
        Copy all files and folders, ignoring some image types.
        >>> folder_copy('C:/TEMP/mydir', 'C:/TEMP/mydir_copy', ignore=['*.jpg'. '*.gif'])
    """
    src = _path.normpath(src)
    dest = _path.normpath(dest)
    try:
        if ignore:
            _shutil.copytree(src, dest, ignore=_shutil.ignore_patterns(*ignore))
        else:
            _shutil.copytree(src, dest)
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == _errno.ENOTDIR:
            _shutil.copy(src, dest)
        else:
            if raise_error:
                raise e
            else:
                print('Directory not copied. Error: %s' % e)


def folder_generator(paths: (str, list)):
    """
    Yield subfolders in paths with wildcard match on any in match.
    Recurses through all subfolders

    Args:
        paths (str, list): Paths to iterate

    Yields:
        str: subfolders in paths

    Notes:
        Also see folder_generator2 which supports wildcard matching and can be set to not recurse

    Examples:
        >>> [s for s in folder_generator2('C:/temp', 'folder')]  # noqa
        ['C:/temp/folder_for_me', 'C:/temp/folder_for_you']
    """
    if isinstance(paths, str):
        paths = [paths]

    paths = [_path.normpath(p) for p in paths]
    for pth in paths:
        for fld, _, _ in _os.walk(pth):
            if fld in paths:
                continue
            yield fld


def folder_generator2(paths: (str, list), match: (str, list) = (), ignore_case: bool = True, recurse: bool=True) -> str:
    """
    Yield subfolders in paths with wildcard match on any in match.

    Args:
        paths (str, list): Paths to iterate
        match (str, list): Wildcard match on this. If empty or None, no filter is applied (i.e. every dir is yielded)
        ignore_case (bool): Make match case insensitive
        recurse (bool): Recurse into subfolders of root subfolders

    Yields:
        str: subfolders in paths

    Examples:
        >>> [s for s in folder_generator2('C:/temp', 'folder')]  # noqa
        ['C:/temp/folder_for_me', 'C:/temp/folder_for_you']
    """
    if isinstance(paths, str):
        paths = [paths]

    if isinstance(match, str):
        match = [match]

    paths = [_path.normpath(p) for p in paths]
    if recurse:
        for pth in paths:
            for fld, _, _ in _os.walk(pth):
                if fld in paths:
                    continue
                if _stringslib.iter_member_in_str(fld, list(map(str, match)), ignore_case):
                    yield fld
    else:
        for pth in paths:
            for item in _os.listdir(pth):
                if _os.path.isdir(_path.join(pth, item)):
                    if _stringslib.iter_member_in_str(item, list(map(str, match)), ignore_case):
                        yield _path.join(pth, item)

def file_list_generator(paths: (str, list, tuple), wildcards: (str, list, tuple)):
    """
    Takes a list of paths and wildcards and yields full file paths
    matching wildcards.

    Args:
       paths (str, list, tuple): Paths to walk, e.g. ('c:/','d:/')
       wildcards ( str, list, tuple):  File extensions, either starred-dotted or dotted

    Yields:
        str: file paths

    Notes:
        Consider using file_list_generator1 instead of this

    Examples:
        >>> paths = ('c:/','d:/'); wildcards=('*.ini','*.txt')  # noqa
        >>> list(file_list_generator(paths, wildcards))
        ['c:/my.ini', 'd:/my.txt', ...]
    """

    if isinstance(wildcards, str):
        wildcards = [wildcards]
    if isinstance(paths, str):
        paths = [paths]
    ww = ['*' + x if x[0] == '.' else x for x in wildcards]  # add * if just dotted i.e. .jpg -> *.jpg

    for dir_, ext in _itertools.product(paths, ww):
        wild_path = fixp(dir_, ext)
        for fname in file_list_glob_generator(wild_path, False):
            yield _path.normpath(fname)


def file_count(paths: (str, list), wildcards: (str, list), match: (str, list) = '*', directory_match: (str, list) = '*', recurse: bool = False) -> int:
    """
    Counts files in paths matching wildcards

    Args:
        paths (str, list): tuple of list of paths
        wildcards (str, list): str or list of dotted file extensions e.g. ".jpg"
        match (str, list): wildcard match
        directory_match (str, list): wildcard match on dir name
        recurse (bool): recurse down folders

    Returns:
        int: file count

    Examples:
        All images in C:/TEMP containing "greece" or "uk"
        >>> file_count('C:/TEMP', ['.jpg', '.gif', 'bmp'], ['greece', 'uk'], True)
        231
    """

    cnt = 0
    for f in file_list_generator1(paths, wildcards, recurse):
        if (not match or match == '*') and (not directory_match or directory_match == '*'):
            cnt += 1
            continue

        d, fname = get_file_parts2(f)[0:2]
        if match and match != '*':
            if isinstance(match, str):
                mtc = [match]
            else:
                mtc = match
            if not _baselib.list_member_in_str(fname, mtc, True):
                continue

        if directory_match and directory_match != '*':
            if isinstance(directory_match, str):
                dmtch = [directory_match]
            else:
                dmtch = directory_match
            if not _baselib.list_member_in_str(d, dmtch, True):
                continue

        cnt += 1

    return cnt


def file_list_generator1(paths: (str, list, tuple), wildcards: (str, list, tuple), recurse: bool = False) -> str:
    """(str|iterable, str|iterable, bool) -> yields str
    Takes path(s) and wildcard(s), yielding the
    path-normed full path to matched files.

    Args:
        paths (str, list, tuple): Single path or list/tuple of paths
        wildcards (str, list, tuple): Single file extension or list of file extensions. Extensions can be star-dotted or dotted.
        recurse (bool): recurse down folders

    Yields:
        str: file path

    Examples:
        >>> for fname in file_list_generator1('C:/temp', '*.txt', recurse=False):
        >>>     print(fname)
        'C:/temp/file.txt'
        'C:/temp/file1.txt'
        ....
        >>> for fname in file_list_generator1(['C:/temp', 'C:/windows'], ['.bat', '.cmd'], recurse=True):
    """
    if isinstance(paths, str):
        paths = [paths]

    if isinstance(wildcards, str):
        wildcards = [wildcards]
    if wildcards is None: wildcards = '*'
    wildcards = tuple(set(['*' + x.lower() if x[0] == '.' else x.lower() for x in wildcards]))

    for vals in (_stringslib.add_right(x[0]) + x[1] for x in _itertools.product(paths, wildcards)):
        if recurse:
            for f in file_list_glob_generator(vals, recurse=True):
                yield _path.normpath(f)
        else:
            for myfile in _glob.glob(_path.normpath(vals)):
                yield _path.normpath(myfile)


def file_list_generator2(paths: (str, list, tuple), wildcards: (str, list, tuple), find: (str, tuple, list, None) = None, exclude: (str, tuple, list, None) = None, recurse: bool = False) -> str:
    """
    Takes path(s) and wildcard(s), yielding the
    path-normed full path to matched files.

    Support find and exclude lists. Exclude overrides find.

    Args:
        paths (str, list, tuple): Single path or list/tuple of paths
        wildcards (str, list, tuple): Single file extension or list of file extensions. Extensions can be star-dotted or dotted.
        find (list, str, tuple, None): list or string, to match file names
        exclude (list, str, tuple, None): list or string, to exclude file names. Overrides find.
        recurse (bool): recurse down folders

    Yields:
        str: file path

    Examples:
        >>> for fname in file_list_generator1('C:/temp', '*.txt', find=['123', 'abc'], exclude=['ignore', 'bad'], recurse=False):
        >>>     print(fname)
        'C:/temp/file.txt'
        'C:/temp/file1.txt'
        ....
        >>> for fname in file_list_generator1(['C:/temp', 'C:/windows'], ['.bat', '.cmd'], recurse=True):
    """

    def _filter(s: str, find_, exclude_) -> bool:
        found = True
        if not (find_ or exclude_):
            return True

        if isinstance(find_, str):  find_ = [find]
        if isinstance(exclude_, str): exclude_ = [exclude]

        # found is first used as a flag to determine if we have found text IN exclude
        if exclude_:
            found = _baselib.list_member_in_str(s, exclude_)  # i.e. have we found anything that wildcard matches text IN exclude
            if found:
                return False

        if find_:
            found = _baselib.list_member_in_str(s, find)
        return found

    if isinstance(paths, str):
        paths = [paths]

    if isinstance(wildcards, str):
        wildcards = [wildcards]

    if wildcards is None: wildcards = '*'
    wildcards = tuple(set(['*' + x.lower() if x[0] == '.' else x.lower() for x in wildcards]))

    for vals in (_stringslib.add_right(x[0]) + x[1] for x in _itertools.product(paths, wildcards)):
        if recurse:
            for f in file_list_glob_generator(vals, recurse=True):
                if _filter(get_file_parts2(f)[1], find, exclude):
                    yield _path.normpath(f)
        else:
            for myfile in _glob.glob(_path.normpath(vals)):
                if _filter(get_file_parts2(myfile)[1], find, exclude):
                    yield _path.normpath(myfile)


def file_last_modified_get(paths: (str, list, tuple), wildcards: (str, list, tuple), find: (str, tuple, list, None) = None, exclude: (str, tuple, list, None) = None, recurse: bool = False) -> str:
    """
    Takes path(s) and wildcard(s) and then returns the last modified fully qualified file name that matches the search criteria.

    Args:
        paths (str, list, tuple): Single path or list/tuple of paths
        wildcards (str, list, tuple): Single file extension or list of file extensions. Extensions can be star-dotted or dotted.
        find (list, str, tuple, None): list or string, to match file names
        exclude (list, str, tuple, None): list or string, to exclude file names. Overrides find.
        recurse (bool): recurse down folders

    Returns:
        str: full qualified file path

    Examples:
        >>> print(file_last_modified_get('C:/temp', '*.txt', find=['123', 'abc'], exclude=['ignore', 'bad'], recurse=False)
        'C:/temp/file_latest.txt'
    """
    files = [f for f in file_list_generator2(paths, wildcards, find, exclude, recurse)]
    return max(files, key=_path.getmtime)


def file_list_generator_dfe(paths, wildcards, recurse=False):
    """
    Takes path(s) and wildcard(s), yielding the
    directory, filename and extension.

    Args:
        paths (str, list, tuple): Single path or list/tuple of paths
        wildcards (str, list, tuple): Single dotted file extension or list of dotted file extensions. None or empty iterable are treated as '*' (i.e. all files).
        recurse (bool): recurse down folders

    Returns:
        tuple: returns a length 4 tuple, (folder, filename with extension, dotted extension, full fie path)

    Notes:
        Case insentive to paths and wildcards (MS Windows - untested on other OS's.
        Fixed bug where this would yield folders.

    Examples:

        >>> for folder, filename, extension, fullname in file_list_generator_dfe('C:/temp', '*.msi', recurse=False):
        ('C:\\TEMP', 'SQL_XEVENT.MSI', '.MSI', 'C:\\TEMP\\SQL_XEVENT.MSI')


        >>> for folder, filename, extension, fullname in file_list_generator_dfe(['C:/temp', 'C:/windows'], ['.MSI', '.txt'], recurse=True):
        ('C:\\TEMP', 'SQL_XEVENT.MSI', '.MSI', 'C:\\TEMP\\SQL_XEVENT.MSI')
        ('C:\\TEMP', 'mytest.txt', '.txt', 'C:\\TEMP\\mytest.txt')
    """
    if not wildcards: wildcards = '*'
    for fname in file_list_generator1(paths, wildcards, recurse):
        if folder_exists(fname):
            continue
        yield *get_file_parts2(fname), fname


def file_list_generator_as_list(paths: (list, tuple, str), wildcards: (list, tuple, str), recurse=False):
    """
    Get a list of file names in paths, matching wildcards.

    Args:
        paths (str, list, tuple): Single path or list/tuple of paths
        wildcards (str, list, tuple): Single dotted file extension or list of dotted file extensions. None or empty iterable are treated as '*' (i.e. all files).
        recurse (bool): recurse down folders

    Returns:
        list: list of file names (no paths)

    Notes:
        Calls file_list_generator_dfe, but less faff when need a simple list.

    Examples:
        >>> file_list_generator_as_list(r'C:\TEMP', '*.pdf')
        ['1.pdf', '2.pdf']
    """
    return [f for _, f, _, _ in file_list_generator_dfe(paths, wildcards, recurse)]


def file_list_glob_generator(wilded_path: str, recurse: bool = False):
    """
    _glob.glob generator from wildcarded path

    Yields fully qualified file names, e.g. c:/temp/a.tmp

    Args:
        wilded_path (str): The path with wildcard. Is normpathed. e.g. 'c:/*.tmp' or c:/*.*
        recurse (bool): recurse

    Yields:
        str: The fully qualified path name

    Notes:
        Will now only yield files. Was previously bugged and would yield folders as well
    """
    fld, f = get_file_parts2(wilded_path)[0:2]

    if recurse:
        wilded_path = _path.normpath(_path.join(fld, '**', f))

    for file in _glob.iglob(wilded_path, recursive=recurse):
        if folder_exists(file):
            continue
        yield _path.normpath(file)


def file_from_substr(fld: str, substr: str, allow_multi_match: bool = False) -> (str, list, None):
    """Get filename from folder and square id

    Args:
        fld (str): root folder to search
        substr (str): substring, eg a sq_id str(123)
        allow_multi_match (bool): returns list of multiple matches, if false and multi matches, raises ValueError

    Returns:
        None: No matches
        str: the full filename if not allow_multi_match, or None if no match
        list: list of matches if allow_multi_match

    Raises:
        ValueError: If get more than 1 file matching substr

    Examples:
        
        >>> file_from_substr('C:/temp', '12345')
        'C:/temp/my_12345_file.txt'


        Multiple matches, but not allowed
        
        >>> file_from_substr('C:/temp', 'this_matches_loads_of_files', allow_multi_match=False)
        Traceback (most recent call last):....


        Multiple matches, allowed
        
        >>> file_from_substr('C:/temp', 'this_matches_loads_of_files', allow_multi_match=False)
        ['C:/temp/this_matches_loads_of_files1.txt', 'C:/temp/this_matches_loads_of_files2.txt', .... ]

    """
    lst = list()
    substr = str(substr)
    for _, f, _, fname in file_list_generator_dfe(fld, substr, recurse=False):
        if substr.lower() in f.lower():
            lst += [fname]

    if allow_multi_match:
        return lst

    if lst and len(lst) > 1:
        raise ValueError('Wildcard %s match more than one file: %s' % (substr, str(lst)))

    if not lst: return None

    return lst[0]


def files_delete2(filenames: (list[str], str)) -> None:
    """
    Delete file(s) without raising an error

    Args:
        filenames (list[str], str): a string or iterable

    Examples:
        >>> files_delete2('C:/myfile.tmp')
        >>> files_delete2(['C:/myfile.tmp', 'C:/otherfile.log'])
    """
    if isinstance(filenames, str):
        filenames = [filenames]

    for fname in filenames:
        fname = _path.normpath(fname)
        if file_exists(fname):
            _os.remove(fname)


def file_delete(fname: str) -> None:
    """Delete a single file

    Is normpathed first

    Args:
        fname (str): file to be deleted

    Returns:
        None
    """
    files_delete2(fname)


def files_delete_wildcarded(root: str, match=(), not_match=(), recurse=False, show_progress: bool = False, init_msg: str = '') -> int:
    """
    Delete files that match or do not match
    match and not match.

    Not recursive.

    Args:
        root (str): the root dir
        match (str, list, tuple): Delete if any item in match is in filename
        not_match (str, list, tuple): Delete if any item in not_match is not in filename
        recurse (bool): recurse subfolders
        show_progress (bool): Show progress bar in terminal
        init_msg (str): Passed to the progress bar

    Returns:
        int: number of files deleted
    """
    if not init_msg and show_progress:
        init_msg = 'Deleting files from %s' % _path.normpath(root)

    files_ = [f for f in file_list_generator1(root, '*', recurse=recurse)]
    if show_progress:
        PP = PrintProgress(iter_=files_, init_msg=init_msg)
    if isinstance(match, str): match = [match]
    if isinstance(not_match, str): not_match = [not_match]
    i = 0
    for f in files_:
        _, fname, _ = get_file_parts2(f)
        if match:
            if _baselib.list_member_in_str(fname, match):
                file_delete(f)
                i += 1

        if not_match:
            if not _baselib.list_member_in_str(fname, not_match):
                file_delete(f)
                i += 1

        if show_progress:
            PP.increment()  # noqa
    return i


def file_delete2(fname, silent=True):
    fname = _path.normpath(fname)
    if silent:
        with _fuckit:
            _os.remove(fname)
    else:
        _os.remove(fname)


def files_delete(folder: str, delsubdirs: bool = False) -> None:
    """
    Delete all files in folder

    Args:
        folder (str): The folder
        delsubdirs (bool): Delete subdirs as well

    Returns:
        None

    Examples:
        >>> files_delete('C:/TEMP', True)
    """
    folder = _path.normpath(folder)
    if not _path.exists(folder):
        return

    for the_file in _os.listdir(folder):
        file_path = _path.normpath(_path.join(folder, the_file))
        try:
            if _path.isfile(file_path):
                _os.unlink(file_path)
            elif _path.isdir(file_path):
                if delsubdirs:
                    _shutil.rmtree(file_path)
        except Exception as _:
            print('Could not clear summary file(s). They are probably being used by tensorboard')


def get_temp_fname(suffix: str = '', prefix: str = '', name_only: bool = False) -> str:
    """
    Get a random filename, rooted in the users temporary directory (%TEMP%)

    Args:
        suffix (str): Suffix, use to define an extension
        prefix (str): Prefix
        name_only (bool): exclude path from basename

    Returns:
        str: the temporary file name, stored in the temp dir

    Examples:
        >>> get_temp_fname('.gdb', '__')
        'C:\\Users\\admin\\AppData\\Local\\Temp\\__8d2zq_9m.gdb'
    """

    f = _tempfile.mktemp(suffix, prefix)
    if name_only:
        _, f, _ = get_file_parts2(f)
    return f


def get_file_name2(fld: str, ext: str = '', length: int = 3) -> str:
    """(str, str, int)-> str
    Generate a random filename from alpha characters only.
    Ensures the generated name does not exist in "fld"

    Args:
        fld (str): root folder
        ext (str): extension
        length (int): length of name to generate, excluding extension

    Returns:
        str: the random file name

    Examples:
        >>> get_file_name2('C:\temp', '.txt', 4)
        'C:/temp/ABeD.txt'

        # Just a random string of length 4
        >>> get_file_name2(length=4)
        'ABeD'
    """
    n = 0
    while True:
        s = _path.normpath(_path.join(fld, '%s%s' % (_stringslib.rndstr(length), ext)))
        if not file_exists(s):
            break
        n += 1
        if n > 20:
            raise StopIteration('Too many iterations creating unique filename')
    return s


def get_file_name(path: str = '', prefix: str = '', ext: str = '.txt') -> str:
    """
    Returns a filename, based on a datetime stamp.

    Args:
        path (str):  path to use, if path='', use CWD,  if None, then just the filename is returned
        prefix (str): prefix to use
        ext (str): extension

    Returns:
        str: A datetime stamped file name

    Notes:
        See get_file_name2 if you want to get just a random file name by specifying a file name length.
    """
    if path == '':
        path = _os.getcwd()

    return _path.normpath(_path.join(path,
                                     prefix + _stringslib.datetime_stamp() + _stringslib.add_left(ext,
                                                                                                  _path.extsep)))


def folder_open(folder='.'):
    """(_string) -> void
    opens a windows folder at path folder"""
    if _os.name == 'nt':
        folder = folder.replace('/', '\\')

    try:
        _subprocess.check_call(['explorer', folder])
    except:
        pass


def notepadpp_open_file(filename):
    """(str) -> void
    opens filename in notepad++

    File name should be in the C:\\dirA\\dirB\\xx.txt format
    """
    with _fuckit:
        openpth = _NOTEPADPP_PATH + ' ' + '"' + filename + '"'
        _subprocess.Popen(openpth)


def open_file(filename: str) -> None:
    """
        Open a file with the default program

        Args:
            filename (str): file path

        Returns: None

        Examples:
             >>> open_file('./myfile.xlsx')
        """
    # see https://stackoverflow.com/questions/434597/open-document-with-default-os-application-in-python-both-in-windows-and-mac-os
    if _platform.system() == 'Darwin':  # macOS
        _subprocess.call(('open', filename))
    elif _platform.system() == 'Windows':  # Windows
        _os.startfile(filename)
    else:  # linux variants
        _subprocess.call(('xdg-open', filename))


def file_to_string(file_: str, encoding: str = 'utf-8', strip_newlines: bool = False) -> str:
    """
    Read a text file as a string.

    Args:
        file_ (str): Path to the file to read
        encoding (str): Encoding of the file
        strip_newlines (bool): Remove newlines

    Returns:
        str: The text file as a string

    Examples:
        >>> file_to_string('c:/my.txt')
        'the quick brown fox'
    """

    file_ = _path.normpath(file_)
    if strip_newlines:
        with open(file_, mode='r', encoding=encoding) as file:
            return file.read().replace('\n', '')

    with open(file_, mode='r', encoding=encoding) as file:
        return file.read()


def write_to_file(results, prefix='', open_in_npp=True, full_file_path='', sep='\n'):
    """
    (str|iterable, str, bool, str, str) -> str
    Takes result_text and writes it to a file in the cwd.
    Prints out the file name at the end and opens the folder location

    If results is a _string then it writes out the _string, otherwise it iterates through
    results writing all elements to the file.

    results (str,list,tuple): a string or iterable
    prefix: prefix for file
    open_in_npp: open full_file_path in notepad++  
    full_file_path: saves the file as this, otherwise creates it in CWD with a datetime stamp
    sep: seperator if results is iterable

    Returns: the fully qualified filename

  
    Example:
        >>> List = [1,2,3,4]
        >>> write_to_file(List, prefix='', open_in_npp=True, full_file_path='c:/temp/results.txt')
    """
    if full_file_path == '':
        filename = _os.getcwd() + '\\RESULT' + prefix + \
                   _stringslib.datetime_stamp() + '.txt'
    else:
        fld, f = full_file_path[0:2]
        create_folder(fld)
        filename = full_file_path

    # n = '\r\n' if _get_platform() == 'windows' else '\n'

    with open(filename, 'w+', encoding='utf-8') as f:
        if isinstance(results, str):
            f.write(results)
        else:
            for s in results:
                f.write('%s%s' % (s, sep))

    # print(results)
    # print(filename)
    if open_in_npp:
        if get_platform() == 'windows':
            notepadpp_open_file(filename)
        else:
            print('Option to open in NPP only available on Windows.')
    return filename


def file_count2(pth: (str, list), match='*') -> int:
    """(str, str|iter) -> int
    Get count of files in a folder. Matches should be wildcarded.

    Args:
        pth: The folder or folders to count
        match: Starred strings or list of strings to feed into the glob, e.g. *.jpg. Confirmed as case insensitive on Windows. Not tested on other OSs

    Returns:
        int: The file count

    Examples:
        >>> file_count('C:\temp', '*.txt')
        >>> file_count('C:\temp', ['*.txt', '*.csv'])
    """
    cnt = 0
    if isinstance(pth, str):
        pth = [pth]

    for f in pth:  # noqa
        if type(match) is str:
            f = _path.normpath('%s/%s' % (pth, match))
            cnt += sum(1 for _ in _glob.glob(f))
        else:
            for s in match:
                f_cur = _path.normpath('%s/%s' % (f, s))
                cnt += sum(1 for _ in _glob.glob(f_cur))

    return cnt


def file_copy(src: str, dest: str, rename: bool = False, create_dest: bool = True, dest_is_folder: bool = False) -> str:
    """
    Copy a file from src to dest. Optionally
    rename the file if it already exists in dest.

    Can create the dest folder if it doesnt exist even when
    dest is a folder or a full file name.

    Args:
        src: source file path
        dest: destination folder or full file path
        rename: create a new file if dest exists
        create_dest: create the destination folder if it does not exist
        dest_is_folder: destination is not a filename but a folder

    Returns:
        str: the name of the created file

    Examples:
        >>> file_copy('c:/temp/myfile.txt', 'c:/temp/newfolder/myfile.txt', create_dest=True,  dest_is_folder=False)
        >>> file_copy('c:/temp/myfile.txt', 'c:/temp/subfolder', create_dest=True, dest_is_folder=True)
    """
    if dest_is_folder:
        _, fname, _ = get_file_parts2(src)
        if not folder_exists(dest) and create_dest:
            _os.mkdir(dest)
        dest = _path.join(dest, fname)
    else:
        pth, fname, ext = get_file_parts(dest)
        if not folder_exists(pth) and create_dest:
            _os.mkdir(pth)

    cnt = 0
    if rename and file_exists(dest):
        pth, fname, ext = get_file_parts(dest)
        dest = _path.join(pth, '%s%s%s' % (fname, _stringslib.rndstr(4), ext))
        while file_exists(dest):
            cnt += 1
            dest = _path.join(pth, '%s%s%s' % (fname, _stringslib.rndstr(4), ext))
            if cnt > 1000:  # safety
                break

    _shutil.copy2(src, dest)
    return dest


def files_copy(from_: str, tofld: str, delete_=False, showprogress: bool = False) -> int:
    """
    Copy files matching from

    Args:
        from_ (str): Wildcarded path
        tofld (str): Folder tocopy files matching fname to
        delete_ (bool): Delete, making this a move, not a copy
        showprogress (bool): Print progress bar to terminal

    Returns:
        int: number of files copied

    Notes:
        files_move is quicker for move operations (i.e. passing delete_ = True here). Also see files_copy2
        See files_copy3 for a simple method that recurses and only copies new/updated files

    Examples:
        >>> files_copy('C:/TEMP/*.*', 'C:/TEMP/SUBDIR')
        15
    """
    from_ = _path.normpath(from_)
    tofld = _path.normpath(tofld)
    i = 0

    if showprogress:
        PP = PrintProgress(iter_=_glob.glob(from_))
    for f in _glob.glob(from_):
        _shutil.copy2(f, tofld)
        if delete_:
            with _fuckit:
                _os.unlink(f)
        i += 1
        if showprogress:
            PP.increment()  # noqa
    return i


def files_copy2(from_: str, tofld: str, file_match: (str, list[str], None) = '', delete_: bool = False, showprogress: bool = False) -> int:
    """
    Copy files, includes an option to partially match the file name

    Args:
        from_ (str): Wildcarded path
        file_match (str, list[str], None): List of string to match against file name (including the extension), e.g. ['.pdf', 'march_images'], would be *.pdf* OR *march_images*
        tofld (str): Folder tocopy files matching fname to
        delete_ (bool): Delete, making this a move, not a copy
        showprogress (bool): Print progress bar to terminal

    Raises:
        ValueError: If from_ is a directory. It should be a wildcarded path.

    Returns:
        int: number of files copied

    Notes:
        files_move is quicker for move operations (i.e. passing delete_ = True here)
        See files_copy3 for a simple method that recurses and only copies new/updated files

    Examples:
        >>> files_copy2('C:/TEMP/*.*', 'C:/TEMP/SUBDIR', file_match= ['.pdf', 'march_images'])  # noqa
        15
    """
    from_ = _path.normpath(from_)
    tofld = _path.normpath(tofld)
    if folder_exists(from_):
        raise ValueError('Looks like you passed a bare directory. You need to pass a wildcarded argument for from_, e.g. C:/temp/*.*')
    if isinstance(file_match, str): file_match = [file_match]
    i = 0

    if showprogress:
        PP = PrintProgress(iter_=_glob.glob(from_))

    for f in _glob.glob(from_):
        if _baselib.list_member_in_str(get_file_parts2(f)[1], map(str, file_match), ignore_case=True):
            _shutil.copy2(f, tofld)

            if delete_:
                with _fuckit:
                    _os.unlink(f)
            i += 1
        if showprogress:
            PP.increment()  # noqa
    return i


def files_move(from_: str, tofld: str, delete_on_exists: bool = True, showprogress: bool = False) -> int:
    """
    Copy files matching from

    Args:
        from_ (str): Wildcarded path
        tofld (str): Folder tocopy files matching fname to
        delete_on_exists (bool): shutil.move fails if the destination exists. Force deletion of the destination file first.
        showprogress (bool): Print progress bar to terminal

    Returns:
        int: number of files copied

    Notes:
        Performs normpaths on fname and tofld.

    Examples:
        >>> files_move('C:/TEMP/*.*', 'C:/TEMP/SUBDIR')
        15
    """
    from_ = _path.normpath(from_)
    tofld = _path.normpath(tofld)
    i = 0

    if showprogress:
        PP = PrintProgress(iter_=_glob.glob(from_), init_msg='Moving files to %s' % tofld)
    for f in _glob.glob(from_):
        if delete_on_exists:
            file_delete(fixp(tofld, get_file_parts2(f)[1]))
        _shutil.move(f, tofld)
        if showprogress:
            PP.increment()  # noqa
    return i


def files_rename(root: str, match: str, replace_with: str, rename_in_place: bool = True, exts: tuple[str] = ('*.*',)):
    """
    Rename files using a case sensitive search/replace.

    Consider using files_rename_apply for more flexibility.

    Also when renaming, if a file already matches, it will rename, appending an underscored incremental count to the file name.

    For example:
        'my.jpg' is to be renamed 'your.jpg', but 'your.jpg' already exists (in root, or in root/renamed).
        Then 'my.jpg' will be renamed to 'your_1.jpg'

    Args:
        root ():
        match ():
        replace_with ():
        rename_in_place ():
        exts: extensions to match

    Returns:
        None
    """
    if not rename_in_place:
        renamed_fld = _path.normpath('%s/renamed' % root)
        create_folder(renamed_fld)

    i = sum([1 for _ in file_list_generator_dfe(root, exts, recurse=False)])
    if i == 0:
        print('No files match criteria. Exiting ...')

    PP = PrintProgress(i)

    for d, f, e, ffn in file_list_generator_dfe(root, exts, recurse=False):
        if match in f:
            new_file_name = f.replace(match, replace_with)
        else:
            PP.increment()
            continue

        if rename_in_place:
            fnew_base = _path.normpath('%s/%s' % (root, new_file_name))
            fnew = fnew_base
            n = 0
            while True:
                if file_exists(fnew):
                    n += 1
                    d, f, e = get_file_parts(fnew_base)
                    s = '%s_%s%s' % (f, n, e)
                    fnew = fixp(d, s)
                else:
                    break

            _os.rename(ffn, fnew)
        else:
            fnew_base = _path.normpath('%s/%s' % (renamed_fld, new_file_name))  # noqa
            fnew = fnew_base
            n = 0
            while True:
                if file_exists(fnew):
                    n += 1
                    d, f, e = get_file_parts(fnew_base)
                    s = '%s_%s%s' % (f, n, e)
                    fnew = fixp(renamed_fld, s)
                else:
                    break
            file_copy(ffn, fnew)
        PP.increment()


def files_rename_apply(root: str, match: str, func, rename_in_place: bool = True, exts=('*.*',)):
    """
    Apply a function to each file, where the func output is the new file name.

    The function is applied to the file name, including the extension.

    Also when renaming, if a file already matches, it will rename, appending an underscored incremental count to the file name.

    For example:
        'my.jpg' is to be renamed 'your.jpg', but 'your.jpg' already exists (in root, or in root/renamed).
        Then 'my.jpg' will be renamed to 'your_1.jpg'

    Args:
        root: The dir
        match: Single string to match files on, all files must contain match (pass an empty string or None to process all files with matched extensions).
        func: function, should accept one argument and return a string
        rename_in_place: rename files inplace, otherwise creates a subfolder renamed in root and creates renamed files here
        exts: Extensions to match

    Returns:
        None

    Examples:

        Convert file names to lower case
        >>> files_rename_apply('C:/temp', 'TMP', lambda filename: filename.lower)
    """
    if not rename_in_place:
        renamed_fld = _path.normpath('%s/renamed' % root)
        create_folder(renamed_fld)

    i = sum([1 for _ in file_list_generator_dfe(root, exts, recurse=False)])
    if i == 0:
        print('No files match criteria. Exiting ...')
    PP = PrintProgress(i)

    for d, f, e, ffn in file_list_generator_dfe(root, exts, recurse=False):
        if match in f or not match:
            try:
                new_file_name = func(f)
            except:
                print('Failed to rename file %s. Skipping ...' % f)
                PP.increment()
                continue
        else:
            PP.increment()
            continue

        if rename_in_place:
            fnew_base = _path.normpath('%s/%s' % (root, new_file_name))
            fnew = fnew_base
            n = 0
            while True:
                if file_exists(fnew):
                    n += 1
                    d, f, e = get_file_parts(fnew_base)
                    s = '%s_%s%s' % (f, n, e)
                    fnew = fixp(d, s)
                else:
                    break

            _os.rename(ffn, fnew)
        else:
            fnew_base = _path.normpath('%s/%s' % (renamed_fld, new_file_name))  # noqa
            fnew = fnew_base
            n = 0
            while True:
                if file_exists(fnew):
                    n += 1
                    d, f, e = get_file_parts(fnew_base)
                    s = '%s_%s%s' % (f, n, e)
                    fnew = fixp(renamed_fld, s)
                else:
                    break

            file_copy(ffn, fnew)
        PP.increment()
        
        
def file_move_to_fold(root: str, wildcards: any, match: str, subfold: str) -> int:
    """
    Move a file to a folder, where file has a partial match to a string and
    you specify the subfolder name.

    Args:
        root: Root dir with files to move
        wildcards (str, list): file extensions to match, e.g. ['*.pdf', '*.docx'], set to "*" or None for all file extensions
        match (str): partial match to identify file to move. Matches tested against file basename.
        subfold (str): subfolder

    Returns:
        int: number of files moved

    Examples:
        >>> file_move_to_fold('C:/temp', '*.pdf', 'myfile', 'subdir')
        1
    """
    # TODO Debug me
    n = 0
    if isinstance(wildcards, str):
        wildcards = [wildcards]

    for _, f, _, fname in file_list_generator_dfe(root, wildcards, recurse=False):
        if match not in f:
            continue
        dest = fixp(root, subfold)
        create_folder(dest)
        file_move(fname, dest)
        n += 1
    return n


def file_move(fname: str, tofld: str, delete_on_exists: bool = True) -> None:
    """
    Copy files matching from

    Args:
        fname (str): file name
        tofld (str): Folder to copy file to
        delete_on_exists (bool): shutil.move fails if the destination exists. Force deletion of the destination file first.

    Returns:
        int: number of files copied

    Notes:
        Performs normpaths on from_ and tofld.

    Examples:
        >>> file_move('C:/TEMP/my.pdf', 'C:/TEMP/SUBDIR')
    """
    fname = _path.normpath(fname)
    tofld = _path.normpath(tofld)

    if delete_on_exists:
        file_delete(fixp(tofld, get_file_parts2(fname)[1]))
    _shutil.move(fname, tofld)


def folder_last_created_age(src: str) -> tuple[_baselib.TimeDelta, str]:
    """
    Get the file last created in folder src.

    Args:
        src (str): Root folder

    Returns:
        tuple[_baselib.TimeDelta, str]: A TimeDelta instance from funclite.baselib and the actual folder detected as last created one

    Examples:

        >>> folder_last_created_age('C:/temp')[1]
        'C:/temp/latest'


        >>> folder_last_created_age('C:/temp')[0].as_days
        8
    """
    fld = folder_last_created(src)
    return _baselib.TimeDelta.TimeDelta(_datetime.datetime.now() - folder_date_created(fld)), fld


def file_modification_date(file_name: str) -> _datetime.datetime:
    """Get file modification date as a datetime

    """
    file_name = _path.normpath(file_name)
    t = _path.getmtime(file_name)
    return _datetime.datetime.fromtimestamp(t)

def file_age(file_name: str, time_unit: str = 'days') -> float:
    """Get age of file

    Args:
        file_name (str): the file
        time_unit (str): units, supports "days", "hours", "seconds"

    Raises:
        ValueError: If time_unit argument was invalid

    Returns:
        float: file age in requested time units

    Notes:
        file_name is normpathed

    Examples:

        >>> file_age('C:/my.txt', 'hours')
        15.123
    """
    file_name = _path.normpath(file_name)
    if time_unit not in ['days', 'hours', 'seconds', 'minutes']:
        raise ValueError('time_unit value "%s" invalid. Use "days", "hours", "seconds" or "minutes"' % time_unit)

    td = _datetime.datetime.now() - file_creation_date(file_name)
    if time_unit == 'days':
        return _baselib.TimeDelta(days=td.days, microseconds=td.microseconds, seconds=td.seconds).as_days
    if time_unit == 'seconds':
        return _baselib.TimeDelta(days=td.days, microseconds=td.microseconds, seconds=td.seconds).as_seconds  # noqa
    if time_unit == 'minutes':
        return _baselib.TimeDelta(days=td.days, microseconds=td.microseconds, seconds=td.seconds).as_mins  # noqa
    if time_unit == 'hours':
        return _baselib.TimeDelta(days=td.days, microseconds=td.microseconds, seconds=td.seconds).as_hours  # noqa

def file_creation_date(file_name: str) -> _datetime.datetime:
    """Get file creation date as a datetime

    """
    file_name = _path.normpath(file_name)
    t = _path.getctime(file_name)
    return _datetime.datetime.fromtimestamp(t)


def file_create(file_name: str, s: str = '') -> None:
    """
    Creates file and write s to it if it doesnt exist

    Args:
        file_name (str): File to create and write s to
        s (str): The text to write to file_name

    Returns:
        None

    Examples:

        Write to a file

        >>> file_create('C:/my.txt', 'The quick brown fox')
    """
    if not _path.isfile(file_name):
        write_to_eof(file_name, s)


def fixp(*args) -> str:
    """
    basically path.normpath accepting multiple path parts.

    Args:
        args: string arguments

    Returns:
        str: The fixed path

    Examples:

        >>> fixp('C:\', 'temp', 'my.txt')
        'C:/temp/my.txt'
    """
    s = ''
    for u in args:
        s = _path.join(s, u)  # noqa
    return _path.normpath(s)


def fix(r: str, s: str, mkdir: bool = False) -> str:
    """Concatenate and normpath

    Args:
        r (str): root path
        s (str): subfolder like string
        mkdir (bool): If true, create the dir

    Returns:
        str: The fixed path
    """
    out = _path.normpath(_path.join(r, s))
    if mkdir: create_folder(out)
    return out


def file_exists(file_name: str) -> bool:
    """
    Returns true if file exists, else False.

    Args:
        file_name (str): The file

    Returns:
        bool: True if exists else false
    """
    file_name = _path.normpath(file_name)
    if isinstance(file_name, str):
        return _path.isfile(fixp(file_name))

    return False


def file_read_write_toggle(fname: str, set_read_only: bool):
    """
    Toggle file to read only or write. Does not raise an error.

    Args:
        fname (str): file
        set_read_only (bool): Read only status

    Returns: None

    Examples:

        Set read only

        >>> file_read_write_toggle('C:/my.txt', True)


        Set write

        >>> file_read_write_toggle('C:/my.txt', False)
    """
    with _fuckit:  # if this fails, not end of world .. ignore error and leave it to the caller to raise/capture the error
        if set_read_only:
            _os.chmod(fname, _stat.S_IREAD)
        else:
            _os.chmod(fname, _stat.S_IWRITE)


def file_rename_date_stamped(file_name: str) -> str:
    """
    Rename a file apending an iso date stamp to the end.

    Args:
        file_name:

    Returns:
        str: The name of the renamed file, or empty string if file_name did not exist

    Notes:
        If the renamed filename already exists, add a 3 letter length random suffix to the filename

    Examples:

        All good

        >>> file_rename_date_stamped('c:/myfile.txt')
        'C:/myfile_2022-10-01.txt'


        The proposed renamed file name already exists

        >>> file_rename_date_stamped('c:/myfile.txt')
        'C:/myfile_2022-10-01_3dP.txt'
    """
    s = _path.normpath(file_name)
    if file_exists(s):
        d, f, e = get_file_parts(s)
        bn = '%s_%s.%s' % (f, pretty_date_now(), e)
        fname = fix(d, bn)
        try:
            _os.rename(s, fname)
        except:
            d, f, e = get_file_parts(s)
            bn = '%s_%s%s.%s' % (f, pretty_date_now(), '_%s' % _stringslib.rndstr(3), e)
            fname = fix(d, bn)
            _os.rename(s, fname)
        return fname
    return ''

def file_size(file_name: str, units: str = 'bytes') -> float:
    """
    Get size of a file

    Args:
        file_name (str): The file name. Is normpathed
        units (str): Supports 'bt|bits', 'b|bytes', 'kb|kilobytes', 'gb|gigabytes', 'mb|megabytes', 'tb|terabytes'

    Returns:
        float: The file size in specified units

    Notes:
        Defaults to bytes id units is invalid

    Examples:
        >>> file_size('myfile.txt')
        1024
        >>> file_size('myfile.txt', 'kb')
        1
    """
    factor = 1
    sz = _os.stat(_path.normpath(file_name)).st_size
    units = units.lower()
    if units in ['kb', 'kilobytes']:
        factor = 1024
    elif units in ['mb', 'megabytes']:
        factor = 1024 * 1024
    elif units in ['gb', 'gigabytes']:
        factor = 1024 * 1024 * 1024
    elif units in ['tb', 'terabytes']:
        factor = 1024 * 1024 * 1024 * 1024
    elif units in ['bt', 'bits']:
        factor = 1 / 8
    return sz / float(factor)


def folder_date_created(fld: str) -> _datetime.datetime:
    """
    Folder created date as datetime instance

    Args:
        fld (str): folder

    Raises:
        ValueError: If fld was not a folder

    Returns:
        datetime: A datetime.datetime instance

    Examples:
        >>> print(folder_date_created('C:/temp'))
        datetime.datetime(2022, 11, 17, 11, 11, 0, 24340)
    """
    fld = _path.normpath(fld)
    if folder_exists(fld):
        return _datetime.datetime.fromtimestamp(_pathlib.Path(fld).stat().st_ctime)
    raise ValueError('%s was not a folder' % fld)


def folder_date_modified(fld: str) -> _datetime.datetime:
    """
    Folder modified date as datetime instance

    Args:
        fld (str): folder

    Raises:
        ValueError: If fld was not a folder

    Returns:
        datetime: A datetime.datetime instance

    Examples:
        >>> print(folder_date_created('C:/temp'))
        datetime.datetime(2022, 11, 17, 11, 11, 0, 24340)
    """
    fld = _path.normpath(fld)
    if folder_exists(fld):
        return _datetime.datetime.fromtimestamp(_pathlib.Path(fld).stat().st_mtime)
    raise ValueError('%s was not a folder' % fld)


def folder_last_created(root: str) -> str:
    """Get last created folder in folder root

    Args:
        root (str): The root folder

    Returns:
        str: The latest created folder
    """
    root = _path.normpath(root)
    return _path.normpath(max(_glob.glob(_path.join(root, '*/')), key=_path.getctime))


def folder_last_modified(root: str) -> str:
    """Get last modified folder in folder root

    Args:
        root (str): The root folder

    Returns:
        str: The latest modified folder
    """
    root = _path.normpath(root)
    return _path.normpath(max(_glob.glob(_path.join(root, '*/')), key=_path.getmtime))


def folder_exists(folder_name: str) -> bool:
    """Check if folder exists, does not raise an error.

    Args:
        folder_name (str, any): folder name. IF folder_name is not a string, return false.

    Returns:
        bool: True if exists, else false
        any: False if folder_name is not a string.

    Notes:
        Why? We don't raise an error if folder_name is None
    """
    if not isinstance(folder_name, str):
        return False
    return _path.isdir(_path.normpath(folder_name))


def create_folder(folder_name):
    """(str) -> void
    creates a folder

    Note in windows that a  folder and a file cannot share the same name.
    path_exists returns True for a file or a folder, which is correct behaviour.
    """
    folder_name = _path.normpath(folder_name)
    if not _path.exists(folder_name):
        _os.makedirs(folder_name)


folder_create = create_folder  # in keeping with other folder funcs, dont break existing code


def folder_delete(fld: str):
    """
    Delete a folder. Calls shutil.rmtree. Suppresses all errors.

    Args:
        fld (str): the folder

    Returns:
        None
    """
    fld = _path.normpath(fld)
    with _fuckit:
        _shutil.rmtree(fld, ignore_errors=True)


def folders_delete_empty(root: str, recursive: bool = False) -> list[str]:
    """
    Delete empty folders in root

    Args:
        root:  The root folder
        recursive: recurse through subfolders

    Returns:
        list of folders which were deleted
    """
    deleted = set()
    root = _path.normpath(root)

    if recursive:
        for current_dir, subdirs, files in _os.walk(root, topdown=False):
            still_has_subdirs = False
            for subdir in subdirs:
                if _os.path.join(current_dir, subdir) not in deleted:
                    still_has_subdirs = True
                    break

            if not any(files) and not still_has_subdirs:
                _os.rmdir(current_dir)
                deleted.add(current_dir)
    else:
        for current_dir, subdirs, files in _os.walk(root, topdown=True):
            for subdir in subdirs:
                pth = _path.join(current_dir, subdir)
                if not folder_has_files(pth):
                    _os.rmdir(pth)
                    deleted.add(pth)
            break

    return sorted(list(deleted))

# endregion


# region console stuff
def input_int(prompt='Input number', default=0):
    """get console input from user and force to int"""
    try:
        inp = input
    except NameError:
        pass
    return int(_stringslib.read_number(inp(prompt), default))  # noqa


def print_progress(iteration,
                   total,
                   prefix='',
                   suffix='',
                   decimals=2,
                   bar_length=30):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix _string (Str)
        suffix      - Optional  : suffix _string (Str)
        decimals    - Optional  : number of decimals in percent complete (Int)
        bar_length   - Optional  : character length of progbar (Int)
    """
    if total == 0:
        _warn('Total iterations was set to zero.')
        return

    filled_length = int(round(bar_length * iteration / float(total))) if total > 0 else 0
    if iteration / float(total) > 1:
        total = iteration
    percents = round(100.00 * (iteration / float(total)), decimals)
    if bar_length > 0:
        progbar = '#' * filled_length + '-' * (bar_length - filled_length)
    else:
        progbar = ''

    _sys.stdout.write('%s [%s] %s%s %s\r' % (prefix, progbar, percents, '%', suffix)), _sys.stdout.flush()
    if iteration == total:
        print("\n")


# In the consider using tqdm
class PrintProgressFlash:
    """class to print a progress flasher
    to console

    Args:
        ticks:  max size of chars before reset,
                set to None to print fixed length flasher
        msg:
                print msg to console
    """

    def __init__(self, ticks=None, msg='\n'):
        self.ticks = ticks
        print(msg)

    def update(self):
        """update state"""
        secs = _datetime.datetime.timetuple(_datetime.datetime.now()).tm_sec

        if self.ticks is None:
            if secs % 3 == 0:
                s = '////'
            elif secs % 2 == 0:
                s = '||||'
            else:
                s = '\\\\\\\\'
        else:
            n = int(self.ticks * (secs / 60))
            s = '#' * n + ' ' * (self.ticks - n)  # print spaces at end

        _sys.stdout.write('%s\r' % s)
        _sys.stdout.flush()


# In the future consider using tqdm
class PrintProgress:
    """Class for dos progress bar. Implement as global for module level progress

    Example:
        from funclite.iolib import PrintProgress as PP
        pp = PP(len(_glob(img_path)))
        pp.iteration = 1
        pp.increment

        iter_ = <a thing which can be iterated to get a maximum>
        pp = PP(yield_or_generator=yieldfunc)
    """

    def __init__(self, maximum=0, bar_length=30, init_msg='\n', iter_=None):
        print(init_msg)

        if iter_:
            self.maximum = sum([1 for _ in iter_])
        elif isinstance(maximum, (int, float)):
            self.maximum = int(maximum)
        else:
            self.maximum = len(maximum)  # noqa

        self.suffix = ''
        self.bar_length = bar_length
        self.iteration = 1
        self.StopWatch = _StopWatch(event_name=init_msg)
        self._max_suffix_len = 0

    def increment(self, step=1, suffix='', show_time_left=True):
        """(int, str, bool) -> void
        Advance the counter step ticks.

        Parameters:
            step: number of ticks (events) to advance
            suffix: textto append to end of bar
            show_time_left: overrides suffix, append estimated time left
        """
        self.StopWatch.lap(step)
        if show_time_left:
            suffix = self.StopWatch.pretty_remaining_global(self.maximum - self.iteration)
        self.suffix = suffix
        print_progress(self.iteration, self.maximum, prefix='%i of %i' % (self.iteration, self.maximum), bar_length=self.bar_length, suffix=self._get_suffix(suffix))
        self.iteration += step

    def reset(self, maximum: (int, None) = None):
        """Reset the counter. Set max if need to change total expected iterations.

        Args:
            maximum (int, None): Reset to counter to 0. Change the maximum if maximum is an int.

        Returns:
            None
        """
        if maximum:
            self.maximum = maximum
        self.iteration = 1
        self.StopWatch.reset()

    def _get_suffix(self, suffix):
        """get padded suffix so we overwrite end chars"""
        if suffix == '': return ''
        if len(suffix) > self._max_suffix_len:
            self._max_suffix_len = len(suffix)
        return suffix.ljust(self._max_suffix_len, ' ')


# endregion

def wait_key(msg=''):
    """ (str) -> str
    Wait for a key press on the console and returns it.
    msg:
        prints msg if not empty
    """
    result = None
    if msg:
        print(msg)

    if _os.name == 'nt':
        import msvcrt
        result = msvcrt.getch()
    else:
        import termios as _termios
        fd = _sys.stdin.fileno()

        oldterm = _termios.tcgetattr(fd)
        newattr = _termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~_termios.ICANON & ~_termios.ECHO
        _termios.tcsetattr(fd, _termios.TCSANOW, newattr)

        try:
            result = _sys.stdin.read(1)
        except IOError:
            pass
        finally:
            _termios.tcsetattr(fd, _termios.TCSAFLUSH, oldterm)

    if isinstance(result, bytes):
        return result.decode()

    return result


@_contextmanager
def quite(stdout=True, stderr=True):
    """(bool, bool) -> void
    Stop messages and errors being sent to the console
    """
    with open(_os.devnull, "w", encoding="utf-8") as devnull:
        old_stdout = _sys.stdout
        old_stderr = _sys.stderr
        if stdout:
            _sys.stdout = devnull

        if stderr:
            _sys.stderr = devnull
        try:
            yield
        finally:
            _sys.stdout = old_stdout
            _sys.stderr = old_stderr


def time_pretty(seconds):
    """(float) -> str
    Return a prettified time interval
    for printing
    """
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(_rndnorm(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%dd %dh %dm %ds' % (sign_string, days, hours, minutes, seconds)
    if hours > 0:
        return '%s%dh %dm %ds' % (sign_string, hours, minutes, seconds)
    if minutes > 0:
        return '%s%dm %ds' % (sign_string, minutes, seconds)

    return '%s%ds' % (sign_string, seconds)


# this is also in baselib
# but don't risk circular imports
def pickle(obj: any, fname: str) -> None:
    """
    Save object to fname

    Also see unpickle

    Args:
        obj (any): the variable to pickle to the file system
        fname: filename to save the object to

    Returns: None

    Notes:
        Handles creating new folders etc.

    Examples:
        >>> lst = [1]
        >>> pickle(lst, 'c:/mylist.pkl')
    """
    fname = _path.normpath(fname)
    d, _, _ = get_file_parts2(fname)
    create_folder(d)
    with open(fname, 'wb') as f:
        _pickle.dump(obj, f)  # noqa


# this is also in baselib
# but don't risk circular imports
def unpickle(path: str) -> any:
    """(str) -> var|None
    attempts to load a pickled object named path

    Args:
        path (str): Path to the file to unpickle

    Returns:
        any: None if file doesnt exist, else the unpickled object

    Examples:
        >>> unpickle('c:/mylist.pkl')
        [1,2,3]
    """
    path = _path.normpath(path)
    if file_exists(path):
        with open(path, 'rb') as myfile:
            return _pickle.load(myfile)
    return None


class Info:
    """Way of grouping info stuff"""
    platform = get_platform


if __name__ == '__main__':
    # Quick debugging here
    # file_count(r'\\nerctbctdb\shared\shared\PROJECTS\WG ERAMMP2 (06810)\2 Field Survey\Data Management\submission\2 images\freshwater\features', wildcards='*', directory_match='2021', recurse=True)
    out_main = folders_delete_empty(r'C:\TEMP\delete_empty_test', recursive=False)
    pass
