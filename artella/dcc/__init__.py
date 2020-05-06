#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for artella-dcc
"""

from __future__ import print_function, division, absolute_import


from artella.dcc.abstract.app import *
from artella.dcc.abstract.ui import *
from artella.dcc.abstract.menu import *
from artella.dcc.abstract.callback import *
from artella.dcc.abstract.parser import *


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


class DccCallbacks(object):
    """
    Class that contains all callbacks that can be supported by DCCs
    """

    BeforeOpenCheck = ('BeforeOpenCheck', {'type': 'simple'})
    AfterOpen = ('AfterOpen', {'type': 'simple'})
    SceneBeforeSave = ('SceneBeforeSave', {'type': 'simple'})
    SceneCreated = ('SceneCreated', {'type': 'simple'})
    AfterLoadReference = ('AfterLoadReference', {'type': 'simple'})
    BeforeCreateReferenceCheck = ('BeforeCreateReferenceCheck', {'type': 'simple'})