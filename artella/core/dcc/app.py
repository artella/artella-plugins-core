#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract application implementation
"""

from __future__ import print_function, division, absolute_import

from artella.core.dcc import reroute
from artella.core.utils import abstract


@reroute
@abstract
def name():
    """
    Returns name of current DCC

    :return: Returns name of DCC without any info about version
    :rtype: str
    """

    pass


@reroute
@abstract
def nice_name():
    """
    Returns nice name of current DCC

    :return: Returns formatted DCC name
    :rtype: str
    """

    pass


@reroute
@abstract
def version():
    """
    Returns version of DCC application

    :return: Returns integer number indicating the version of the DCC application
    :rtype: int
    """

    pass


@reroute
@abstract
def extensions():
    """
    Returns a list of available extension for DCC application

    :return: List of available extensions with the following format: .{EXTENSION}
    :rtype: list(str)
    """

    pass


@reroute
@abstract
def scene_name():
    """
    Returns the name of the current scene

    :return: Full file path name of the current scene. If no file is opened, None is returned.
    :rtype: str or None
    """

    pass


@reroute
@abstract
def new_scene(force=True):
    """
    Creates a new scene inside DCC
    :param force: True to skip saving of the current opened DCC scene; False otherwise.
    :return: True if the new scene is created successfully; False otherwise.
    :rtype: bool
    """

    pass


@reroute
@abstract
def scene_is_modified():
    """
    Returns whether or not current opened DCC file has been modified by the user or not

    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def open_scene(file_path, save=True):
    """
    Opens DCC scene file
    :param str file_path: Absolute local file path we want to open in current DCC
    :param bool save: Whether or not save current opened DCC scene file
    :return: True if the save operation was successful; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def save_scene(force=True, **kwargs):
    """
    Saves DCC scene file

    :param bool force: Whether to force the saving operation or not
    :return: True if the save operation was successful; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def import_scene(file_path):
    """
    Opens scene file into current opened DCC scene file
    :param str file_path: Absolute local file path we want to import into current DCC
    :return: True if the import operation was successful; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def reference_scene(file_path, **kwargs):
    """
    References scene file into current opened DCC scene file
    :param str file_path: Absolute local file path we want to reference into current DCC
    :return: True if the reference operation was successful; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def supports_uri_scheme():
    """
    Returns whether or not current DCC support URI scheme implementation

    :return: True if current DCC supports URI scheme implementation; False otherwise
    """

    pass


@reroute
@abstract
def pass_message_to_main_thread_fn():
    """
    Returns function used by DCC to execute a function in DCC main thread in the next idle event of that thread.

    :return If DCC API supports it, returns function to call a function in main thread from other thread
    """

    pass


@reroute
@abstract
def is_batch():
    """
    Returns whether or not current DCC is being executed in batch mode (no UI)
    :return: True if current DCC session is being executed in batch mode; False otherwise.
    :rtype: bool
    """

    pass


@reroute
@abstract
def clean_path(file_path):
    """
    Cleans given path so it can be properly used by current DCC

    :param str file_path: file path we want to clean
    :return: Cleaned version of the given file path
    :rtype: str
    """

    pass


@reroute
@abstract
def get_installation_paths(versions=None):
    """
    Returns installation path of the given versions of current DCC

    :param list(int) versions: list of versions to find installation paths of. If not given, current DCC version
        installation path will be returned
    :return: List of installation paths of the given DCC versions
    :rtype: list(str)
    """

    pass


@reroute
@abstract
def is_udim_path(file_path):
    """
    Returns whether or not given file path is an UDIM one

    :param str file_path: File path we want to check
    :return: True if the given paths is an UDIM path; False otherwise.
    :rtype: bool
    """

    pass


@reroute
@abstract
def execute_deferred(fn):
    """
    Executes given function in deferred mode (once DCC UI has been loaded)
    :param callable fn: Function to execute in deferred mode
    :return:
    """

    pass


@reroute
@abstract
def register_dcc_resource_path(resources_path):
    """
    Registers path into given DCC so it can find specific resources
    :param resources_path: str, path we want DCC to register
    """

    pass
