#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Blender DCC plugin specific implementation
"""

from __future__ import print_function, division, absolute_import

import bpy

import artella
import artella.plugin as plugin
from artella.core.utils import Singleton


class ArtellaBlenderPlugin(plugin.ArtellaPlugin, object):
    def init(self):
        """
        Initializes Artella plugin in current DCC
        :return: True if the initialization was successful; False otherwise
        :rtype: bool
        """

        import artella.dcc.blender.addon as addon

        addon.register()

        super(ArtellaBlenderPlugin, self).init()

    def get_version_comment(self, current_file):
        comment = bpy.context.scene.SaveToCloudProps.comment

        return comment

    def shutdown(self):
        """

        :return:
        """

        import artella.dcc.blender.addon as addon

        try:
            addon.unregister()
        except Exception as exc:
            pass

        super(ArtellaBlenderPlugin, self).shutdown()


@Singleton
class ArtellaBlenderPluginSingleton(ArtellaBlenderPlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaBlenderPlugin.__init__(self, artella_drive_client=artella_drive_client)


artella.register_class('Plugin', ArtellaBlenderPluginSingleton)
