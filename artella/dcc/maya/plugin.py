#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC plugin specific implementation
"""

from __future__ import print_function, division, absolute_import

import os

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya

import artella
from artella import dcc
from artella import logger
from artella import register
from artella.core import consts, callback, dccplugin
from artella.core.utils import Singleton
from artella.dcc.maya import utils as maya_utils


class ArtellaMayaPlugin(dccplugin.ArtellaDccPlugin, object):

    # ==============================================================================================================
    # OVERRIDES
    # ==============================================================================================================

    def init(self):
        """
        Initializes Artella DCC plugin
        :return: True if the initialization was successful; False otherwise
        :rtype: bool
        """

        # Force Maya MEL stack trace on before we start using the plugin
        maya_utils.force_mel_stack_trace_on()

        super(ArtellaMayaPlugin, self).init()

        # Register Maya specific callbacks
        callback.register(artella.Callbacks.AfterOpenCallback, self._after_open)
        callback.register(artella.Callbacks.SceneBeforeSaveCallback, self._before_save)
        callback.register(artella.Callbacks.BeforeOpenCheckCallback, self._before_open_check)
        callback.register(artella.Callbacks.AfterLoadReferenceCallback, self._after_load_reference)
        callback.register(artella.Callbacks.BeforeCreateReferenceCheckCallback, self._before_reference_check)

    def _post_update_paths(self, **kwargs):
        """
        Internal function that is called after update paths functionality is over.
        """

        maya_utils.reload_textures()
        maya_utils.reload_dependencies()

    # ==============================================================================================================
    # FUNCTIONS
    # ==============================================================================================================

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
        logger.log_info('Set Maya Workspace Path: {}'.format(artella_local_root_path))

    def validate_environment_for_callback(self, callback_name):
        """
        Checks that all necessary parts are available before executing a Maya callback

        :param str callback_name: name of the callback to validate
        """

        logger.log_info('validate_environment_for_callback for {}'.format(callback_name))
        client = self.get_client()
        local_root = cmds.encodeString(client.get_local_root())
        if local_root:
            # We use this to make sure that Artella environment variable is set
            logger.log_debug('set local root in local environment: {}'.format(local_root))
            os.environ[consts.ALR] = local_root
            os.putenv(consts.ALR, local_root)
            mel.eval('putenv "{}" "{}"'.format(consts.ALR, local_root))

        if consts.ALR not in os.environ:
            msg = 'Unable to execute Maya "{}" callback, {} is not set in the environment'.format(
                callback_name, consts.ALR)
            logger.log_error(msg)
            raise Exception(msg)

    # ==============================================================================================================
    # INTERNAL
    # ==============================================================================================================

    def _show_get_deps_dialog(self, deps):
        """
        Internal function that shows a dialog that allows the user to select if the want to update missing dependencies
        or not.
        # TODO: (tpoveda): Once Qt framework is ready, this function will be generic and added to core plugin
        :param deps: List of dependencies files that are missing
        :return: True if the user acceps the operation; False otherwise
        """

        if len(deps) > 10:
            deps = deps[:10]
            deps.append('...')

        title = 'Artella - Missing dependency' if len(deps) <= 1 else 'Artella - Missing dependencies'
        msg = ('One or more dependent files are missing.\nWould you like to download all missing files?\n\n {}'.format(
            "\n  ".join(deps)))
        result = cmds.confirmDialog(
            title=title, message=msg, button=['Yes', 'No'], cancelButton='No', dismissString='No')

        return result == 'Yes'

    # ==============================================================================================================
    # CALLBACKS
    # ==============================================================================================================

    def _after_open(self, *args):
        """
        Internal callback function that is called once a Maya scene is opened

        :param args:
        """

        self.validate_environment_for_callback('AfterOpen')

    def _before_save(self, *args):
        """
        Internal callback function that is called before saving a Maya scene

        :param args:
        """

        self.validate_environment_for_callback('BeforeSave')

        valid_lock = self.lock_file(force=True, show_dialogs=False)
        if not valid_lock:
            logger.log_error('Unable to checkout file. Changes cannot be saved.')
            return

        self.update_paths(show_dialogs=False, skip_save=True)

    def _before_open_check(self, retcode, maya_file, client_data=None):
        """
        Internal callback function that is called before a Maya scene is opened

        :param bool retcode: Flag that indicates if the file can opened or not
        :param MFileObject maya_file: Maya API object that contains info about the file we want to open
        :param dict client_data:
        """

        self.validate_environment_for_callback('BeforeOpenCheck')

        file_path = maya_file.resolvedFullName()
        logger.log_info('Opening file: "{}"'.format(file_path))

        logger.log_info('Checking missing dependencies ...')

        get_deps_plugin = artella.PluginsMgr().get_plugin_by_id('artella-plugins-getdependencies')
        if not get_deps_plugin or not get_deps_plugin.is_loaded():
            msg = 'Get Dependencies plugin is not loaded. Get dependencies functionality is not available!'
            dcc.show_warning('Get Dependencies Plugin not available', msg)
            logger.log_warning(msg)

        non_available_deps = get_deps_plugin.get_non_available_dependencies(file_path)
        if non_available_deps:
            logger.log_info('{} Missing dependencies found.'.format(len(non_available_deps)))
            get_deps = self._show_get_deps_dialog(deps=non_available_deps)
            if get_deps:
                get_deps_plugin.get_dependencies(file_path, recursive=True, update_paths=False)

        OpenMaya.MScriptUtil.setBool(retcode, True)

    def _after_load_reference(self, *args):
        """
        Internal callback function that is called after a Maya reference is loaded

        :param args:
        """

        self.validate_environment_for_callback('AfterLoadReference')

    def _before_reference_check(self, retcode, maya_file, client_data=None):
        """
        Internal callback function that is called before a Maya reference is opened

        :param bool retcode: Flag that indicates if the file can opened or not
        :param MFileObject maya_file: Maya API object that contains info about the file we want to open
        :param dict client_data:
        """

        self.validate_environment_for_callback('BeforeReferenceCheck')

        OpenMaya.MScriptUtil.setBool(retcode, True)


@Singleton
class ArtellaMayaPluginSingleton(ArtellaMayaPlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaMayaPlugin.__init__(self, artella_drive_client=artella_drive_client)


register.register_class('DccPlugin', ArtellaMayaPluginSingleton)
