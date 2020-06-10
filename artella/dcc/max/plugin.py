#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC plugin specific implementation
"""

from __future__ import print_function, division, absolute_import

import artella
from artella import register
from artella.core import dccplugin, callback
from artella.core.utils import Singleton


class ArtellaMaxPlugin(dccplugin.ArtellaDccPlugin, object):
    def __init__(self, artella_drive_client):
        super(ArtellaMaxPlugin, self).__init__(artella_drive_client=artella_drive_client)

    def init(self, dev=False):
        super(ArtellaMaxPlugin, self).init(dev=dev)

        # Register 3ds Max specific callbacks
        callback.register(artella.Callbacks.ShutdownCallback, self._on_close)

    def _on_close(self, *args):
        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return

        artella_drive_client.artella_drive_disconnect()


@Singleton
class ArtellaMaxPluginSingleton(ArtellaMaxPlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaMaxPlugin.__init__(self, artella_drive_client=artella_drive_client)


register.register_class('DccPlugin', ArtellaMaxPluginSingleton)
