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


def scene_name():
    """
    Returns the name of the current scene

    :return: Full file path name of the current scene. If no file is opened, None is returned.
    :rtype: str or None
    """

    return cmds.file(query=True, sceneName=True)
