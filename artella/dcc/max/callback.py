#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains 3ds Max DCC callback implementation
"""

from __future__ import print_function, division, absolute_import

from artella import register
from artella.dcc.abstract import callback

import MaxPlus


class Callbacks(object):
    """
    Class that contains all supported callback definitions supported by Maya
    """

    class BeforeOpenCheckCallback(callback.AbstractCallback, object):
        """
        Callback that is called before a file is opened
        """

        @classmethod
        def filter(cls, *args):
            code = args[0]
            return code == MaxPlus.NotificationCodes.FilePreOpen, None, None

        @classmethod
        def register(cls, fn):
            return MaxPlus.NotificationManager.Register(MaxPlus.NotificationCodes.FilePreOpen, fn)

        @classmethod
        def unregister(cls, token):
            if token:
                return MaxPlus.NotificationManager.Unregister(token)

    class AfterOpenCallback(callback.AbstractCallback, object):
        """
        Callback that is called before opening a DCC scene
        """

        @classmethod
        def filter(cls, *args):
            code = args[0]
            return code == MaxPlus.NotificationCodes.FilePostOpen, None, None

        @classmethod
        def register(cls, fn):
            return MaxPlus.NotificationManager.Register(MaxPlus.NotificationCodes.FilePostOpen, fn)

        @classmethod
        def unregister(cls, token):
            if token:
                return MaxPlus.NotificationManager.Unregister(token)

    class SceneBeforeSaveCallback(callback.AbstractCallback, object):
        """
        Callback that is called before a DCC scene is saved
        """

        @classmethod
        def filter(cls, *args):
            code = args[0]
            return code == MaxPlus.NotificationCodes.FilePreSave, None, None

        @classmethod
        def register(cls, fn):
            return MaxPlus.NotificationManager.Register(MaxPlus.NotificationCodes.FilePreSave, fn)

        @classmethod
        def unregister(cls, token):
            if token:
                return MaxPlus.NotificationManager.Unregister(token)

    class SceneCreatedCallback(callback.AbstractCallback, object):
        """
        Callback that is called when a new DCC scene is created
        """

        @classmethod
        def filter(cls, *args):
            code = args[0]
            return code == MaxPlus.NotificationCodes.SystemPostNew, None, None

        @classmethod
        def register(cls, fn):
            return MaxPlus.NotificationManager.Register(MaxPlus.NotificationCodes.SystemPostNew, fn)

        @classmethod
        def unregister(cls, token):
            if token:
                return MaxPlus.NotificationManager.Unregister(token)

    class ShutdownCallback(callback.AbstractCallback, object):
        """
        Callback that is called before DCC app is closed
        """

        @classmethod
        def filter(cls, *args):
            code = args[0]
            return code == MaxPlus.NotificationCodes.SystemShutdown, None

        @classmethod
        def register(cls, fn):
            return MaxPlus.NotificationManager.Register(MaxPlus.NotificationCodes.SystemShutdown, fn)

        @classmethod
        def unregister(cls, token):
            if token:
                return MaxPlus.NotificationManager.Unregister(token)


register.register_class('Callbacks', Callbacks)
