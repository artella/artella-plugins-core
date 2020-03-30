#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC application implementation
"""

from __future__ import print_function, division, absolute_import

import os

import maya.cmds as cmds
import maya.utils as utils


def name():
    """
    Returns name of current DCC

    :return: Returns name of DCC without any info about version
    :rtype: str
    """

    return 'maya'


def version():
    """
    Returns version of DCC application

    :return: Returns integer number indicating the version of the DCC application
    :rtype: int
    """

    return (int(cmds.about(version=True)),)


def extensions():
    """
    Returns a list of available extension for DCC application

    :return: List of available extensions with the following format: .{EXTENSION}
    :rtype: list(str)
    """

    return ['.ma', '.mb']


def scene_name():
    """
    Returns the name of the current scene

    :return: Full file path name of the current scene. If no file is opened, None is returned.
    :rtype: str or None
    """

    return cmds.file(query=True, sceneName=True)


def scene_is_modified():
    """
    Returns whether or not current opened DCC file has been modified by the user or not

    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    return cmds.file(query=True, modified=True)


def save_scene(force=True, **kwargs):
    """
    Saves DCC scene file

    :param bool force: Whether to force the saving operation or not
    :return:
    """

    file_extension = kwargs.get('extension_to_save', extensions()[0])
    current_scene_name = scene_name()
    if current_scene_name:
        file_extension = os.path.splitext(current_scene_name)[-1]
    if not file_extension.startswith('.'):
        file_extension = '.{}'.format(file_extension)
    maya_scene_type = 'mayaAscii' if file_extension == '.ma' else 'mayaBinary'

    if force:
        cmds.SaveScene()
        return True
    else:
        if scene_is_modified():
            cmds.SaveScene()
            return True
        else:
            cmds.file(save=True, type=maya_scene_type)
            return True


def supports_uri_scheme():
    """
    Returns whether or not current DCC support URI scheme implementation

    :return: True if current DCC supports URI scheme implementation; False otherwise
    """

    return True


def pass_message_to_main_thread(fn, data):
    """
    Executes given callable object in the DCC thread in the next idle event of that thread.
    :param fn: callable object to execute
    :param data: arguments to pass to the callable object
    """

    utils.executeInMainThreadWithResult(fn, data)
