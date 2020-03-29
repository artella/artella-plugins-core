#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC plugin specific implementation
"""

from __future__ import print_function, division, absolute_import

import maya.utils as utils

import artella
import artella.plugin as plugin
from artella.core.utils import Singleton

from . import utils as maya_utils


class ArtellaMayaPlugin(plugin.ArtellaPlugin, object):

    def init(self):
        """
        Initializes Artella plugin in current DCC
        :return: True if the initialization was successful; False otherwise
        :rtype: bool
        """

        # Force Maya MEL stack trace on before we start using the plugin
        maya_utils.force_mel_stack_trace_on()

        super(ArtellaMayaPlugin, self).init()

    def pass_message(self, json_data):
        artella.log_debug('Passing message to Maya: {}'.format(json_data))
        utils.executeInMainThreadWithResult(self.handle_message, json_data)


@Singleton
class ArtellaMayaPluginSingleton(ArtellaMayaPlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaMayaPlugin.__init__(self, artella_drive_client=artella_drive_client)


artella.register_class('Plugin', ArtellaMayaPluginSingleton)
