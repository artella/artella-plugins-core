#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Houdini DCC plugin specific implementation
"""

from __future__ import print_function, division, absolute_import

import artella
from artella import register
import artella.plugin as plugin
from artella.core.utils import Singleton


class ArtellaHoudiniPlugin(plugin.ArtellaPlugin, object):
    def __init__(self, artella_drive_client):
        super(ArtellaHoudiniPlugin, self).__init__(artella_drive_client=artella_drive_client)

    def create_menus(self):
        """
        Setup DCC Artella menu.
        If the menu already exists, it will be deleted and recreated.

        :return: True if the menu was created successfully; False otherwise
        :rtype: bool
        """

        from artella.dcc.houdini import shelf

        if shelf.shelf_set_exists(self.MENU_NAME):
            shelf.remove_shelf_set(self.MENU_NAME)

        new_shelf = shelf.create_shelf_set(shelf_set_name=self.MENU_NAME, shelf_set_label=self.MENU_NAME, dock=True)

        if shelf.shelf_exists(self.MENU_NAME):
            shelf.remove_shelf(self.MENU_NAME)
        shelve = shelf.create_shelf(self.MENU_NAME, self.MENU_NAME)

        shelf_tools = [
            shelf.create_shelf_tool(
                'save_to_cloud', 'Save to Cloud', 'import artella; artella.DccPlugin().make_new_version()'),
            shelf.create_shelf_tool(
                'get_deps', 'Get Dependencies', 'import artella; artella.DccPlugin().get_dependencies()')
        ]

        shelve.setTools(shelf_tools)

        new_shelf.setShelves([shelve])


@Singleton
class ArtellaHoudiniPluginSingleton(ArtellaHoudiniPlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaHoudiniPlugin.__init__(self, artella_drive_client=artella_drive_client)


register.register_class('DccPlugin', ArtellaHoudiniPluginSingleton)
