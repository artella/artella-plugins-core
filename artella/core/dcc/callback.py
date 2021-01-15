#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract callback implementation
"""

from artella import dcc
from artella.core.dcc import reroute
from artella.core.utils import abstract, add_metaclass


class _MetaCallbacks(type):

    def __call__(cls, *args, **kwargs):
        if dcc.is_maya():
            from artella.dccs.maya import callback as maya_callback
            return maya_callback.Callbacks
        else:
            return AbstractCallback


class AbstractCallback(object):
    """
    Class that defines basic callback abstract functions
    """

    @classmethod
    @abstract
    @reroute
    def filter(cls, *args):
        """
        Used to process function callback arguments during the execution of a callback
        :param args: List of arguments pass from the callback function to be evaluated
        :return: Return tuple of flags
        :rtype: tuple(bool, bool)
        """

        pass

    @classmethod
    @abstract
    @reroute
    def register(cls, fn):
        """
        Registers given Python function as callback

        :param fn: function, Python function to register
        :return: token that can be used later to unregister the callback function
        :rtype: str
        """

        pass

    @classmethod
    @abstract
    @reroute
    def unregister(cls, token):
        """
        Unregisters Python function callback linked to given token
        :param token: Token provided by register function to unregister a specific callback function
        """

        pass


class AbstractCallbacks(object):
    """
    Class that contains all supported callback definitions
    """

    class ShutdownCallback(AbstractCallback, object):
        """
        Callback that is called before DCC app is closed
        """

        pass

    class BeforeOpenCheckCallback(AbstractCallback, object):
        """
        Callback that is called before a file is opened
        """

        pass

    class AfterOpenCallback(AbstractCallback, object):
        """
        Callback that is called before opening a DCC scene
        """

        pass

    class SceneBeforeSaveCallback(AbstractCallback, object):
        """
        Callback that is called before a DCC scene is saved
        """

        pass

    class SceneCreatedCallback(AbstractCallback, object):
        """
        Callback that is called when a new DCC scene is created
        """

        pass

    class AfterLoadReferenceCallback(AbstractCallback, object):
        """
        Callback that is called after a reference file is loaded
        """

        pass

    class BeforeCreateReferenceCheckCallback(AbstractCallback, object):
        """
        Callback that is called before a new reference is created
        """

        pass


@add_metaclass(_MetaCallbacks)
class Callbacks(AbstractCallbacks):
    pass
