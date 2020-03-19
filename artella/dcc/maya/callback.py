#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC callback implementation
"""

from __future__ import print_function, division, absolute_import

import artella
from artella.dcc.abstract import callback

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya


class Callbacks(object):
    """
    Class that contains all supported callback definitions supported by Maya
    """

    class SceneCreatedCallback(callback.AbstractCallback, object):
        """
        Callback that is emitted when a new DCC scene is created
        """

        _codes = [OpenMaya.MSceneMessage.kBeforeNew, OpenMaya.MSceneMessage.kBeforeOpen]

        @classmethod
        def filter(cls, *args):
            return True, args

        @classmethod
        def register(cls, fn):
            return [OpenMaya.MSceneMessage.addCallback(c, fn) for c in cls._codes]

        @classmethod
        def unregister(cls, token):
            for t in token:
                OpenMaya.MSceneMessage.removeCallback(t)


artella.register_class('Callbacks', Callbacks)
