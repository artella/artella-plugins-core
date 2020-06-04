#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains 3ds Max DCC application implementation
"""

from __future__ import print_function, division, absolute_import

import MaxPlus

from . import utils


def name():
    """
    Returns name of current DCC

    :return: Returns name of DCC without any info about version
    :rtype: str
    """

    return 'max'


def version():
    """
    Returns version of DCC application

    :return: Returns integer number indicating the version of the DCC application
    :rtype: int
    """

    return int(utils.get_max_version(as_year=True))


def extensions():
    """
    Returns a list of available extension for DCC application

    :return: List of available extensions with the following format: .{EXTENSION}
    :rtype: list(str)
    """

    return ['.max']


def scene_name():
    """
    Returns the name of the current scene

    :return: Full file path name of the current scene. If no file is opened, None is returned.
    :rtype: str or None
    """

    return MaxPlus.FileManager.GetFileNameAndPath()


def new_scene(force=True):
    """
    Creates a new scene inside DCC
    :param force: True to skip saving of the current opened DCC scene; False otherwise.
    :return: True if the new scene is created successfully; False otherwise.
    :rtype: bool
    """

    if not force:
        save_scene(force=force)
        ACTION_TABLE_ID = 0
        NEW_ACTION_ID = "16"
        MaxPlus.Core.EvalMAXScript('actionMan.executeAction ' + str(ACTION_TABLE_ID) + ' "' + str(NEW_ACTION_ID) + '"')

    MaxPlus.FileManager.Reset(noPrompt=force)


def scene_is_modified():
    """
    Returns whether or not current opened DCC file has been modified by the user or not

    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    return MaxPlus.FileManager.IsSaveRequired()


def open_scene(file_path, save=True):
    """
    Opens DCC scene file
    :param str file_path: Absolute local file path we want to open in current DCC
    :param bool save: Whether or not save current opened DCC scene file
    :return: True if the save operation was successful; False otherwise
    :rtype: bool
    """

    pass


def save_scene(force=True, **kwargs):
    """
    Saves DCC scene file

    :param bool force: Whether to force the saving operation or not
    :return:
    """

    if force:
        return MaxPlus.FileManager.Save()
    else:
        file_check_state = MaxPlus.FileManager.IsSaveRequired()
        if file_check_state:
            res = MaxPlus.Core.EvalMAXScript(
                'queryBox "Do you want to save your changes?" title: "3ds Max has been modified"').Get()
            if res:
                return MaxPlus.FileManager.Save()

    return False


def supports_uri_scheme():
    """
    Returns whether or not current DCC support URI scheme implementation

    :return: True if current DCC supports URI scheme implementation; False otherwise
    """

    return False


def pass_message_to_main_thread_fn():
    """
    Returns function used by DCC to execute a function in DCC main thread in the next idle event of that thread.

    :return If DCC API supports it, returns function to call a function in main thread from other thread
    """

    return None


def clean_path(file_path):
    """
    Cleans given path so it can be properly used by current DCC

    :param str file_path: file path we want to clean
    :return: Cleaned version of the given file path
    :rtype: str
    """

    from artella.core import utils

    return utils.clean_path(file_path)
