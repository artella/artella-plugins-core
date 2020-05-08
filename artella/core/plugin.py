#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella Plugins framework implementation
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import inspect

import artella
from artella import dcc
from artella import logger
from artella import register
from artella.core import consts, utils


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
            self.cleanup()

        main_menu = artella.DccPlugin().get_main_menu()
        if not main_menu:
            return

        plugin_menu = self._config_dict.get('menu')
        plugin_package = self._config_dict.get('package', 'Artella')

        if plugin_menu and 'label' in plugin_menu:
            menu_label = plugin_menu['label']
            menu_command = plugin_menu['command']
            dcc.add_menu_item(menu_label, menu_command, main_menu)

        self._loaded = True

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

            if plugin_path not in sys.path:
                print('Adding: {}'.format(plugin_path))
                sys.path.append(plugin_path)

            self._plugin_paths.append(plugin_path)

    def load_registered_plugins(self):
        """
        Loads all the plugins found in the registered plugin paths
        :return:
        """

        plugin_paths = list(set([
            utils.clean_path(plugin_path) for plugin_path in self._plugin_paths if os.path.isdir(plugin_path)]))
        if not plugin_paths:
            logger.log_info('No Artella Plugins found to load!')
            return

        found_paths = dict()

        for plugin_path in plugin_paths:
            for root, dirs, files in os.walk(plugin_path):
                if consts.ARTELLA_PLUGIN_CONFIG not in files:
                    continue
                clean_path = utils.clean_path(root)
                found_paths[clean_path] = os.path.join(root, consts.ARTELLA_PLUGIN_CONFIG)
                if clean_path not in sys.path:
                    print('Adding: {}'.format(clean_path))
                    sys.path.append(clean_path)

        if not found_paths:
            logger.log_info('No plugins found in registered plugin paths: {}'.format(self._plugin_paths))
            return

        for plugin_path, plugin_config in found_paths.items():

            # Search sub modules paths
            sub_modules_found = list()
            for sub_module in utils.iterate_modules(plugin_path):
                file_name = os.path.splitext(os.path.basename(sub_module))[0]
                if file_name.startswith('__') or sub_module.endswith('.pyc'):
                    continue
                if not sub_module or sub_module in sub_modules_found:
                    continue
                sub_modules_found.append(sub_module)
            if not sub_modules_found:
                continue

            # Find specific DCC plugin implementation
            sub_module = None
            dcc_name = dcc.name()
            for sub_module_found in sub_modules_found:
                parent_dir_name = os.path.basename(os.path.dirname(sub_module_found))
                if parent_dir_name == dcc_name:
                    sub_module = sub_module_found
                    break
            if not sub_module:
                sub_module = sub_modules_found[0]

            module_path = utils.convert_module_path_to_dotted_path(os.path.normpath(sub_module))

            try:
                sub_module_obj = utils.import_module(module_path)
            except Exception as exc:
                logger.log_error('Error while importing Artella Plugin module: {} | {}'.format(module_path, exc))
                continue
            if not sub_module_obj:
                continue

            for member in utils.iterate_module_members(sub_module_obj, predicate=inspect.isclass):
                self.register_plugin(member[1], plugin_config)

        if not self._plugins:
            logger.log_warning('No Artella plugins found to load!')
            return

        ordered_plugins_list = list()
        for plugin_id, plugin_dict in self._plugins.items():
            plugin_class = plugin_dict['class']
            plugin_index = plugin_class.INDEX or -1
            added = False
            for i, plugin_item in enumerate(ordered_plugins_list):
                plugin_item_index = plugin_item.values()[0]['index']
                if plugin_index < plugin_item_index:
                    ordered_plugins_list.insert(i, {plugin_id: {'index': plugin_index, 'dict': plugin_dict}})
                    added = True
                    break
            if not added:
                ordered_plugins_list.append({plugin_id: {'index': plugin_index, 'dict': plugin_dict}})

        for plugin_item in ordered_plugins_list:
            plugin_id = plugin_item.keys()[0]
            plugin_dict = plugin_item.values()[0]['dict']
            plugin_class = plugin_dict['class']
            plugin_config_dict = plugin_dict.get('config', dict())
            try:
                plugin_inst = plugin_class(plugin_config_dict, manager=self)
            except Exception as exc:
                logger.log_error('Impossible to instantiate Artella Plugin: "{}" | {}'.format(plugin_id, exc))
                continue
            self._plugins[plugin_id]['plugin_instance'] = plugin_inst

    def register_plugin(self, class_obj, config_path):
        """
        Registers an Artella plugin instance into the manager
        :param class_obj:
        :param config_path:
        :return:
        :rtype: bool
        """

        if not config_path or not os.path.isfile(config_path):
            logger.log_warning(
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
            logger.log_warning('Artella Plugin: "{}" already registered!'.format(plugin_id))
            return True

        try:
            plugin_config = utils.read_json(config_path)
        except Exception as exc:
            logger.log_warning(
                'Artella Plugin "{}" configuration file "{}" has not a proper structure. Skipping plugin ...'.format(
                    plugin_id, config_path))
            return True

        plugin_name = plugin_config.get('name', None)
        plugin_package = plugin_config.get('package', None)
        plugin_icon = plugin_config.get('icon', None)
        plugin_resources = plugin_config.get('resources', None)

        self._plugins[plugin_id] = {
            'name': plugin_name,
            'package': plugin_package,
            'icon': plugin_icon,
            'class': class_obj,
            'config': plugin_config
        }

        logger.log_info('Artella Plugin: "{}" registered successfully!'.format(plugin_id))

        return True

    def shutdown(self):
        """
        Unloads all current loaded Artella plugins
        """

        if not self._plugins:
            return

        for plugin_id, plugin_dict in self._plugins.items():
            plugin_inst = plugin_dict.get('plugin_instance', None)
            if not plugin_inst:
                continue
            plugin_inst.cleanup()


@utils.Singleton
class ArtellaPluginsManagerSingleton(ArtellaPluginsManager, object):
    def __init__(self):
        ArtellaPluginsManager.__init__(self)


register.register_class('PluginsMgr', ArtellaPluginsManagerSingleton)
