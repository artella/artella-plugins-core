#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains 3ds Max DCC menu functions
"""

from __future__ import print_function, division, absolute_import

import MaxPlus

from artella import logger
from . import utils

if utils.get_max_version() >= 2017:
    from pymxs import runtime as rt


def main_menu_toolbar():
    """
    Returns Main menu toolbar where DCC menus are created by default
    :return: Native object that represents main menu toolbar in current DCC
    :rtype: object
    """

    if utils.get_max_version() < 2017:
        return MaxPlus.MenuManager.GetMainMenu()
    else:
        return rt.menuMan.getMainMenuBar()


def get_menus():
    """
    Return all the available menus in current DCC. This function returns specific DCC objects that represents DCC
    UI menus.

    :return: List of all menus names in current DCC
    :rtype: list(object)
    """

    all_menus = list()
    main_menu = main_menu_toolbar()

    if utils.get_max_version() < 2017:
        num_items = main_menu.GetNumItems()
        for i in range(num_items):
            all_menus.append(main_menu.GetItem(i))
    else:
        num_items = main_menu.numItems()
        for i in range(num_items):
            all_menus.append(main_menu.getItem(i))

    return all_menus


def get_menu(menu_name):
    """
    Returns native DCC menu with given name
    :param str menu_name: name of the menu to search for
    :return: Native DCC menu object or None if the menu does not exists
    :rtype: str or None
    """

    if utils.get_max_version() < 2017:
        return MaxPlus.MenuManager.FindMenu(menu_name)
    else:
        return rt.menuMan.findMenu(menu_name)


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

    if utils.get_max_version() < 2017:
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
    else:
        parent_menu = parent_menu if parent_menu is not None else main_menu_toolbar()

        native_menu = rt.menuMan.createMenu(menu_name)
        sub_menu_index = parent_menu.numItems()
        sub_menu_item = rt.menuMan.createSubMenuItem(menu_name, native_menu)
        parent_menu.addItem(sub_menu_item, sub_menu_index)
        rt.menuMan.updateMenuBar()

    return native_menu


def remove_menu(menu_name):
    """
    Removes menu from current DCC if exists

    :param str menu_name: name of the menu to remove
    :return: True if the removal was successful; False otherwise
    :rtype: bool
    """

    MaxPlus.MenuManager.UnregisterMenu(menu_name)


def add_menu_item(menu_item_name, menu_item_command, parent_menu, **kwargs):
    """
    Adds a new menu item to the given parent menu. When the item is clicked by the user the given command will be+
    executed.
    :param str menu_item_name: name of the menu item to create
    :param str menu_item_command: command to execute when menu item is clicked
    :param MenuBuilder parent_menu: parent menu to attach this menu into. Must be specific menu DCC native object
    :return: New DCC native menu item created or None if the menu item was not created successfully
    :rtype: object or None
    """

    if utils.get_max_version() < 2017:
        def _make_fn(cmd):
            def _fn(cmd=cmd):
                exec(cmd)
            return _fn

        action = MaxPlus.ActionFactory.Create(menu_item_name, menu_item_name, _make_fn(menu_item_command))
        parent_menu.AddItem(action)
    else:
        parent_menu = parent_menu if parent_menu is not None else main_menu_toolbar()
        macro_name = 'artella_{}'.format(menu_item_name.replace(' ', '_'))
        category = kwargs.get('category', 'Artella 3ds Max Python Framework Action')
        tooltip = kwargs.get('tooltip', menu_item_name)

        # createActionItem expects a macro
        rt.execute(
            """
            macroScript {}
            category: "{}"
            tooltip: "{}"
            (
                on execute do
                (
                    python.execute "{}"
                )
            )
        """.format(
                macro_name,
                category,
                tooltip,
                menu_item_command
            )
        )

        menu_action = rt.menuMan.createActionItem(macro_name, category)
        menu_action.setUseCustomTitle(True)
        menu_action.setTitle(menu_item_name)
        parent_menu.addItem(menu_action, -1)


def remove_menu_item(menu_item_name, parent_menu):
    """
    Removes a menu item from the given parent menu.
    :param str menu_item_name: name of the menu item to remove
    :param Menu parent_menu: parent menu to remove this menu from. Must be specific menu DCC native object
    :return: Try if the operation was successful; False otherwise.
    :rtype: bool
    """

    if utils.get_max_version() < 2017:
        logger.log_warning(
            'Remove menu item functionality is not available in 3ds Max {}'.format(utils.get_max_version()))
        return

    parent_menu = parent_menu if parent_menu is not None else main_menu_toolbar()

    num_items = parent_menu.numItems()
    for i in range(num_items):
        item = parent_menu.getItem(i + 1)
        if item.getTitle() == menu_item_name:
            parent_menu.removeItem(item)
            return True

    return False


def add_menu_separator(parent_menu):
    """
    Adds a new separator to the given parent menu
    :param MenuBuilder  parent_menu: parent menu to attach this menu into. Must be specific menu DCC native object
    """

    if utils.get_max_version() < 2017:
        return MaxPlus.MenuBuilder.AddSeparator(parent_menu)
    else:
        sep = rt.menuMan.createSeparatorItem()
        parent_menu.addItem(sep, -1)
