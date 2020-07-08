#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract menu functions
"""

from artella.core.dcc import reroute
from artella.core.utils import abstract


@reroute
@abstract
def main_menu_toolbar():
    """
    Returns Main menu toolbar where DCC menus are created by default

    :return: Native object that represents main menu toolbar in current DCC
    :rtype: object
    """

    pass


@reroute
@abstract
def get_menus():
    """
    Return all the available menus in current DCC. This function returns specific DCC objects that represents DCC
    UI menus.

    :return: List of all menus names in current DCC
    :rtype: list(str)
    """

    pass


@reroute
@abstract
def get_menu_items():
    """
    Returns all available menu items in current DCC. This function returns specific DCC objects that represents DCC
    UI menu items.

    :return: List of all menu item names in current DCC
    :rtype: list(str)
    """

    pass


@reroute
@abstract
def get_menu(menu_name):
    """
    Returns native DCC menu with given name
    :param str menu_name: name of the menu to search for
    :return: Native DCC menu object or None if the menu does not exists
    :rtype: str or None
    """

    pass


@reroute
@abstract
def get_menu_item(menu_item_name):
    """
    Returns native DCC menu item with given name
    :param str menu_item_name: name of the menu item to search for
    :return: Native DCC menu object or None if the menu does not exists
    :rtype: str or None
    """

    pass


@reroute
@abstract
def check_menu_exists(menu_name):
    """
    Returns whether or not menu with given name exists

    :param str menu_name: name of the menu to search for
    :return: True if the menu already exists; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def add_menu(menu_name, parent_menu=None, tear_off=True, icon='', **kwargs):
    """
    Creates a new DCC menu.

    :param str menu_name: name of the menu to create
    :param object parent_menu: parent menu to attach this menu into. If not given, menu will be added to
    specific DCC main menu toolbar. Must be specific menu DCC native object
    :param bool tear_off: Whether or not new created menu can be tear off from its parent or not
    :param str icon: name of the icon to be used in this menu
    :return: New DCC native menu object created or None if the menu item was not created successfully
    :rtype: object or None
    """

    pass


@reroute
@abstract
def remove_menu(menu_name):
    """
    Removes menu from current DCC if exists

    :param str menu_name: name of the menu to remove
    :return: True if the removal was successful; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def add_menu_item(menu_item_name, menu_item_command='', parent_menu=None, icon='', **kwargs):
    """
    Adds a new menu item to the given parent menu. When the item is clicked by the user the given command will be+
    executed
    :param str menu_item_name: name of the menu item to create
    :param str menu_item_command: command to execute when menu item is clicked
    :param object parent_menu: parent menu to attach this menu into. Must be specific menu DCC native object
    :param str icon: name of the icon to be used in this menu item
    :return: New DCC native menu item object created or None if the menu item was not created successfully
    :rtype: object or None
    """

    pass


@reroute
@abstract
def add_sub_menu_item(menu_item_name, menu_item_command='', parent_menu=None, icon='', **kwargs):
    """
    Adds a new sub menu item to the given parent menu. When the item is clicked by the user the given command will be+
    executed
    :param str menu_item_name: name of the menu item to create
    :param str menu_item_command: command to execute when menu item is clicked
    :param object parent_menu: parent menu to attach this menu into. Must be specific menu DCC native object
    :param str icon: name of the icon to be used in this menu item
    :return: New DCC native menu item object created or None if the menu item was not created successfully
    :rtype: object or None
    """

    pass


@reroute
@abstract
def remove_menu_item(menu_item_name, parent_menu):
    """
    Removes a menu item from the given parent menu.
    :param str menu_item_name: name of the menu item to remove
    :param object parent_menu: parent menu to remove this menu from. Must be specific menu DCC native object
    :return: Trie if the operation was successful; False otherwise.
    :rtype: bool
    """

    pass


@reroute
@abstract
def add_menu_separator(parent_menu):
    """
    Adds a new separator to the given parent menu
    :param object parent_menu: parent menu to attach this menu into. Must be specific menu DCC native object
    """

    pass
