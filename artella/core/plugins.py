#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions to manage Artella plugins
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import inspect
import logging

from artella import dcc
from artella.core import consts, utils, plugin

logger = logging.getLogger('artella')

_PLUGINS = dict()
_PLUGIN_PATHS = list()


def plugins():
    """
    Returns a dictionary containing all the info of already registered Artella plugins
    :return: Dictionary with already loaded Artella plugins information
    :rtype :dict
    """

    return _PLUGINS


def plugin_paths():
    """
    Returns a list of paths where Artella Plugin Manager will find for plugins
    :return: List of plugin directory paths
    :rtype: list(str)
    """

    return _PLUGIN_PATHS


def get_plugin_by_name(plugin_name):
    """
    Returns plugin instance by its name
    :param plugin_name: Name of the plugin to retrieve
    :return: Returns plugin instance if a plugin with the given name is loaded; None otherwise.
    :rtype: ArtellaPlugin
    """

    if not _PLUGINS:
        return None

    for plugin_id, plugin_dict in _PLUGINS.items():
        plug_name = plugin_dict['name']
        if plugin_name == plug_name:
            return plugin_dict['plugin_instance']

    return None


def get_plugin_by_id(plugin_id):
    """
    Returns plugin instance by its ID
    :param plugin_id: Name of the plugin to retrieve (for example, artella-plugin-test)
    :return: Returns plugin instance if a plugin with the given ID is loaded; None otherwise.
    :rtype: ArtellaPlugin
    """

    if not _PLUGINS:
        return None

    for plug_id, plugin_dict in _PLUGINS.items():
        if plug_id == plugin_id:
            return plugin_dict['plugin_instance']


def register_paths(plugin_paths):
    """
    Registers given path into the list of Artella plugin paths.
    :param str plugin_paths: Path that will be used by Artella Plugins Manager to search plugins into.
    """

    plugin_paths = utils.force_list(plugin_paths, remove_duplicates=True)

    for plugin_path in plugin_paths:
        plugin_path = utils.clean_path(plugin_path)
        if not plugin_path or not os.path.isdir(plugin_path) or plugin_path in _PLUGIN_PATHS:
            return

        _PLUGIN_PATHS.append(plugin_path)


def load_registered_plugins(dev=False):
    """
    Loads all the plugins found in the registered plugin paths
    :return:
    """

    plugin_paths = list(set([
        utils.clean_path(plugin_path) for plugin_path in _PLUGIN_PATHS if os.path.isdir(plugin_path)]))
    if not plugin_paths:
        logger.info('No Artella Plugins found to load!')
        return

    found_paths = dict()

    for plugin_path in plugin_paths:
        for root, dirs, files in os.walk(plugin_path):
            if consts.ARTELLA_PLUGIN_CONFIG not in files:
                continue
            clean_path = utils.clean_path(root)
            found_paths[clean_path] = os.path.join(root, consts.ARTELLA_PLUGIN_CONFIG)

    if not found_paths:
        logger.info('No plugins found in registered plugin paths: {}'.format(_PLUGIN_PATHS))
        return

    for plugin_path in plugin_paths:
        for plugin_dir in os.listdir(plugin_path):
            clean_path = utils.clean_path(os.path.join(plugin_path, plugin_dir))
            if os.path.isdir(clean_path) and clean_path not in sys.path:
                sys.path.append(clean_path)

    for plugin_path, plugin_config in found_paths.items():

        # Search sub modules paths
        sub_modules_found = list()
        for sub_module in utils.iterate_modules(plugin_path):
            file_name = os.path.splitext(os.path.basename(sub_module))[0]
            if file_name.startswith('_') or file_name.startswith('test_') or sub_module.endswith('.pyc'):
                continue
            if not sub_module or sub_module in sub_modules_found:
                continue
            sub_modules_found.append(sub_module)
        if not sub_modules_found:
            continue

        # Find specific DCC plugin implementation
        dcc_name = dcc.name()
        sub_module = sub_modules_found[0]

        max_length = 50
        index = 0
        artella_module_parts = list()
        temp_sub_module = sub_module
        while True:
            if index > max_length:
                artella_module_parts = list()
                break
            base_name = os.path.basename(temp_sub_module)
            if not base_name or base_name == 'artella':
                artella_module_parts.append(base_name)
                break
            artella_module_parts.append(base_name)
            temp_sub_module = os.path.dirname(temp_sub_module)
            index += 1
        if not artella_module_parts:
            module_path = utils.convert_module_path_to_dotted_path(os.path.normpath(sub_module))
        else:
            module_path = os.path.splitext('.'.join(reversed(artella_module_parts)))[0]

        module_path_split = module_path.split('.')
        dcc_module_path = '{}.{}.{}'.format('.'.join(module_path_split[:-1]), dcc_name, module_path_split[-1])
        sub_module_obj = utils.import_module(dcc_module_path, skip_exceptions=True)
        if not sub_module_obj:
            sub_module_obj = utils.import_module(module_path)
            if not sub_module_obj:
                logger.error('Error while importing Artella Plugin module: {}'.format(module_path))
                continue

        if dev:
            plugin_version = 'DEV'
        else:
            plugin_version = None
            module_path_dir = module_path.rsplit('.', 1)[0]
            version_module_path = '{}.__version__'.format(module_path_dir)
            version_module_path = version_module_path.replace('.{}.__'.format(dcc_name), '.__')
            try:
                version_module_obj = utils.import_module(version_module_path)
            except Exception:
                version_module_obj = None
            if version_module_obj:
                try:
                    plugin_version = version_module_obj.get_version()
                except Exception as exc:
                    logger.warning(
                        'Impossible to retrieve version for Artella Plugin module: {} | {}'.format(module_path, exc))

        for member in utils.iterate_module_members(sub_module_obj, predicate=inspect.isclass):
            register_plugin(member[1], plugin_config, os.path.dirname(sub_module), plugin_version)

    if not _PLUGINS:
        logger.warning('No Artella plugins found to load!')
        return

    ordered_plugins_list = list()
    for plugin_id, plugin_dict in _PLUGINS.items():
        plugin_class = plugin_dict['class']
        plugin_index = plugin_class.INDEX or -1
        index = 0
        for i, plugin_item in enumerate(ordered_plugins_list):
            plugin_item_index = list(plugin_item.values())[0]['index']
            if plugin_index < plugin_item_index:
                index += 1
        ordered_plugins_list.insert(index, {plugin_id: {'index': plugin_index, 'dict': plugin_dict}})

    for plugin_item in ordered_plugins_list:
        plugin_id = list(plugin_item.keys())[0]
        plugin_dict = list(plugin_item.values())[0]['dict']
        plugin_class = plugin_dict['class']
        plugin_config_dict = plugin_dict.get('config', dict())
        try:
            plugin_inst = plugin_class(plugin_config_dict)
        except Exception as exc:
            logger.error('Impossible to instantiate Artella Plugin: "{}" | {}'.format(plugin_id, exc))
            continue
        _PLUGINS[plugin_id]['plugin_instance'] = plugin_inst


def register_plugin(class_obj, config_path, plugin_path, plugin_version=None, plugin_interface=None):
    """
    Registers an Artella plugin instance into the manager
    :param class_obj:
    :param config_path:
    :param plugin_path:
    :param plugin_version:
    :param plugin_interface:
    :return:
    :rtype: bool
    """

    if not config_path or not os.path.isfile(config_path):
        logger.warning(
            'Impossible to register Artella Plugin: {} because its config file does not exists: {}!'.format(
                class_obj, config_path))
        return False

    plugin_interface = plugin_interface or plugin.ArtellaPlugin

    if not issubclass(class_obj, plugin_interface):
        return True

    plugin_id = None
    if hasattr(class_obj, 'ID'):
        plugin_id = getattr(class_obj, 'ID')
    if not plugin_id:
        plugin_id = class_obj.__name__
    if plugin_id in _PLUGINS:
        logger.warning('Artella Plugin: "{}" already registered!'.format(plugin_id))
        return True

    try:
        plugin_config = utils.read_json(config_path)
    except Exception:
        logger.warning(
            'Artella Plugin "{}" configuration file "{}" has not a proper structure. Skipping plugin ...'.format(
                plugin_id, config_path))
        return False

    plugin_name = plugin_config.get('name', None)
    plugin_package = plugin_config.get('package', None)
    plugin_icon = plugin_config.get('icon', None)
    plugin_resources = plugin_config.get('resources', None)

    # Register DCC resources, both DCC specific plugin implementation
    # resources and generic implementation resources
    plugin_resources_paths = list()
    if plugin_resources and plugin_path:
        plugin_path_base = os.path.basename(plugin_path)
        if plugin_path_base == dcc.name():
            plugin_resources_paths.append(os.path.join(plugin_path, plugin_resources))
            plugin_resources_paths.append(os.path.join(os.path.dirname(plugin_path), plugin_resources))
        else:
            plugin_resources_paths.append(os.path.join(plugin_path, plugin_resources))
        for plugin_resources_path in plugin_resources_paths:
            if os.path.isdir(plugin_resources_path):
                dcc.register_dcc_resource_path(plugin_resources_path)
                icons_path = os.path.join(plugin_resources_path, 'icons')
                if os.path.isdir(icons_path):
                    dcc.register_dcc_resource_path(icons_path)

    _PLUGINS[plugin_id] = {
        'name': plugin_name,
        'package': plugin_package,
        'icon': plugin_icon,
        'class': class_obj,
        'config': plugin_config,
        'version': plugin_version,
        'resource_paths': plugin_resources_paths
    }

    logger.info('Artella Plugin: "{}" registered successfully!'.format(plugin_id))

    return True


def shutdown(dev=False):
    """
    Unloads all current loaded Artella plugins
    """

    if not _PLUGINS:
        return

    for plugin_id, plugin_dict in _PLUGINS.items():
        plugin_inst = plugin_dict.get('plugin_instance', None)
        if not plugin_inst:
            continue
        if dev:
            plugin_inst.cleanup()
        else:
            dcc.execute_deferred(plugin_inst.cleanup)
