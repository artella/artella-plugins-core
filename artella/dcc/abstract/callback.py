#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract callback implementation
"""

import artella
from artella import reroute
from artella.core.utils import abstract


class AbstractCallback(object):
    """
    Class that defines basic callback interface functions
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


class Callbacks(object):
    """
    Class that contains all supported callback definitions
    """

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


artella.register_class('Callbacks', Callbacks)