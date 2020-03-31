#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains dcc module initialization
"""

from __future__ import print_function, division, absolute_import

from artella.dcc.abstract.app import *
from artella.dcc.abstract.ui import *
from artella.dcc.abstract.menu import *
from artella.dcc.abstract.callback import *
from artella.dcc.abstract.parser import *


class DccCallbacks(object):
    """
    Class that contains all callbacks that can be supported by DCCs
    """

    BeforeOpenCheck = ('BeforeOpenCheck', {'type': 'simple'})
    AfterOpen = ('AfterOpen', {'type': 'simple'})
    SceneBeforeSave = ('SceneBeforeSave', {'type': 'simple'})
    SceneCreated = ('SceneCreated', {'type': 'simple'})
    AfterLoadReference = ('AfterLoadReference', {'type': 'simple'})
    BeforeCreateReferenceCheck = ('BeforeCreateReferenceCheck', {'type': 'simpple'})


def is_standalone():
    """
    Returns whether or not current application is standalone (no DCC)
    :return: True if current session application is standalone; False otherwise
    :rtype: bool
    """

    return artella.current_dcc() == 'standalone'


def is_maya():
    """
    Returns whether or not current DCC is Maya
    :return: True if current session DCC is Maya; False otherwise
    :rtype: bool
    """

    return artella.current_dcc() == 'maya'


def is_blender():
    """
    Returns whether or not current DCC is Blender
    :return: True if current session DCC is Blender; False otherwise
    :rtype: bool
    """

    return artella.current_dcc() == 'blender'


def is_max():
    """
    Returns whether or not current DCC is 3ds Max
    :return: True if current session DCC is 3ds Max; False otherwise
    :rtype: bool
    """

    return artella.current_dcc() == 'max'


def is_houdini():
    """
    Returns whether or not current DCC is Houdini
    :return: True if current session DCC is Houdini; False otherwise
    :rtype: bool
    """

    return artella.current_dcc() == 'houdini'


def callbacks():
    """
    Returns a list of callbacks based on DCC available callbacks
    :return: List of available DCC callbacks
    :rtype: list
    """

    callbacks_list = list()
    for k, v in DccCallbacks.__dict__.items():
        if k.startswith('__') or k.endswith('__'):
            continue
        callbacks_list.append(v[0])

    return callbacks_list
