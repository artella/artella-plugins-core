#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains 3ds Max DCC menu functions
"""

from __future__ import print_function, division, absolute_import

import MaxPlus

from artella import logger

DEFAULT_MAX_MENUS = [
    'Edit', 'Tools', 'Group', 'View', 'Create' 'Modifiers', 'Graph Editors', 'Rendering', 'Civil View',
    'Customize', 'Scripting', 'Content', 'Help']


def main_menu_toolbar():
    """
    Returns Main menu toolbar where DCC menus are created by default
    :return: Native object that represents main menu toolbar in current DCC
    :rtype: object
    """

    return MaxPlus.MenuManager.GetMainMenu()


def check_menu_exists(menu_name):
    """
    Returns whether or not menu with given name exists

    :param str menu_name: name of the menu to search for
    :return: True if the menu already exists; False otherwise
    :rtype: bool
    """

    return MaxPlus.MenuManager.MenuExists(menu_name)


def add_menu(menu_name, parent_menu=None, tear_off=True, **kwargs):
    """
    Creates a new DCC menu.

    :param str menu_name: name of the menu to create
    :param object parent_menu: parent menu to attach this menu into. If not given, menu will be added to
    specific DCC main menu toolbar. Must be specific menu DCC native object
    :param bool tear_off: whether or not new created menu can be teared off
    :param bool tear_off: whether or not new created menu can be teared off
    :return: True if the menu was created successfully; False otherwise
    :rtype: bool
    """

    if check_menu_exists(menu_name):
        logger.log_warning('Menu "{}" already exists. Skipping creation.'.format(menu_name))
        return None

    menu_builder = MaxPlus.MenuBuilder(menu_name)

    items = kwargs.get('items', list())
    for item in items:
        add_menu_item(item['name'], item['command'], menu_builder)

    menu_created = False
    if parent_menu:
        menu = MaxPlus.MenuManager.FindMenu(parent_menu)
        if menu:
            menu_builder.Create(menu)
            menu_created = True

    if not menu_created:
        native_menu = menu_builder.Create(main_menu_toolbar())
    else:
        native_menu = MaxPlus.MenuManager.FindMenu(menu_name)
    if not native_menu:
        logger.log_warning('Impossible to create native 3ds Max menu "{}"'.format(menu_name))
        return None

    return native_menu


def remove_menu(menu_name):
    """
    Removes menu from current DCC if exists

    :param str menu_name: name of the menu to remove
    :return: True if the removal was successful; False otherwise
    :rtype: bool
    """

    MaxPlus.MenuManager.UnregisterMenu(menu_name)


def add_menu_item(menu_item_name, menu_item_command, parent_menu=None):
    """
    Adds a new menu item to the given parent menu. When the item is clicked by the user the given command will be+
    executed.
    :param str menu_item_name: name of the menu item to create
    :param str menu_item_command: command to execute when menu item is clicked
    :param object parent_menu: parent menu to attach this menu into. Must be specific menu DCC native object
    :return: New DCC native menu item created or None if the menu item was not created successfully
    :rtype: object or None
    """

    def _make_fn(cmd):
        def _fn(cmd=cmd):
            exec(cmd)
        return _fn

    action = MaxPlus.ActionFactory.Create(menu_item_name, menu_item_name, _make_fn(menu_item_command))
    parent_menu.AddItem(action)
