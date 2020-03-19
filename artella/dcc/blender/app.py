#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Blender DCC application implementation
"""

from __future__ import print_function, division, absolute_import

from bpy import app


def version():
    """
    Returns version of the current DCC application

    :return: Returns list of integers indicating the version of the DCC application
    :rtype: tuple(int)
    """

    return app.version
