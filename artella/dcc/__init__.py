#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains dcc module initialization
"""

from __future__ import print_function, division, absolute_import

from artella.dcc.abstract.app import *
from artella.dcc.abstract.callback import *
from artella.dcc.abstract.parser import *


class DccCallbacks(object):
    """
    Class that contains all callbacks that can be supported by DCCs
    """

    SceneCreated = ('SceneCreated', {'type': 'simple'})


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
