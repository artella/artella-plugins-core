#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC plugin specific implementation
"""

from __future__ import print_function, division, absolute_import

import artella
from artella import register
import artella.dcc as dcc
import artella.plugin as plugin
from artella.core.utils import Singleton


class ArtellaMaxPlugin(plugin.ArtellaPlugin, object):
    def __init__(self, artella_drive_client):
        super(ArtellaMaxPlugin, self).__init__(artella_drive_client=artella_drive_client)

    def create_menus(self):
        """
        Setup DCC Artella menu.
        If the menu already exists, it will be deleted and recreated.

        :return: True if the menu was created successfully; False otherwise
        :rtype: bool
        """

        if dccs.check_menu_exists(self.MENU_NAME):
            dccs.remove_menu(self.MENU_NAME)

        menu_items = [
            {'name': 'Save to Cloud', 'command': 'import artella; artella.DccPlugin().make_new_version()'},
            {'name': 'Get Dependencies', 'command': 'import artella; artella.DccPlugin().get_dependencies()'}
        ]
        dccs.add_menu(self.MENU_NAME, items=menu_items)


@Singleton
class ArtellaMaxPluginSingleton(ArtellaMaxPlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaMaxPlugin.__init__(self, artella_drive_client=artella_drive_client)


register.register_class('Plugin', ArtellaMaxPluginSingleton)
