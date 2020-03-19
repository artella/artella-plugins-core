#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains dcc module initialization
"""

from __future__ import print_function, division, absolute_import

import artella
from artella.dcc.abstract.app import *


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
