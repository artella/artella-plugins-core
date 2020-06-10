#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Standalone plugin specific implementation
"""

from __future__ import print_function, division, absolute_import

from artella import register
from artella.core import dccplugin
from artella.core.utils import Singleton


class ArtellaStandalonePlugin(dccplugin.ArtellaDccPlugin, object):

    def init(self, dev=False):
        super(ArtellaStandalonePlugin, self).init(dev=dev)


@Singleton
class ArtellaStandalonePluginSingleton(ArtellaStandalonePlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaStandalonePlugin.__init__(self, artella_drive_client=artella_drive_client)


register.register_class('DccPlugin', ArtellaStandalonePluginSingleton)
