#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC application implementation
"""

from __future__ import print_function, division, absolute_import

import maya.cmds as cmds


def version():
    """
    Returns version of the current DCC application

    :return: Returns integer number indicating the version of the DCC application
    :rtype: int
    """

    return (int(cmds.about(version=True)),)
