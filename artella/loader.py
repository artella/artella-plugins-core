#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for artella
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import logging

import artella
from artella import logger as logger
import artella.register as register
from artella.core import consts, utils


def init(
        init_client=True, plugin_paths=None, dcc_paths=None, extensions=None, dev=False,
        load_plugins=True, create_menu=True, create_callbacks=True):
    """
    Initializes Artella Plugin

    :param bool init_client: Whether or not Artella Drive Client should be initialized during initialization.
        Useful to avoid to connect to Artella client when developing DCC specific functionality.
    :param list(str) plugin_paths: List of paths where Artella plugins can be located
    :param list(str) dcc_paths: List of paths where Artella DCC implementations can be located
    :param list(str) extensions: List of extensions to register
    :param bool dev: Whether or not initialization should be done in dev mode
    :param bool load_plugins: Whether or not Artella Plugins should be loaded
    :param bool create_menu: Whether or not Artella menu should be created
    :param bool create_callbacks: Whether or not Artella DCC plugin callbacks should be created
    :return: True if Artella initialization was successful; False otherwise.
    :rtype: bool
    """

    plugins_path = plugin_paths if plugin_paths is not None else list()
    dccs_path = dcc_paths if dcc_paths is not None else list()
    extensions = extensions if extensions is not None else list()

    # Create logger
    logger.create_logger()
    artella_logger = logging.getLogger('artella')

    # Register DCC paths
    valid_dcc_paths = list()
    default_dccs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dccs')
    if default_dccs_path not in dccs_path:
        dccs_path.append(default_dccs_path)
    for dcc_path in dccs_path:
        if os.path.isdir(dcc_path):
            if dcc_path not in sys.path:
                sys.path.append(dcc_path)
            valid_dcc_paths.append(dcc_path)
    if valid_dcc_paths:
        if os.environ.get(consts.AED, None):
            env = os.environ[consts.AED].split(';')
            env.extend(valid_dcc_paths)
            clean_env = list(set([utils.clean_path(pth) for pth in env]))
            dcc_paths_str = ';'.join(clean_env)
        else:
            dcc_paths_str = ';'.join(valid_dcc_paths)
    if os.environ.get(consts.AED, ''):
        if dcc_paths_str:
            os.environ[consts.AED] += ';{}'.format(dcc_paths_str)
    else:
        os.environ[consts.AED] = dcc_paths_str

    # Once DCC paths are registered we can import modules
    import artella
    import artella.register as register

    import artella.dcc as dcc

    # Do not remove this imports, they do registration of some of the core Artella classes
    from artella.core import dcc as dcc_core
    from artella.core import client, resource, plugin, dccplugin, qtutils
    from artella.widgets import theme, color

    # Make sure that Artella Drive client and DCC are cached during initialization
    current_dcc = dcc_core.current_dcc()
    if not current_dcc:
        artella_logger.error('Impossible to load Artella Plugin because no DCC is available!')
        return False

    # Specific DCC extensions are managed by the client
    dcc_extensions = dcc.extensions() or list()
    extensions.extend(dcc_extensions)

    # Initialize resources and theme
    resources_mgr = artella.ResourcesMgr()
    resources_mgr.register_resources_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources'))
    if qtutils.QT_AVAILABLE:
        artella_theme = theme.ArtellaTheme(main_color=color.ArtellaColors.DEFAULT)
        register.register_class('theme', artella_theme)

    # Create Artella Drive Client
    artella_drive_client = client.ArtellaDriveClient.get(extensions=extensions) if init_client else None

    # Load Plugins
    if load_plugins:
        default_plugins_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
        if default_plugins_path not in plugins_path:
            plugins_path.append(default_plugins_path)
        artella.PluginsMgr().register_paths(plugins_path)
        artella.PluginsMgr().load_registered_plugins()

    # Initialize Artella DCC plugin
    artella.DccPlugin(artella_drive_client).init(
        dev=dev, show_dialogs=False, create_menu=create_menu, create_callbacks=create_callbacks)

    updater_plugin = artella.PluginsMgr().get_plugin_by_id('artella-plugins-updater')
    if updater_plugin and updater_plugin.update_is_available(show_dialogs=False):
        updater_plugin.check_for_updates(show_dialogs=False)

    return True


def shutdown(dev=False, cleanup_modules=False):
    """
    Shutdown Artella Plugin

    :param bool cleanup_modules: Whether import artella modules should be removed from sys.path or not
    :return: True if Artella shutdown was successful; False otherwise.
    :rtype: bool
    """

    # Create logger
    logger.create_logger()

    try:
        artella.PluginsMgr().shutdown(dev=dev)
        artella.DccPlugin().shutdown(dev=dev)
    except Exception as exc:
        pass

    # Cleanup artella modules
    if cleanup_modules:

        register.cleanup()

        for k in sys.modules.keys():
            if k.startswith('artella.'):
                del sys.modules[k]

        global CURRENT_DCC
        CURRENT_DCC = None

    return True
