# pylint: disable=C0103, too-few-public-methods, locally-disabled, consider-using-enumerate,
# stop-iteration-return, simplifiable-if-statement, stop-iteration-return,
# too-many-return-statements, consider-using-f-string
# unused-variable
"""Decorators, base classes and misc functions
for manipulatin other base classes.

Stick list/tuple/dic functions in here.
"""
import traceback as _traceback
from datetime import timedelta as _timedelta
from datetime import datetime as _datetime
import sys as _sys
import inspect as _inspect
import itertools as _itertools
import pickle as _pickle
import collections as _collections
import random as _random

import operator as _operator
from copy import deepcopy as _deepcopy
from enum import Enum as _Enum
import ast as _ast

import numpy as _np
import dateutil as _dateutil



# region enums
class eDictMatch(_Enum):
    """do dictionaries match
    """
    Exact = 0  # every element matches in both
    Subset = 1  # one dic is a subset of the other
    Superset = 2  # dic is a superset of the other
    Intersects = 3  # some elements match
    Disjoint = 4  # No match
# endregion

# region Decorators
class classproperty(property):
    """class prop decorator, used
    to enable class level properties"""

    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)

    def __set__(self, obj, value):
        super(classproperty, self).__set__(type(obj), value)

    def __delete__(self, obj):
        super(classproperty, self).__delete__(type(obj))
# endregion


# region classes misc
class Switch:
    """ Replicates the C switch statement

    if case(): # default, could also just omit condition or 'if True'
        print "something else!"

    Credit:
        http://code.activestate.com/recipes/410692/.

    Examples:
        >>> v = 'ten'
        >>> for case in Switch(v):
        >>>     if case('one'):
        >>>         print 1
        >>>     if case('two'):
        >>>         print 2
        >>>     if case('ten'):
        >>>         print 10
        >>>     if case('eleven'):
        >>>         print 11
        10
    """
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True

        if self.value in args:  # changed for v1.5, see below
            self.fall = True
            return True
        return False


def dt_week_start_end(dt: (str, _datetime)) -> tuple[_datetime, _datetime]:
    """
    Get start and end date of the week in which dt falls

    Args:
        dt (str, datetime): A datetime, date or string representation of a date in iso formay (yyyy-mm-dd)

    Returns:
        tuple[_datetime, _datetime]: A tuple of week start, week end datetimes

    Notes:
        Monday based start week

    Examples:
        ISO date as string
        >>> dt_week_start_end('2022-12-25')
        datetime.datetime(2022, 12, 23, 0, 0), datetime.datetime(2022, 12, 30, 0, 0)  # noqa

        passing a datetime instance
        >>> dt_week_start_end(datetime.strptime('2022-12-23', '%Y-%m-%d'))  # noqa
        datetime.datetime(2022, 12, 23, 0, 0), datetime.datetime(2022, 12, 30, 0, 0)  # noqa
    """
    if isinstance(dt, str):
        dt = _datetime.strptime(dt, '%Y-%m-%d')

    return dt - _timedelta(days=dt.weekday()), dt - _timedelta(days=dt.weekday()) + _timedelta(days=6)


def date_to_datetime(dt):
    """
    Converts a date instance to a datetime

    Credited to https://stackoverflow.com/a/1937636/5585800

    Args:
        dt (date instance): An instance of datetime.date

    Returns:
        datetime instance
    """
    return _datetime.combine(dt.today(), _datetime.min.time())


class TimeDelta(_timedelta):
    """
    Subclasses datetime.timedelta, adding several methods
    to get total time diff in mins, hours or seconds.
    Also supports friendly print.

    Methods:
        __str__: Overridden __str__ class, with friendly time print
        as_mins: Time diff in mins
        as_hours: Time diff in hours
        as_seconds: Time diff in seconds
        TimeDelta: Create an instance from a timedelta instance

    Notes:
        If timedelta is provided, all other arguments are ignored at initialisation.

    Examples:
        Use as basic timedelta

        >>> datetime.now() - TimeDelta(days=2)  # noqa
        1.1234


        Time conversion to different units

        >>> TimeDelta(days=8).as_hours
        192.0

    Credit:
        Partial credit to https://stackoverflow.com/a/61883517/5585800
    """
    def __str__(self):
        _times = super(TimeDelta, self).__str__().split(':')
        if "," in _times[0]:
            _hour = int(_times[0].split(',')[-1].strip())
            if _hour:
                _times[0] += " hours" if _hour > 1 else " hour"
            else:
                _times[0] = _times[0].split(',')[0]
        else:
            _hour = int(_times[0].strip())
            if _hour:
                _times[0] += " hours" if _hour > 1 else " hour"
            else:
                _times[0] = ""
        _min = int(_times[1])
        if _min:
            _times[1] += " minutes" if _min > 1 else " minute"
        else:
            _times[1] = ""
        _sec = int(_times[2])
        if _sec:
            _times[2] += " seconds" if _sec > 1 else " second"
        else:
            _times[2] = ""
        return ", ".join([i for i in _times if i]).strip(" ,").title()

    @property
    def as_mins(self) -> float:
        """Difference in minutes

        Returns:
            float: Diff in minutes
        """
        return self.as_seconds/60

    @property
    def as_hours(self) -> float:
        """
        Diff in hours

        Returns:
            float: diff in hours
        """
        return self.as_mins/60

    @property
    def as_days(self) -> float:
        """ Diff in days
        Returns:
            float: diff in days
        """
        return self.as_hours/24

    @property
    def as_seconds(self) -> float:
        """Diff in seconds
        Returns:
            float: Diff in seconds
        """
        return self.seconds + (self.microseconds/1e6) + self.days * 86400

    # region statics
    @staticmethod
    def now():
        return _datetime.now()


    @staticmethod
    def TimeDelta(timedelta: _timedelta):
        """
        Args:
            timedelta (datetime.timedelta): A timedelta class used to create a TimeDelta subclass

        Returns:
            TimeDelta: A TimeDelta instance

        Notes:
            This method created as issue with overriding and super(ing) to timedelta.__init__
            Could probably resolve at some point, but this will do for now.
        """
        return TimeDelta(timedelta.days, timedelta.seconds, timedelta.microseconds)
    # endregion
# endregion

# region dict classes
class odict(_collections.OrderedDict):
    """subclass OrderedDict to support item retreival by index
    d = _baselib.odict()
    d[1] = '12'
    """

    def getbyindex(self, ind):
        """(int)->tuple
        Retrieve dictionary key-value pair as a tuple using
        the integer index
        """
        items = list(self.items())
        return items[ind]

# For convieniance, and dont want to break compatibility by renaming odict
DictOrdered = odict

class DictAttributed(dict):
    """
    Small wrapper around dict, which exposes the dict keys as instance fields

    Credit: https://stackoverflow.com/a/1639632/6494418

    Examples:

        >>> D = DictAttributed({"hello": 1, "world": 2, "cat": {"dog": 5}})
        >>> print(D.cat, D.cat.dog, D.cat.items())
        {'dog': 5}, 5, dict_items([('dog', 5)])
    """
    def __getattr__(self, name):
        return self[name] if not isinstance(self[name], dict) else DictAttributed(self[name])

class dictp(dict):
    """allow values to be accessed with partial key match
    dic = {'abc':1}
    d = dictp(dic)
    print(d['a']) # returns 1
    """

    def __getitem__(self, partial_key):
        key = ''
        keys = [k for k in self.keys() if partial_key in k and k.startswith(partial_key)]
        if keys:
            if len(keys) > 1:
                raise KeyError('Partial key matched more than 1 element')

            key = keys[0] if keys else None
        return self.get(key)

    def getp(self, partial_key, d=None):
        """(str, any)->dict item
        Support partial key matches,
        return d if key not found
        """
        keys = [k for k in self.keys() if partial_key in k and k.startswith(partial_key)]
        if keys:
            if len(keys) > 1:
                raise KeyError('Partial key matched more than 1 element')
            key = keys[0] if keys else None
            if key is None:
                return d
            return self.get(key)

        return d

# For convieniance, and dont want to break compatibility by renaming dictp
DictPartialKeyMatches = dictp

class DictKwarg(dict):
    """Dictionary wrapper adding the method kwargs.

    Methods:
        kwargs (dict): Yields keword arguments constructed from the key values (lists) on a 'row like' basis

    Raises:
        ValueError: If the len of the lists do not all match or if the values were not of type list or tuple

    Examples:
        Yield args as kword like dict
        >>> dK = DictKwarg({'age': [75, 20], 'hair': ['bald', 'blonde']})
        >>> for d in dK.kwargs():
        >>>     print(d)
        {'age':12, 'hair':'bald'}
        {'age':20, 'hair':'blonde'}
    """

    def kwargs(self) -> dict:
        """
        Yield the kword arguments as a dict

        Returns:
            dict: A single row from the dict used to instantiate the class instance

        Examples:
            See the class documentation

        """
        for v in self.values():
            if not isinstance(v, (list, tuple)):
                raise ValueError('DictKwarg expects all values to be lists or tuples. Got type %s' % type(v))

        lens = [len(v) for v in self.values()]
        out = dict()
        if len(set(lens)) != 1:
            raise ValueError('All dictionary lists should be the same length.')

        for i in range(lens[0]):
            for k in self.keys():
                out[k] = self[k][i]
            yield out


class DictList(DictKwarg):
    """Easy support for dictionary values as lists.

    Methods:
        keys_from_item: Get a list of all keys where the dictionary values (which are lists) contain a specified value
        kwargs (dict): Yields keword arguments constructed from the key values (lists) on a 'row like' basis

    Notes:
         kwargs method is supported by inheriting from DictKwarg.

    Examples:
        >>> d = DictList()
        >>> d['test'] = 1
        >>> d['test'] = 2
        >>> d['test'] = 3
        >>> d
        {'test': [1, 2, 3]}
        >>> d['other'] = 100
        >>> d
        {'test': [1, 2, 3], 'other': [100]}

        Yield args as kword like dict
        >>> dK = DictList({'age': [75, 20], 'hair': ['bald', 'blonde']})
        >>> for d in dK.kwargs():
        >>>     print(d)
        {'age':12, 'hair':'bald'}
        {'age':20, 'hair':'blonde'}
    """

    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super(DictList, self).__setitem__(key, [])
        self[key].append(value)


    def keys_from_item(self, v) -> (list, None):
        """
        Get the key(s) that contains the value v

        Args:
            v : A value, expected to be in some subset of dictionary values

        Returns:
            None: v not in any of the dict values
            list: List of keys

        Examples:
            >>> DL = DictList({'a':[1,2,3], 'b':[1,10], 'c':[100,120]})
            >>> DL.keys_from_item(1)
            ['a', 'b']

            >>> DL.keys_from_item(100)
            ['c']

            >>> DL.keys_from_item(-10)
            None
        """
        out = list()
        for k, vv in self.items():
            if v in list_flatten(vv):
                out += [k]
        if out:
            return out  # noqa
        return None

    def as_dict(self):
        """
        Get as inbuilt dict. Just returns dict(self)
        Returns: dict
        """
        return dict(self)
# endregion


# region dictionaries
def dic_filter_by_keys(d: dict, keys: (list, tuple)) -> dict:
    """
    Filter a dictionary by a list of keys.
    No filter is applied if "not keys" evaliates to true.

    Args:
        d (dict): Target dict to apply filter
        keys (list, tuple): iterable of keys to remove from dict

    Returns:
        dict: the dictionary sans all keys in keys

    Notes:
        Returns d if "not keys" evaluates to True

    Examples:
        >>> dic_filter_by_keys({'a':1, 'b':2}, ['a'])
        {'b':2}
    """
    if not keys:
        return d
    return {key: d[key] for key in keys}


def dic_filter_by_values(d: dict, v: (list, tuple)) -> dict:
    """
    Filter a dictionary by a list of its values.

    Args:
        d (dict): Target dict to apply filter
        v (list, tuple): iterable of values to remove from dict

    Returns:
        dict: the dictionary sans all members whose value is in v

    Notes:
        Returns d if "not v" evaluates to True

    Examples:
        >>> dic_filter_by_values({'a':1, 'b':2}, [1])
        {2:2}
    """
    if not v:
        return d
    return {itm[0]: itm[1] for itm in d if itm[1] in v}


def dic_merge_two(x_, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x_.copy()
    z.update(y)
    return z


def dic_key_with_max_val(d):
    """(dict)->value
    Get key with largest value

    Examples:
        >>> dic_key_with_max_val({'a':12, 'b':100, 'x':-1})
        'b'
    """
    return max(d, key=lambda key: d[key])

def dic_expand_keys_to_list(d: dict[str:list]) -> list[list]:
    """

    Args:
        d (dict): A dictionary where keys are non-iterables and value are iterables (list)

    Returns:
        list: A nested list. See examples

    Examples:

        >>> dic_expand_to_list({'a':[1, 3]. 'b':['x', 'y']})
        [['a', 1], ['a', 3], ['b', 'x'], ['b', 'y']]
    """
    lst = []
    for k, v in d.items():
        for s in v:
            lst += [[k, s]]
    return lst


def dic_value_counts(d: dict) -> dict:
    """

    Args:
        d (dict): Get count of values in dict d.

    Returns:
        dict: {'value1': n1, 'value2': n2, 'value3': n3}

    Examples:
        >>> dic_value_counts(({'a':'given', 'b':'given', 'c':'bad','d':'good' }))
        {'given': 2, 'bad': 1, 'good': 1}
    """
    return dict(_collections.Counter(d.values()))


def dic_vals_same_len(d) -> bool:
    """
    Check if the values in dictionary d have the same length.

    Args:
        d: dictionary to check

    Returns:
        bool: True of all same length, else false.

    Examples:
        >>> dic_vals_same_len({'a':[1,2,3,4,5], 'b':[1,2,3,4,5]})
        True

        >>> dic_vals_same_len({'a':[1,2,3,4,5], 'b':[2,3,4,5]})
        False
    """
    b = len(set([len(itm[1]) for itm in d.items()])) == 1
    return b


def dic_sort_by_val(d: dict, as_dict: bool = False) -> (list, dict):
    """
    Sort a dictionary by the values, returning as a list or dict

    Args:
        d (dict): dictionary
        as_dict (bool): return as dictionary rather than list

    Returns:
        list: list of tuples, [(k1, v1), (k2, v2), ...]
        dict: Sorted dictionary

    Examples:
        >>> dic_sort_by_val({1:1, 2:10, 3:22, 4:1.03})
        [(1, 1), (4, 1.03), (2, 10), (3, 22)]
    """
    if as_dict:
        return dict(sorted(d.items(), key=lambda item: item[1]))  # noqa
    return sorted(d.items(), key=_operator.itemgetter(1))


def dic_sort_by_key(d: dict, as_dict: bool = False) -> (list, dict):
    """(dict) -> list
    Sort a dictionary by its keys, returning as a list or dict

    Args:
        d (dict): dictionary
        as_dict (bool): return as dictionary rather than list

    Returns:
        list: list of tuples, [(k1, v1), (k2, v2), ...]
        dict: Sorted dictionary

    Examples:
        >>> dic_sort_by_key({1:1, 4:10, 3:22, 2:1.03})
        [(1,1), (2,1.03), (3,22), (4,10)]
    """
    if as_dict:
        return dict(sorted(d.items()))  # noqa
    return sorted(d.items(), key=_operator.itemgetter(0))


def dic_match(a: dict, b: dict) -> ("eDictMatch", None):
    """(dict, dict) -> Enum:eDictMatch
    Compares dictionary a to dictionary b.

    Args:
        a (dict): Dictionary, compared to b
        b (dict): Dictionary, which a is compared to

    Returns:
        eDictMatch: A member of eDictMatch.
        None: If a or b were not dicts

    Notes:
        eDictMatch is defined as follows,
        Exact = 0  # every element matches in both
        Subset = 1  # a is a subset of b
        Superset = 2  # a is a superset b
        Intersects = 3  # some elements match
        Disjoint = 4  # No match

    Examples:
        >>> dic_match({'a':1}, {'a':1, 'b':2})
        eDictMatch.Subset

        >>> dic_match({'a':1, 'b':2}}, {'a':1, 'b':2})
        eDictMatch.Exact
    """
    if not isinstance(a, dict) or not isinstance(a, dict):
        return None  # noqa

    unmatched = False
    matched = False
    b_lst = list(b.items())
    a_lst = list(a.items())

    if len(a_lst) < len(b_lst):
        for i in a_lst:
            if i in b_lst:
                matched = True
            else:
                unmatched = True

        if matched and unmatched:
            return eDictMatch.Intersects

        if not matched:
            return eDictMatch.Disjoint

        if not unmatched:
            return eDictMatch.Subset
        return None  # noqa

    if len(a_lst) > len(b_lst):
        for i in b_lst:
            if i in a_lst:
                matched = True
            else:
                unmatched = True

        if matched and unmatched:
            return eDictMatch.Intersects

        if not matched:
            return eDictMatch.Disjoint

        if not unmatched:
            return eDictMatch.Superset
        return None  # noqa
    # same length
    for i in b_lst:
        if i in a_lst:
            matched = True
        else:
            unmatched = True

    if matched and unmatched:
        return eDictMatch.Intersects

    if not matched:
        return eDictMatch.Disjoint

    if not unmatched:
        return eDictMatch.Exact
    return None  # noqa
# endregion

# region lists
def list_filter_by_list(a: list, filt: list) -> list:
    """
    Filter the values in a list which contain substrings in another list.

    Args:
        a (list): The list to filter
        filt (list): The list to use to filter values in a

    Returns:
        list: List a, filtered by wildcard matches of filt[n] in a

    Notes:
        Is case sensitive.
        Useful for doing things like filtering file lists by a list of partial matches.
        Returns a if "not a" evaluates to True

    Examples:
        >>> list_filter_by_list(['aaa','bbb', 'ccc'], ['a', 'bb'])
        ['aaa', 'bbb']
    """
    if not filt or not a:
        return a
    filt = lambda fcs, match: [s for s in fcs if [z for z in match if z in s]]
    return filt(a, filt)

def list_delete_value_pairs(list_a: list, list_b: list, match_value=0) -> None:
    """(list,list,str|number) -> void
    Given two lists, removes matching values pairs occuring
    at same index location. By Ref

    Args:
        list_a (list): first list
        list_b (list): second list
        match_value (any): value to match (and delete if matched)

    Returns:
        None: This method is BY REF

    Notes:
        List arguments are **By Ref**

    Examples:
        >>> a = [1, 0, 2, 0]; b = [2, 0, 2, 1]
        >>> list_delete_value_pairs(a, b)
        >>> a, b
        ([1, 2, 0], [2, 2, 1])

    """
    for ind, value in reversed(list(enumerate(list_a))):
        if value == match_value and list_b[ind] == match_value:
            del list_a[ind]
            del list_b[ind]


def list_index(list_, val):
    """(list, <anything>) -> int|None
    Safely returns the list index which
    matches val, else None

    Parameters:
        list_: a list
        val: the value to find in list

    Returns:
        None if the item not found, else the index of the item in list

    Examples:
        >>> list_index([1,2,3], 2)
        1
        >>> list_index([1,2,3], 5)
        None
    """
    return list_.index(val) if val in list_ else None


def list_get_dups(lst: list, thresh: int = 2, value_list_only: bool = False) -> (list, dict):
    """
    Get a dictionary containing dups in list where
    the key is the duplicate value, and the value is the
    duplicate nr.

    Args:
        lst (list): The list to check
        thresh (int): Duplicate threshhold count, i.e. only consider an value a duplicate if it has >= thresh occurences
        value_list_only (bool): Just return values that are duplicated in a list

    Returns:
        list: If value_list_only is True. An empty list is returned if there on no duplicates
        dict: If value_list_only is False. Keys are the duplicate values, values are the count of duplicates. Returns empty dict of no duplicates.

    Examples:

        Default behaviour, all duplicates\n

        >>> list_get_dups([1,1,2,3,4,4,4])
        {1:2, 4:3}

        Only count duplicates with 3 or more occurences

        >>> list_get_dups([1,2,3,4,4], thresh=3)
        {}

        Unique list of the values with duplicates

        >>> list_get_dups([1, 1, 2, 3, 4, 4, 4, 5, 5, 5], thresh=3, value_list_only=True)
        [4, 5]
    """
    my_dict = {i: lst.count(i) for i in lst}
    out_ = dict(my_dict)  # create a copy
    for k, v in my_dict.items():
        if v < thresh:
            del (out_[k])

    if value_list_only:
        return list(out_.keys())

    return out_  # noqa


def list_add_elementwise(lsts):
    """lists->list
    Add lists elementwise.

    lsts:
        a list of lists with the same nr of elements

    Returns:
        list with summed elements

    Examples:
        >>> list_add_elementwise([[1, 2], [1, 2]])
        [2, 4]
    """
    return list(map(sum, zip(*lsts)))


def list_most_common(L, force_to_string=False):
    """(list, bool)->str|int|float
    Find most _common value in list

    force_to_string:
        make everything a string, use if list
        has mixed types
    """
    if force_to_string:
        Ll = [str(s) for s in L]
    else:
        Ll = L.copy()

    SL = sorted((x, i) for i, x in enumerate(Ll))  # noqa
    groups = _itertools.groupby(SL, key=_operator.itemgetter(0))

    def _auxfun(g):
        _, iterable = g
        count = 0
        min_index = len(Ll)
        for _, where in iterable:
            count += 1
            min_index = min(min_index, where)
        return count, -min_index

    return max(groups, key=_auxfun)[0]


def list_batch(lst: list, batch_sz: int) -> list:
    """
    Yields sublists from list of length "batch_sz"

    Args:
        lst: list to batch
        batch_sz: sublist length

    Yields:
        lists of size "batch_sz", except ofcourse for (potentially) the first or last
    """
    for i in range(0, len(lst), batch_sz):
        yield lst[i:i + batch_sz]


def lists_match(a: list, b: list, ignore_case: bool = False) -> bool:
    """
    Check if the contents of two list match.

    Args:
        a (list): First list
        b (list): Second list
        ignore_case (bool): Ignore case

    Returns:
        bool: If all elements of two lists match, ignoring order

    Notes:
        Considers unique values only, i.e. calls list(set()) on each list
        prior to comparison.

    Examples:
        >>> lists_match(['a', 'c', 'D'], ['c','d','d','a'], ignore_case=True)
        True
        >>> lists_match(['a', 'c', 'D'], ['c','d','d'], ignore_case=True)
        False
    """
    c = list(set(a))
    d = list(set(b))
    if ignore_case:
        return list_sym_diff(list(map(str.lower, c)), list(map(str.lower, d)))['a_and_b'] == len(c) == len(d)
    return list_sym_diff(c, d)['a_and_b'] == len(c) == len(d)


def lists_merge(first_has_priority=True, *args):
    """merge lists, filling in blanks according to
    first_has_priority

    Args:
        first_has_priority (bool): prioritise first to last, otherwise other way
        *args (any): lists as args

    Raises:
        ValueError: If lists are of different lengths

    Returns:
        list: single list

    Examples:
        >>> lists_merge(True, [1,'' ,None,4], ['a',(),3,''], [1,'AZ','',''])  # noqa
        [1, 'AZ', 3, 4]
    """
    if len(set([len(itm) for itm in args])) != 1:
        raise ValueError('All lists must be the same length')

    lsts = _deepcopy(args)
    if not first_has_priority:
        lsts.reverse()  # noqa

    d = {k: None for k in range(len(args[0]))}
    for lst in lsts:
        for i, v in enumerate(lst):
            if not d[i] and v not in (None, '', (), [], {}):  # don't ignore 0's
                d[i] = v
    return d.values()


def lists_remove_empty_pairs(list1, list2):
    """(list|tuple, list|tuple) -> list, list, list
       Zip through datasets (pairwise),
       make sure both are non-empty; erase if empty.

       Returns:
        list1: non-empty corresponding pairs in list1
        list2: non-empty corresponding pairs in list2
        list3: list of original indices prior to erasing of empty pairs
    """
    xs, ys, posns = [], [], []
    for i in range(len(list1)):
        if list1[i] and list2[i]:
            xs.append(list1[i])
            ys.append(list2[i])
            posns.append(i)
    return xs, ys, posns


def depth(iter_):
    """(List|Tuple) -> int
    Depth of a list or tuple.

    Returns 0 of l is and empty list or
    tuple.
    """
    if isinstance(iter_, (list, tuple)):
        if iter_:
            d = lambda L: isinstance(L, (list, tuple)) and max(map(d, L)) + 1
        else:
            return 0
    else:
        s = 'Depth takes a list or a tuple but got a %s' % (type(iter_))
        raise ValueError(s)
    return d(iter_)


list_depth = depth  # convieniance


# also in stringslib
def list_member_in_str(s: str, match: (str, tuple, list), ignore_case: bool = False) -> bool:
    """
    Check if any member of an iterable is IN s

    Args:
        s (str): string to check list items against
        match (list, str, tuple): items to check for being IN s
        ignore_case (bool): make check case insensitive

    Returns:
        bool: True if match in [ [],(),None,'',0 ] or if any item in member is IN s else False

    Notes:
        Also see list_member_in_str2, which returns what the match was made on
    """
    s = str(s)  # let it work with floats & ints
    if not match: return True  # everything is a match if we have nothing to match to
    if not isinstance(match, (list, tuple, set, map)):
        return str(match) in s
    if ignore_case: s = s.lower()
    for m in match:
        m = str(m)
        if ignore_case:
            m = m.lower()
        if m in s: return True
    return False


# also in stringslib
def list_member_in_str2(s: str, match: (str, tuple, list), ignore_case: bool = False) -> tuple[bool, (str, None)]:
    """
    Check if any member of an iterable is IN s.
    BUT, returns what the match was made on. Unlike list_member_in_str.

    Args:
        s (str): string to check list items against
        match (list, str, tuple): items to check for being IN s
        ignore_case (bool): make check case insensitive

    Returns:
        tuple[bool, (str, None)]: True if match in [ [],(),None,'',0 ] or if any item in member is IN s else False; the second tuple element is the match string on which the match was made.


    Examples:
        Matching string
        >>> list_member_in_str2('my_1234_xyz', ('xyz',))
        (True, 'xyz')

        No match
        >>> list_member_in_str2('my_1234_xyz', ('abc',))
        (False, None)
    """
    s = str(s)  # let it work with floats & ints
    if not match: return True, None  # everything is a match if we have nothing to match to
    if not isinstance(match, (list, tuple, set, map)):
        if str(match) in s:
            return True, match
        else:
            return False, None

    if ignore_case: s = s.lower()
    for m in match:
        m = str(m)
        if ignore_case:
            m = m.lower()
        if m in s: return True, m
    return False, None


def list_random_pick(lst: list, n: int) -> list:
    """pick n random elements from list lst

    Args:
        lst: list
        n: number of elements to pick

    Returns:
        list:
            The list with n random elements

    Notes:
        If n > len(list), the full list is returned
        If lst evaluates to None, an empty list is returned

    Examples:

        Pick 3 elements randomly from a list

        >>> list_random_pick([1, 2, 3, 4, 5], 3)
        [2, 4, 5]

        List too small for "n" elements

        >>> list_random_pick([1, 2, 3, 4, 5], 6)
        [1, 2, 3, 4, 5]

        lst evaluates to False (e.g. None)

        >>> list_random_pick(None, 6)  # noqa
        []
    """
    if not lst: return []
    if len(lst) <= n: return list(lst)
    return _random.sample(lst, n)


# also in stringslib
def list_str_in_iter(s: str, iter_: (list, tuple), ignore_case: bool = True) -> bool:
    """
    Check if s occurs in any member of iter

    Args:
        s (str): The string to check against iter
        iter_ (list, tuple): The iterable to test if s occurs in any member
        ignore_case (bool): Ignore case

    Returns:
        bool: True if occurs else False OR if iter_ is empty or None
    """

    def _filt(t: str):
        if ignore_case:
            return s.lower() in t.lower()
        else:
            return s in t

    if not iter_: return True
    lst = list(filter(_filt, iter_))
    return any(lst)


def list_from_str(s: str) -> list:
    """
    Concert a string representation of a list
    to a list

    Examples:
        >>> list_from_str('[1,2,3]')
        [1,2,3]
    """
    return _ast.literal_eval(s)


def list_not(lst: list, not_in_list: list) -> (list, None):
    """
    Return list of elements which are in lst, but not in "not_in_list"

    Notes:
        Removes duplicates

    Returns:
        list: A list or none if lst and not_in_list are empty
        None: if lst and not_in_list are both None

    Examples:

        >>> list_not([1,2,3,4,5,6], [5,6,7,8])
        [1,2,3,4]

        >>> list_not([1,2], [])
        [1,2]

        >>> list_not(None, None)  # noqa
        None
    """
    if lst is None and not_in_list is None:
        return None  # noqa

    if not lst and not not_in_list:
        return []  # noqa

    if not not_in_list:
        return list(set(lst))  # noqa

    if not lst:
        return []  # noqa

    return list(set(lst) - set(not_in_list))  # noqa


def list_sym_diff(a: list, b: list, rename_keys: (None, list, tuple) = None) -> dict:
    """
    Get a dictionary of the symetrical difference between two lists.

    Args:
        a (list): list of items
        b (list): list of items
        rename_keys (list, tuple, None): Rename the keys to these values. Matches by index.

    Returns:
        dict: Dictionary, {'a_notin_b':[..], 'a_and_b':[...], 'b_notin_a':[...]}

    Examples:
        >>> list_sym_diff([1,2,3,4,10], [2,10,11,12])
        {'a_notin_b':[1, 3, 4], 'a_and_b':[2, 10], 'b_notin_a':[10, 11]}
        \n\nSame, but rename the keys
        >>> list_sym_diff([1,2,3,4,10], [2,10,11,12], rename_keys=['A!B', 'A&B', 'B!A'])
        {'A!B':[1, 3, 4], 'A&B':[2, 10], 'B!A':[10, 11]}
    """
    d = {'a_notin_b': list_not(a, b), 'a_and_b': list_and(a, b), 'b_notin_a': list_not(b, a)}
    if rename_keys:
        d[rename_keys[0]] = d.pop('a_notin_b')  # noqa
        if len(rename_keys) > 1:
            d[rename_keys[1]] = d.pop('a_and_b')
        if len(rename_keys) > 2:
            d[rename_keys[2]] = d.pop('b_notin_a')

    return d


def list_and(lst1: (list, None), lst2: (list, None), strict: bool = True) -> list:
    """
    Return list elements in both lists. Removes duplicates

    Args:
        lst1 (list, None): List or None
        lst2 (list, None): second list
        strict (bool): Do a strict and test. If *not* strict then empty lists or None are ignored for the test, and the none empty list is returned

    Returns:
         list: A list of the intersection of two lists. See the strict arg.

    Examples:
        >>> list_and([1,2,3], [3])
        [3]

        Strict
        >>> list_and([1,2,3], [])
        []

        Not strict
        >>> list_and([1,2,3], [], strict=False)
        [1, 2, 3]

        Empty, None
        >>> list_and([], None, strict=False)
        []
    """
    # TODO: test/debug list_and
    if not lst1 and not lst2: return []

    if strict or (lst1 and lst2):
        return list(set(lst1).intersection(set(lst2)))

    if not lst1:
        return list(set(lst2))

    if not lst2:
        return list(set(lst1))



def list_or(lst1, lst2):
    """(list,list)->list
    return all list elements (union)

    **Removes duplicates"""
    return set(lst1) | set(lst2)


def list_subset(lst1_is_subsetof: list, lst2: list) -> bool:
    """
    Check if lst1 is a subset of list2

    Args:
        lst1_is_subsetof (list): the subset list to check
        lst2 (list): the superset list to check

    Returns: bool
    """
    return set(lst1_is_subsetof).issubset(set(lst2))


def list_superset(lst1_is_supersetof: list, lst2: list) -> bool:
    """
    Check if lst1 is a superset of list2

    lst1_is_supersetof (list):
    Args:
        lst1_is_supersetof (list): the superset list to check
        lst2: the subset list to check

    Returns: bool
    """
    return set(lst1_is_supersetof).issuperset(set(lst2))


def list_symmetric_diff(lst1: list, lst2: list) -> set:
    """
    Return set of elements not _common to both sets.

    i.e. The NOT of a union.

    Args:
        lst1 (list): list of items
        lst2 (list): list of items

    Returns:
        set: Unique elements not _common to both sets

    Notes:
        See list_sym_diff, which returns a more comprehensive result
        as a dict.

    Examples:
        >>> list_symmetric_diff([1], [2])
        {1, 2}
        >>> list_symmetric_diff([1], [1])
        {}
    """
    return set(lst1) ^ set(lst2)


def list_max_ind(lst):
    """(list) -> index
    Get list items with max
    value from a list
    """
    return lst.index(max(lst))


def list_min_ind(lst):
    """(list) -> index
    Get list items with max
    value from a list
    """
    return lst.index(min(lst))


def list_append_unique(list_in, val):
    """(list, type)->void
    Appends val to list_in if it isnt already in the list
    List is by ref
    """
    if val not in list_in:
        list_in.append(val)


def list_get_unique(list_in: list) -> list:
    """
    Returns a new list with duplicates removed and
    maintains order.

    Returns:
        list: list of unique values (i.e. no duplicates)

    Notes:
        Retains the list order, unlike using list(set())

    Examples:
        >>> list_get_unique([1,2,2,3,4])
        [1,2,3,4]
        >>> list_get_unique([None])
        []
    """
    if list_in is None: return list()  # noqa
    out_ = []
    for x_ in list_in:
        list_append_unique(out_, x_)
    return out_


def list_flatten(items, seqtypes=(list, tuple)):
    """flatten a list

    **beware, this is also by ref**
    """
    citems = _deepcopy(items)
    for i, dummy in enumerate(citems):
        while i < len(citems) and isinstance(citems[i], seqtypes):
            citems[i:i + 1] = citems[i]
    return citems
# endregion



# region tuples
def tuple_add_elementwise(tups):
    """lists->list
    Add tuples elementwise.

    lsts:
        a tuple of tuples with the same nr of elements

    Returns:
        tuple with summed elements

    Example:
    >>>tuple_add_elementwise(((1, 2), (1, 2)))
    (2, 4)
    """
    return tuple(map(sum, zip(*tups)))
# endregion


# region Python Info Stuff
def isPython3():  # noqa
    """->bool
    """
    return _sys.version_info.major == 3


def isPython2():
    """->bool
    """
    return _sys.version_info.major == 2


# also implemented in iolib


def get_platform():
    """-> str
    returns windows, mac, linux or unknown
    """
    s = _sys.platform.lower()
    if s in ("linux", "linux2"):
        return 'linux'
    if s == "darwin":
        return 'mac'
    if s in ("win32", "windows"):
        return 'windows'
    return 'unknown'
# endregion


# region Other
def is_debug() -> bool:
    """ Do we look like we are running in a debugger?

    Returns:
        bool: True if looks like we are in a debugger

    Notes:
        Reported to work on PyCharm, unknown in other RADs.
        Credit to https://stackoverflow.com/a/71170397/5585800

    Examples:
        >>> is_debug()
        True
    """
    gettrace = getattr(_sys, 'gettrace', None)

    if gettrace is None:
        return False
    else:
        v = gettrace()
        if v is None:
            return False
        else:
            return True


def isIterable(i, strIsIter=False, numpyIsIter=False):
    """(any, bool)->bool
    Tests to see if i looks like an iterable.

    To count strings a noniterable, strIsIter should be False
    """
    if isinstance(i, str) and strIsIter is False:
        return False

    if isinstance(i, _np.ndarray) and numpyIsIter is False:
        return False
    out_ = isinstance(i, _collections.Iterable)
    return out_


def item_from_iterable_by_type(iterable, match_type):
    """(iterable,class type)->item|None
    given an iterable and a type, return the item
    which first matches type
    """
    if isIterable(iterable):
        for i in iterable:
            if isinstance(iterable, match_type):
                return i
            return None
    return iterable if isinstance(iterable, match_type) else None


def isempty(x_):
    """(something)->bool
    Check of a variable looks empty
    """
    try:
        if isinstance(x_, _np.ndarray):
            return x_.size == 0
        if x_ is None: return True
        if x_ == '': return True
        if not x_: return True
    except Exception:
        assert False  # how did we get here?

    return False


# endreion


def pickle(obj, fname):
    """(Any, str)->void
    Save object to fname

    Also see unpickle
    """
    from iolib import get_file_parts2, create_folder  # import here to avoid circular imports
    d, _, _ = get_file_parts2(fname)
    create_folder(d)
    with open(fname, 'wb') as f:
        _pickle.dump(obj, f)


def unpickle(fname):
    """(str)->obj

    fname: path to pickled object
    unpickle"""
    with open(fname, 'rb') as f:
        obj = _pickle.load(f)
    return obj

def is_date(s) -> bool:
    """Test if s looks like a date
    """
    if s:
        try:
            _dateutil.parser.parse(s)  # noqa
            return True
        except:
            return False
    return False

def is_int(s):
    """is int. A float is not an int for this func"""
    try:
        n = int(s)
        f = float(s)
        return n == f
    except:
        return False


def is_float(s):
    """ is float"""
    try:
        _ = float(s)
        return True
    except:
        return False


def var_get_name(var):
    """(Any)->str
    Get name of var as string

    Parameters
    var: Any variable
    Example:
    >>> var_get_name(var)
    'var'
    """
    #  see https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string
    callers_local_vars = _inspect.currentframe().f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]


# region exceptions
def exception_to_str(e: Exception) -> (str, None):
    """
    Get an exception as a string, as printed to the console

    Args:
        e (Exception): an exception instance

    Returns:
        str: Exception as printed to console
        None: If e was not a Exception instance
    """
    if isinstance(e, Exception):
        return '\n'.join(_traceback.format_exception(type(e), value=e, tb=e.__traceback__))
# endregion exceptions


if __name__ == "__main__":
    out__ = list_get_dups([1, 1, 2, 3, 4, 4, 4], 3)
    x = 1
