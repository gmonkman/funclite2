"""main init for funclite"""
from funclite2 import *


def totextfile(s, fname):
    """dum s, to a file.
    where s can be a string, list, dict etc
    """
    with open(fname, "w", encoding='utf-8') as text_file:
        text_file.write(s)
