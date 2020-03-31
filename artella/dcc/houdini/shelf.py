#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Houdini DCC plugin specific implementation
"""

from __future__ import print_function, division, absolute_import

import hou
from hou import shelves

import artella


def get_shelf(shelf_name):
    """
    Returns shelf by name

    :param str shelf_name: name of the shelf to retrieve
    :return: Houdini object shelf if the shelf was found; None otherwise.
    :rtype: hou.Shelf
    """

    current_shelves = shelves.shelves()
    for k, v in current_shelves.items():
        if k == shelf_name:
            return v

    return None


def shelf_exists(shelf_name):
    """
    Returns whether given shelf exits or not

    :param str shelf_name: name of the shelf we want to check if exists or not
    :return: True if the shelf exists; False otherwise
    :rtype: bool
    """

    current_shelves = shelves.shelves()
    if shelf_name in current_shelves.keys():
        return True

    return False


def create_shelf(shelf_name, shelf_label):
    """
    Creates new Shelf

    :param str shelf_name: internal Houdini object name of the shelf we want to create
    :param str shelf_label: name used in the label in the shelf UI
    :return: Houdini object of the new created shelf
    :rtype: hou.Shelf
    """

    return shelves.newShelf(name=shelf_name, label=shelf_label)


def remove_shelf(name):
    """
    Removes given shelf with the given name (if exists)

    :param str name: name of the shelf we want to destroy
    :return: True if the removal operation was successful; False otherwise.
    :rtype: bool
    """

    if not shelf_exists(shelf_name=name):
        return

    shelf = get_shelf(shelf_name=name)
    if not shelf:
        return False

    shelf.destroy()

    return True


def get_shelf_set(shelf_set_name):
    """
    Returns shelf set by name

    :param str shelf_set_name: Name of the shelf set we want to retrieve
    :return: Houdini shelf set object with the given name
    :rtype: hou.ShelfSet
    """

    current_shelve_sets = shelves.shelfSets()
    for k, v in current_shelve_sets.items():
        if k == shelf_set_name:
            return v

    return None


def shelf_set_exists(shelf_set_name):
    """
    Returns whether given shelf set exits or not

    :param str shelf_set_name: name of the shelf set we want to check if exists or not
    :return: True if the shelf exists; False otherwise
    :rtype: bool
    """

    current_shelve_sets = shelves.shelfSets()
    if shelf_set_name in current_shelve_sets.keys():
        return True

    return False


def create_shelf_set(shelf_set_name, shelf_set_label, dock=True):
    """
    Creates new Shelf

    :param str shelf_set_name: internal Houdini object name of the shelf set we want to create
    :param str shelf_set_label: name used in the label in the shelf set UI
    :param bool dock: Whether or not we want to dock newly created shelf set
    :return: Houdini object of the new created shelf set
    :rtype: hou.ShelfSet
    """

    new_shelf_set = shelves.newShelfSet(name=shelf_set_name, label=shelf_set_label)
    if new_shelf_set and dock:
        dock_shelf_set(shelf_set_name=shelf_set_name)

    return new_shelf_set


def remove_shelf_set(shelf_set_name):
    """
    Removes given shelf set with the given name (if exists)

    :param str shelf_set_name: name of the shelf set we want to destroy
    :return: True if the removal operation was successful; False otherwise.
    :rtype: bool
    """

    if not shelf_set_exists(shelf_set_name=shelf_set_name):
        return

    shelf_set = get_shelf_set(shelf_set_name=shelf_set_name)
    if not shelf_set:
        return False

    shelf_set.destroy()

    return True


def dock_shelf_set(shelf_set_name, dock_name='Build'):
    """
    Docks given shelf set into given dock name

    :param str shelf_set_name: name of the set we want to dock
    :param str dock_name: name of the dock we want to add
    :rtype: True if the operation was successful; False otherwise.
    :rtype: bool
    """

    hou.hscript('shelfdock -d {} add {}'.format(dock_name, shelf_set_name))


def undock_shelf_set(shelf_set_name, dock_name='Build'):
    """
    Undocks given shelf set into given dock name

    :param shelf_set_name: str
    :param dock_name: str
    :rtype: True if the operation was successful; False otherwise.
    :rtype: bool
    """

    hou.hscript('shelfdock -d {} remove {}'.format(dock_name, shelf_set_name))


def create_shelf_tool(tool_name, tool_label, tool_script, tool_type='python', icon=None, help=None):
    """
    Creates a new Houdini Python shelf tool
    :param str tool_name: name of the tool we want to create
    :param str tool_label: name that will appear in the tool UI
    :param str tool_script: script that will be executed when tool is launched
    :param str tool_type: type of tool we want to create ('python' or 'hscript')
    :param str icon: name of the icon to use by the tool
    :param str help: help string that will be show when the user access the tool help
    :return: Newly created shelf tool Houdini object
    :rtype: ShelfTool
    """

    language = None
    if tool_type == 'python':
        language = hou.scriptLanguage.Python
    elif tool_type == 'hscript':
        language = hou.scriptLanguage.HScript
    if language is None:
        artella.log_warning(
            'Impossible to create shelf tool {} because script language {} is not supported by Houdini'.format(
                tool_name, tool_type))
        return None

    return shelves.newTool(
        name=tool_name, label=tool_label, script=tool_script, icon=icon, help=help, language=language)
