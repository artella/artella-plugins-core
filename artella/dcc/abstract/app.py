#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract application implementation
"""

from __future__ import print_function, division, absolute_import

from artella import reroute
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
def scene_is_modified():
    """
    Returns whether or not current opened DCC file has been modified by the user or not

    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def save_scene(force=True, **kwargs):
    """
    Saves DCC scene file

    :param bool force: Whether to force the saving operation or not
    :return:
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
def pass_message_to_main_thread(fn, data):
    """
    Executes given callable object in the DCC thread in the next idle event of that thread.
    :param fn: callable object to execute
    :param data: arguments to pass to the callable object
    """

    pass
