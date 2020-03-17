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
def version():
    """
    Returns version of the current DCC application

    :return: Returns integer number indicating the version of the DCC application
    :rtype: int
    """

    pass
