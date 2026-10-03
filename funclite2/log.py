# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument
"""
Very simple logging. The log is held in a list in memory and only saved on calling Log.write()

Supports appending to existing log, or overwriting.

Example:
    >>> L = Log('c:/temp/log.log')
    >>> L.log('my message', EnumLogStatus.INFO)
    >>> L.write()
"""
from warnings import warn as _warn
from os import path as _path
from enum import Enum as _Enum

import fuckit as _fuckit

from funclite2 import iolib as _iolib
import funclite2.stringslib as _stringslib



class EnumLogStatus(_Enum):
    """LogStatus"""
    CRITICAL = 1
    WARNING = 2
    INFO = 3

WARN_SIZE_MB = 5

class Log:
    """
    In memory logfile, until it is written

    Args:
        logfile (str): log file path
        overwrite (bool): Append or overwrite to logfile

    Methods:
        log: add an log record to the in-memory log
        clear: clear the in-memory log
        write: write the log out to path defined by logfile

    Examples:
        >>> L = Log('c:/temp/log.log')
        >>> L.log('my message', EnumLogStatus.INFO)
        >>> L._write()  # noqa
    """
    _COL_CNT = 3
    EnumLogStatus = EnumLogStatus  # noqa


    def __init__(self, logfile: str, overwrite: bool = True):
        self.logfile = _path.normpath(logfile)
        self._existed = False
        if _iolib.file_exists(self.logfile):
            self._existed = True
        self._overwrite = overwrite or not self._existed
        self._log = []
        self._read()


    def log(self, msg: str, status=EnumLogStatus.INFO) -> None:
        """
        Log a message to an in memory list.

        Args:
            msg (str): The message to log
            status (EnumLogStatus): The status level of the message

        Returns: None
        """
        msg = msg.replace(',', ';')
        # don't want to bugger up writing invalid chars to the line, otherwise reading
        # the log back in will fail
        include = ';', '.', '<', '>', '(', ')', '-', '+', '@', '#', ':', '~', '{', '}', '[', ']', '!', '£', '$', '%', '&', '*', '=', '_', '?', '/', '|', '\\'
        msg = _stringslib.filter_alphanumeric1(msg, strict=True, allow_cr=False, allow_lf=False, include=include)
        row = [status.name, _stringslib.pretty_date_now(with_time=True), msg]
        assert len(row) == Log._COL_CNT, 'Bad log row count, or _COL_CNT incorrect'
        self._log.append(row)


    def clear(self) -> None:
        """
        Clear all in-memory log messages

        Returns: None
        """
        self._log = []


    def write(self, append: bool = True) -> None:
        """
        Write the in-memory log messages to file.

        Args:
            append (bool): Append or overwrite the log on the file system

        Returns: None
        """
        # We delete the log file in all cases, because we have already read in the entire existing logfile
        # if we are appending.
        if self._log:
            if self._overwrite or not append:
                with _fuckit:
                    _iolib.file_delete(self.logfile)  # just to be sure
                _iolib.writecsv(self.logfile, self._log, header=['status', 'when', 'msg'], inner_as_rows=False, append=False)
            else:
                _iolib.writecsv(self.logfile, self._log, inner_as_rows=False, append=False)



    def _read(self) -> None:
        """Read log from file system if we do not want to overwrite"""
        if not self._overwrite:
            if _iolib.file_exists(self.logfile):
                if _iolib.file_size(self.logfile, 'mb') > WARN_SIZE_MB:
                    _warn('Log file %s is greater than %sMb, consider deleting it.' % (self.logfile, WARN_SIZE_MB))
                self._log = _iolib.readcsv_by_row(self.logfile)



def get_datestamped_name(fld: str, suffix: str = '', ext: str = '.log') -> str:
    """
    Helper to get a datestamped name.

    Args:
        fld (str): The dir inwhich the file is created
        suffix (str): File name suffix, no seperators are assumed, so include in name.
        ext (str): The dotted extension

    Returns:
        str: Full log file name.

    Examples:
        >>> get_datestamped_name('C:/temp', suffix='IMPORT_', ext='.txt')
        'C:/temp/IMPORT_2022-02-01 123944.txt'
    """
    return _path.normpath('%s/%s%s%s' % (fld, suffix, _stringslib.pretty_date_now(with_time=True, time_sep=''), ext))
