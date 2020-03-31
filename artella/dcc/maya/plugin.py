#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC plugin specific implementation
"""

from __future__ import print_function, division, absolute_import

import maya.cmds as cmds
import maya.mel as mel

import artella
import artella.plugin as plugin
from artella.core.utils import Singleton

from . import utils as maya_utils


class ArtellaMayaPlugin(plugin.ArtellaPlugin, object):

    def setup_project(self, artella_local_root_path):
        """
        Setup Artella local root as current DCC active project
        This function should be override in specific DCC plugin implementation
        Is not an abstract function because its implementation is not mandatory

        :param str artella_local_root_path: current user Artella local root path
        """

        artella_local_root_path = cmds.encodeString(artella_local_root_path)
        mel.eval('setProject "%s"' % artella_local_root_path.replace('\\', '\\\\'))
        cmds.workspace(directory=artella_local_root_path)
        cmds.workspace(fileRule=['sourceImages', ''])
        cmds.workspace(fileRule=['scene', ''])
        cmds.workspace(fileRule=['mayaAscii', ''])
        cmds.workspace(fileRule=['mayaBinary', ''])
        artella.log_info('Set Maya Workspace Path: {}'.format(artella_local_root_path))

    def init(self):
        """
        Initializes Artella plugin in current DCC
        :return: True if the initialization was successful; False otherwise
        :rtype: bool
        """

        # Force Maya MEL stack trace on before we start using the plugin
        maya_utils.force_mel_stack_trace_on()

        super(ArtellaMayaPlugin, self).init()


@Singleton
class ArtellaMayaPluginSingleton(ArtellaMayaPlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaMayaPlugin.__init__(self, artella_drive_client=artella_drive_client)


artella.register_class('Plugin', ArtellaMayaPluginSingleton)
