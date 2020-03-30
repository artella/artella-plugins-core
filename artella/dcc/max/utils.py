#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains 3ds Max DCC utils functions
"""

from __future__ import print_function, division, absolute_import

import math

import MaxPlus

from artella.core import utils

if utils.is_python3():
    long = int


def get_max_version(as_year=True):
    """
    Returns the current version of 3ds Max

    :param  bool as_year: Whether to return version as a year or not
    :return: Current version of your 3ds Max
    :rtype: long or float

    >>> print(get_max_version())
    2018.0

    >>> print(get_max_version(False))
    20000L
    """

    # 3dsMax Version returns a number which contains max version, sdk version, etc...
    version_id = MaxPlus.Application_Get3DSMAXVersion()

    # Transform it to a version id
    # (Macro to get 3ds max release from version id)
    # NOTE: 17000 = 2015, 17900 = 2016, etc
    version_number = (version_id >> 16) & 0xffff

    if as_year:
        year = 2000 + (math.ceil(version_number / 1000.0) - 2)
        return year

    return version_number


def get_max_window():
    """
    Returns an instance of the current Max window
    """

    # 17000 = Max 2015
    # 18000 = Max 2016
    # 19000 = Max 2017
    # 20000 = Max

    version = int(get_max_version(as_year=True))

    if version == 2014:
        import ctypes
        import ctypes.wintypes
        pyobject = MaxPlus.Win32.GetMAXHWnd()                       # Swig Object Containing HWND *
        hwndptr = pyobject.__int__()                                # Getting actual HWND* mem address
        ptr = ctypes.c_void_p(hwndptr)                              # Casting to HWD* of Void*
        ptrvalue = ptr.value                                        # Getting actual Void* mem address (should be same as hwndptr)
        clonglong = ctypes.c_longlong.from_address(ptrvalue)        # Getting derefeerence Void* and get HWND as c_longlong
        longhwnd = clonglong.value                                  # Getting actual HWND value from c_longlong
        chwnd = ctypes.wintypes.HWND.from_address(ptrvalue)         # Getting derefeerence Void* and get HWND as c_longlong
        hwnd = clonglong.value                                      # Getting actual HWND value from c_longlong
        return hwnd
    elif version == 2015 or version == 2016:
            return long(MaxPlus.Win32.GetMAXHWnd())
    elif version == 2017:
        return MaxPlus.GetQMaxWindow()
    else:
        return MaxPlus.GetQMaxMainWindow()
