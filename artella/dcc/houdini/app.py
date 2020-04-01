#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Houdini DCC application implementation
"""

from __future__ import print_function, division, absolute_import

import hou
import hdefereval

from . import utils


def name():
    """
    Returns name of current DCC

    :return: Returns name of DCC without any info about version
    :rtype: str
    """

    return 'houdini'


def version():
    """
    Returns version of DCC application

    :return: Returns integer number indicating the version of the DCC application
    :rtype: int
    """

    return utils.get_houdini_version(as_string=False)


def extensions():
    """
    Returns a list of available extension for DCC application

    :return: List of available extensions with the following format: .{EXTENSION}
    :rtype: list(str)
    """

    return ['.hip', '.hiplc', '.hipnc', '.hip*']


def scene_name():
    """
    Returns the name of the current scene

    :return: Full file path name of the current scene. If no file is opened, None is returned.
    :rtype: str or None
    """

    return hou.hipFile.path()


def scene_is_modified():
    """
    Returns whether or not current opened DCC file has been modified by the user or not

    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    return hou.hipFile.hasUnsavedChanges()


def save_scene(force=True, **kwargs):
    """
    Saves DCC scene file

    :param bool force: Whether to force the saving operation or not
    :return:
    """

    hou.hipFile.save()

    return True


def supports_uri_scheme():
    """
    Returns whether or not current DCC support URI scheme implementation

    :return: True if current DCC supports URI scheme implementation; False otherwise
    """

    return False


def pass_message_to_main_thread(fn, data):
    """
    Executes given callable object in the DCC thread in the next idle event of that thread.
    :param fn: callable object to execute
    :param data: arguments to pass to the callable object
    """

    hdefereval.executeInMainThreadWithResult(fn, data)
