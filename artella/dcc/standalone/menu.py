#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Standalone application menu functions
"""


def main_menu_toolbar():
    """
    Returns Main menu toolbar where DCC menus are created by default

    :return: Native object that represents main menu toolbar in current DCC
    :rtype: object
    """

    return None


def get_menus():
    """
    Return all the available menus in current DCC. This function returns specific DCC objects that represents DCC
    UI menus.

    :return: List of all menus names in current DCC
    :rtype: list(str)
    """

    return []


def check_menu_exists(menu_name):
    """
    Returns whether or not menu with given name exists

    :param str menu_name: name of the menu to search for
    :return: True if the menu already exists; False otherwise
    :rtype: bool
    """

    return False


def add_menu(menu_name, parent_menu=None, tear_off=True):
    """
    Creates a new DCC menu.

    :param str menu_name: name of the menu to create
    :param object parent_menu: parent menu to attach this menu into. If not given, menu will be added to
    specific DCC main menu toolbar. Must be specific menu DCC native object
    :param bool tear_off: Whether or not new created menu can be tear off from its parent or not
    :return: New DCC native menu object created or None if the menu item was not created successfully
    :rtype: object or None
    """

    return None


def remove_menu(menu_name):
    """
    Removes menu from current DCC if exists

    :param str menu_name: name of the menu to remove
    :return: True if the removal was successful; False otherwise
    :rtype: bool
    """

    return False


def add_menu_item(menu_item_name, menu_item_command, parent_menu, **kwargs):
    """
    Adds a new menu item to the given parent menu. When the item is clicked by the user the given command will be+
    executed
    :param str menu_item_name: name of the menu item to create
    :param str menu_item_command: command to execute when menu item is clicked
    :param object parent_menu: parent menu to attach this menu into. Must be specific menu DCC native object
    :return: New DCC native menu item object created or None if the menu item was not created successfully
    :rtype: object or None
    """

    return None
