#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Houdini DCC utils functions
"""

from __future__ import print_function, division, absolute_import

import hou


def get_houdini_version(as_string=True):
    """
    Returns version of the executed Houdini

    :param as_string: bool, Whether to return the string version or integer version
    :return: Current version of Houdini
    :rtype: int or float
    """

    if as_string:
        return hou.applicationVersionString()
    else:
        return hou.applicationVersion()


def get_houdini_window():
    """
    Returns the Houdini Qt main window

    :return: Houdini Qt main window
    :rtype: QMainWindow
    """

    try:
        return hou.qt.mainWindow()
    except Exception:
        return hou.ui.mainQtWindow()
