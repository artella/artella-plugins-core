#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for artella
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import logging.config

from artella import dcc
from artella.core import consts, utils, client, resource, plugins, dccplugin, dcc as dcc_core


def create_logger():
    """
    Creates Artella logger based on logging.ini configuration file
    :return:
    """

    logger_path = os.path.normpath(os.path.join(os.path.expanduser('~'), 'artella', 'logs'))
    if not os.path.isdir(logger_path):
        os.makedirs(logger_path)

    logging.config.fileConfig(
        os.path.normpath(os.path.join(os.path.dirname(__file__), 'logging.ini')), disable_existing_loggers=False)


def register_dcc_paths(dcc_paths=None):

    # Register DCC paths
    dccs_path = utils.force_list(dcc_paths)
    valid_dcc_paths = list()
    dcc_paths_str = ''
    default_dccs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dccs')
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


def init(
        dcc_paths=None, init_client=True, plugin_paths=None, extensions=None, dev=False,
        load_plugins=True, create_menu=True, create_callbacks=True):
    """
    Initializes Artella Plugin

    :param bool init_client: Whether or not Artella Drive Client should be initialized during initialization.
        Useful to avoid to connect to Artella client when developing DCC specific functionality.
    :param list(str) plugin_paths: List of paths where Artella plugins can be located
    :param list(str) extensions: List of extensions to register
    :param bool dev: Whether or not initialization should be done in dev mode
    :param bool load_plugins: Whether or not Artella Plugins should be loaded
    :param bool create_menu: Whether or not Artella menu should be created
    :param bool create_callbacks: Whether or not Artella DCC plugin callbacks should be created
    :return: True if Artella initialization was successful; False otherwise.
    :rtype: bool
    """

    register_dcc_paths(dcc_paths)

    plugins_path = plugin_paths if plugin_paths is not None else list()
    extensions = extensions if extensions is not None else list()

    artella_logger = logging.getLogger('artella')

    # Make sure that Artella Drive client and DCC are cached during initialization
    current_dcc = dcc_core.current_dcc()
    if not current_dcc:
        artella_logger.error('Impossible to load Artella Plugin because no DCC is available!')
        return False

    # Due to the TCP server, Artella plugin freezes some DCCs (such as Maya) if its execute in batch mode (through
    # console). For now we skip Artella plugin initialization in that scenario.
    if dcc.is_batch():
        return False

    shutdown(dev=dev)

    # Specific DCC extensions are managed by the client
    dcc_extensions = dcc.extensions() or list()
    extensions.extend(dcc_extensions)

    # Initialize resources and theme
    resource.register_resources_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources'))

    # Create Artella Drive Client
    artella_drive_client = client.ArtellaDriveClient.get(extensions=extensions) if init_client else None

    # Load Plugins
    if load_plugins:
        default_plugins_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
        if default_plugins_path not in plugins_path:
            plugins_path.append(default_plugins_path)
        plugins.register_paths(plugin_paths)
        plugins.load_registered_plugins(dev=dev)

    # Initialize Artella DCC plugin
    dccplugin.DccPlugin(artella_drive_client).init(
        dev=dev, show_dialogs=False, create_menu=create_menu, create_callbacks=create_callbacks,
        init_client=init_client)

    if not dev:
        updater_plugin = plugins.get_plugin_by_id('artella-plugins-updater')
        if updater_plugin and updater_plugin.update_is_available(show_dialogs=False):
            updater_plugin.check_for_updates(show_dialogs=False)

    return True


def shutdown(dev=False):
    """
    Shutdown Artella Plugin

    :return: True if Artella shutdown was successful; False otherwise.
    :rtype: bool
    """

    try:
        plugins.shutdown(dev=dev)
        dccplugin.DccPlugin().shutdown(dev=dev)
    except Exception as exc:
        pass

    return True


create_logger()
