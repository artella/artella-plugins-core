#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Blender DCC application implementation
"""

from __future__ import print_function, division, absolute_import

import bpy


def name():
    """
    Returns name of current DCC

    :return: Returns name of DCC without any info about version
    :rtype: str
    """

    return 'blender'


def version():
    """
    Returns version of the current DCC application

    :return: Returns list of integers indicating the version of the DCC application
    :rtype: tuple(int)
    """

    return bpy.app.version


def extensions():
    """
    Returns a list of available extension for DCC application

    :return: List of available extensions with the following format: .{EXTENSION}
    :rtype: list(str)
    """

    return ['.blend']


def scene_name():
    """
    Returns the name of the current scene

    :return: Full file path name of the current scene. If no file is opened, None is returned.
    :rtype: str or None
    """

    return bpy.data.filepath


def scene_is_modified():
    """
    Returns whether or not current opened DCC file has been modified by the user or not

    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    return bpy.data.isdirty


def save_scene(force=True, **kwargs):
    """
    Saves DCC scene file

    :param bool force: Whether to force the saving operation or not
    :return:
    """

    bpy.ops.wm.save_as_mainfile()

    return True


def supports_uri_scheme():
    """
    Returns whether or not current DCC support URI scheme implementation

    :return: True if current DCC supports URI scheme implementation; False otherwise
    """

    return False
