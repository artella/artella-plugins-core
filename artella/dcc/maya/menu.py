#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC menu functions
"""

import logging

import maya.cmds as cmds
import maya.mel as mel

LOGGER = logging.getLogger(__name__)


def main_menu_toolbar():
    """
    Returns Main menu toolbar where DCC menus are created by default
    :return: Native object that represents main menu toolbar in current DCC
    :rtype: object
    """

    return mel.eval('$tmp=$gMainWindow')


def get_menus():
    """
    Return all the available menus in current DCC. This function returns specific DCC objects that represents DCC
    UI menus.

    :return: List of all menus names in current DCC
    :rtype: list(object)
    """

    return cmds.lsUI(menus=True)


def check_menu_exists(menu_name):
    """
    Returns whether or not menu with given name exists

    :param str menu_name: name of the menu to search for
    :return: True if the menu already exists; False otherwise
    :rtype: bool
    """

    for menu in get_menus():
        menu_label = cmds.menu(menu, query=True, label=True)
        if menu_label == menu_name:
            return True

    return False


def add_menu(menu_name, parent_menu=None, tear_off=True):
    """
    Creates a new DCC menu.

    :param str menu_name: name of the menu to create
    :param object parent_menu: parent menu to attach this menu into. If not given, menu will be added to
    specific DCC main menu toolbar. Must be specific menu DCC native object
    :return: True if the menu was created successfully; False otherwise
    :return: True if the menu was created successfully; False otherwise
    :rtype: bool
    """

    if not parent_menu:
        parent_menu = main_menu_toolbar()

    if check_menu_exists(menu_name):
        LOGGER.warning('Menu "{}" already exists. Skipping creation.'.format(menu_name))
        return None

    native_menu = cmds.menu(parent=parent_menu, tearOff=tear_off, label=menu_name)
    if not native_menu:
        LOGGER.warning('Impossible to create native Maya menu "{}"'.format(menu_name))
        return None

    return native_menu


def remove_menu(menu_name):
    """
    Removes menu from current DCC if exists

    :param str menu_name: name of the menu to remove
    :return: True if the removal was successful; False otherwise
    :rtype: bool
    """

    for menu in get_menus():
        menu_label = cmds.menu(menu, query=True, label=True)
        if menu_label == menu_name:
            cmds.deleteUI(menu, menu=True)
            return True

    return False


def add_menu_item(menu_item_name, menu_item_command, parent_menu=None):
    """
    Adds a new menu item to the given parent menu. When the item is clicked by the user the given command will be+
    executed
    :param str menu_item_name: name of the menu item to create
    :param str menu_item_command: command to execute when menu item is clicked
    :param object parent_menu: parent menu to attach this menu into. Must be specific menu DCC native object
    :return: New DCC native menu item created or None if the menu item was not created successfully
    :rtype: object or None
    """

    return cmds.menuItem(parent=parent_menu, label=menu_item_name, command=menu_item_command)
