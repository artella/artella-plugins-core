#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella Plugins framework implementation
"""

from __future__ import print_function, division, absolute_import

import logging
import inspect

from artella import dcc
from artella.core import dccplugin

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

        main_menu = dccplugin.DccPlugin().get_main_menu()
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
