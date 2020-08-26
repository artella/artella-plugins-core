#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella Plugins framework implementation
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import logging
import inspect

import artella
import artella.dcc as dcc
import artella.register as register
from artella.core import consts, utils

logger = logging.getLogger('artella')


class ArtellaPlugin(object):

    ID = ''                 # Unique ID of the Artella Plugin
    INDEX = -1              # Index of the plugin. This index will control the instantiation order
    VERSION = None          # Version of the Artella Plugin
    PACKAGE = None          # Package Artella Plugin belongs to

    def __init__(self, config_dict=None, manager=None):

        self._config_dict = config_dict or dict()
        self._manager = manager
        self._stats = ArtellaPluginStats(self)
        self._loaded = False

        self.init()

    def is_loaded(self):
        """
        Returns whether or not this plugin is loaded
        :return: True if the plugin is loaded; False otherwise.
        :rtype: bool
        """

        return self._loaded

    def init(self):
        """
        Function that is called when plugin is instantiated
        """

        if self._loaded:
            dcc.execute_deferred(self.cleanup)

        dcc.execute_deferred(self.init_ui)

        self._loaded = True

    def init_ui(self):
        """
        Function that initializes plugin UI related functionality
        """

        main_menu = artella.DccPlugin().get_main_menu()
        if not main_menu:
            return

        plugin_menu = self._config_dict.get('menu')
        plugin_package = self._config_dict.get('package', 'Artella')
        plugin_dccs = self._config_dict.get('dcc', list())

        can_load_plugin = True
        if plugin_dccs:
            can_load_plugin = dcc.name() in plugin_dccs

        if can_load_plugin:
            if plugin_menu and 'label' in plugin_menu:
                menu_parents = plugin_menu.get('parents', None)
                if menu_parents:
                    current_parent = 'Artella' if dcc.check_menu_exists('Artella') else None
                    for menu_parent in menu_parents:
                        if not dcc.check_menu_exists(menu_parent):

                            # TODO: Before More Artella menu addition we force the creation of a
                            # TODO: separator. We should find a way to avoid hardcoded this.
                            icon = ''
                            if menu_parent == 'More Artella':
                                dcc.add_menu_separator('Artella')
                                icon = 'artella.png'

                            dcc.add_sub_menu_item(menu_parent, parent_menu=current_parent, icon=icon)
                        current_parent = menu_parent

                menu_label = plugin_menu['label']
                menu_command = plugin_menu['command']
                menu_icon = self._config_dict.get('icon', '')
                if menu_parents:
                    menu_parent = menu_parents[-1]
                    dcc.add_menu_item(menu_label, menu_command, menu_parent, icon=menu_icon)
                else:
                    dcc.add_menu_item(menu_label, menu_command, main_menu, icon=menu_icon)

    def cleanup(self):
        """
        Function that is called when the plugin is disabled
        """

        plugin_menu = self._config_dict.get('menu')
        menu = dcc.get_menu('Artella')

        if plugin_menu and menu:
            menu_label = plugin_menu['label']
            dcc.remove_menu_item(menu_label, menu)

        self._loaded = False

    @property
    def manager(self):
        """
        Returns Artella Plugins manager instance that is owner of this plugin

        :return: Artella Plugin manager instance that owns this plugin
        :rtype: ArtellaPluginsManager
        """

        return self._manager

    @property
    def stats(self):
        """
        Returns Artella Plugin Stats instance that stores useful data related with the plugin

        :return: Artella Plugin Stats instance with useful data of the plugin
        :rtype: ArtellaPluginStats
        """

        return self._stats


class ArtellaPluginStats(object):
    def __init__(self, plugin):
        self._plugin = plugin
        self._id = self._plugin.ID
        self._start_time = 0.0
        self._end_time = 0.0
        self._execution_time = 0.0
        self._info = dict()
        self._init()

    @property
    def start_time(self):
        """
        Returns the time the plugin was executed

        :return: Time the plugin was executed
        :rtype: str
        """

        return self._start_time

    @start_time.setter
    def start_time(self, value):
        """
        Sets the time the plugin was executed

        :param str value: Time the plugin was executed
        """

        self._start_time = value

    @property
    def end_time(self):
        """
        Returns the time the plugin ended its execution

        :return: Time the plugin was executed
        :rtype: str
        """

        return self._end_time

    @end_time.setter
    def end_time(self, value):
        """
        Sets the time the plugin ended its execution

        :param str value: Time the plugin ended its execution
        """

        self._end_time = value

    @property
    def execution_time(self):
        """
        Returns the the total amount of execution time of the plugin

        :return: Total execution time of the plugin during current session in seconds
        :rtype: float
        """

        return self._execution_time

    def _init(self):
        """
        Internal function that initializes info for the plugin and its environment
        """

        from artella import dcc

        self._info.update({
            'name': self._plugin.__class__.__name__,
            'module': self._plugin.__class__.__module__,
            'filepath': inspect.getfile(self._plugin.__class__),
            'id': self._id,
            'application': dcc.name()
        })


class ArtellaPluginsManager(object):

    PLUGIN_INTERFACE = ArtellaPlugin

    def __init__(self):
        self._plugins = dict()
        self._plugin_paths = list()

    @property
    def plugins(self):
        """
        Returns a dictionary containing all the info of already registered Artella plugins
        :return: Dictionary with already loaded Artella plugins information
        :rtype :dict
        """

        return self._plugins

    @property
    def plugin_paths(self):
        """
        Returns a list of paths where Artella Plugin Manager will find for plugins
        :return: List of plugin directory paths
        :rtype: list(str)
        """

        return self._plugin_paths

    def get_plugin_by_name(self, plugin_name):
        """
        Returns plugin instance by its name
        :param plugin_name: Name of the plugin to retrieve
        :return: Returns plugin instance if a plugin with the given name is loaded; None otherwise.
        :rtype: ArtellaPlugin
        """

        if not self._plugins:
            return None

        for plugin_id, plugin_dict in self._plugins.items():
            plug_name = plugin_dict['name']
            if plugin_name == plug_name:
                return plugin_dict['plugin_instance']

        return None

    def get_plugin_by_id(self, plugin_id):
        """
        Returns plugin instance by its ID
        :param plugin_id: Name of the plugin to retrieve (for example, artella-plugin-test)
        :return: Returns plugin instance if a plugin with the given ID is loaded; None otherwise.
        :rtype: ArtellaPlugin
        """

        if not self._plugins:
            return None

        for plug_id, plugin_dict in self._plugins.items():
            if plug_id == plugin_id:
                return plugin_dict['plugin_instance']

    def register_paths(self, plugin_paths):
        """
        Registers given path into the list of Artella plugin paths.
        :param str plugin_paths: Path that will be used by Artella Plugins Manager to search plugins into.
        """

        plugin_paths = utils.force_list(plugin_paths, remove_duplicates=True)

        for plugin_path in plugin_paths:
            plugin_path = utils.clean_path(plugin_path)
            if not plugin_path or not os.path.isdir(plugin_path) or plugin_path in self._plugin_paths:
                return

            self._plugin_paths.append(plugin_path)

    def load_registered_plugins(self):
        """
        Loads all the plugins found in the registered plugin paths
        :return:
        """

        plugin_paths = list(set([
            utils.clean_path(plugin_path) for plugin_path in self._plugin_paths if os.path.isdir(plugin_path)]))
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
            logger.info('No plugins found in registered plugin paths: {}'.format(self._plugin_paths))
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
                    logger.error('Error while importing Artella Plugin module: {} | {}'.format(module_path, exc))
                    continue

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
                self.register_plugin(member[1], plugin_config, os.path.dirname(sub_module), plugin_version)

        if not self._plugins:
            logger.warning('No Artella plugins found to load!')
            return

        ordered_plugins_list = list()
        for plugin_id, plugin_dict in self._plugins.items():
            plugin_class = plugin_dict['class']
            plugin_index = plugin_class.INDEX or -1
            index = 0
            for i, plugin_item in enumerate(ordered_plugins_list):
                plugin_item_index = plugin_item.values()[0]['index']
                if plugin_index < plugin_item_index:
                    index += 1
            ordered_plugins_list.insert(index, {plugin_id: {'index': plugin_index, 'dict': plugin_dict}})

        for plugin_item in ordered_plugins_list:
            plugin_id = plugin_item.keys()[0]
            plugin_dict = plugin_item.values()[0]['dict']
            plugin_class = plugin_dict['class']
            plugin_config_dict = plugin_dict.get('config', dict())
            try:
                plugin_inst = plugin_class(plugin_config_dict, manager=self)
            except Exception as exc:
                logger.error('Impossible to instantiate Artella Plugin: "{}" | {}'.format(plugin_id, exc))
                continue
            self._plugins[plugin_id]['plugin_instance'] = plugin_inst

    def register_plugin(self, class_obj, config_path, plugin_path, plugin_version=None):
        """
        Registers an Artella plugin instance into the manager
        :param class_obj:
        :param config_path:
        :param plugin_path:
        :param plugin_version:
        :return:
        :rtype: bool
        """

        if not config_path or not os.path.isfile(config_path):
            logger.warning(
                'Impossible to register Artella Plugin: {} because its config file does not exists: {}!'.format(
                    class_obj, config_path))
            return True

        if not issubclass(class_obj, self.PLUGIN_INTERFACE):
            return True

        plugin_id = None
        if hasattr(class_obj, 'ID'):
            plugin_id = getattr(class_obj, 'ID')
        if not plugin_id:
            plugin_id = class_obj.__name__
        if plugin_id in self._plugins:
            logger.warning('Artella Plugin: "{}" already registered!'.format(plugin_id))
            return True

        try:
            plugin_config = utils.read_json(config_path)
        except Exception as exc:
            logger.warning(
                'Artella Plugin "{}" configuration file "{}" has not a proper structure. Skipping plugin ...'.format(
                    plugin_id, config_path))
            return True

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

        self._plugins[plugin_id] = {
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

    def shutdown(self, dev=False):
        """
        Unloads all current loaded Artella plugins
        """

        if not self._plugins:
            return

        for plugin_id, plugin_dict in self._plugins.items():
            plugin_inst = plugin_dict.get('plugin_instance', None)
            if not plugin_inst:
                continue
            if dev:
                plugin_inst.cleanup()
            else:
                dcc.execute_deferred(plugin_inst.cleanup)


@utils.Singleton
class ArtellaPluginsManagerSingleton(ArtellaPluginsManager, object):
    def __init__(self):
        ArtellaPluginsManager.__init__(self)


register.register_class('PluginsMgr', ArtellaPluginsManagerSingleton)
