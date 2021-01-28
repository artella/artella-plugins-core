#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC reroute functions
"""

from __future__ import print_function, division, absolute_import

from artella.core.dcc import reroute
from artella.core.utils import abstract

main = __import__('__main__')


class Dccs(object):
    Standalone = 'standalone'
    Maya = 'maya'
    Max = 'max'
    Houdini = 'houdini'

    packages = {
        'cmds': Maya,
        'pymxs': Max,
        'hou': Houdini,
    }


def is_standalone():
    """
    Check if current environment is standalone or not
    :return: bool
    """

    return not any(pkg in list(main.__dict__.keys()) for pkg in Dccs.packages)


def is_maya():
    """
    Checks if Maya is available or not
    :return: bool
    """

    return 'cmds' in main.__dict__


def is_max():
    """
    Checks if Max is available or not
    :return: bool
    """

    return 'MaxPlus' in main.__dict__ or 'pymxs' in main.__dict__


def is_mobu():
    """
    Checks if MotionBuilder is available or not
    :return: bool
    """

    return 'pyfbsdk' in main.__dict__


def is_houdini():
    """
    Checks if Houdini is available or not
    :return: bool
    """

    return 'hou' in main.__dict__


def is_unreal():
    """
    Checks if Unreal is available or not
    :return: bool
    """

    try:
        import unreal
    except ImportError:
        return False

    return True


@reroute
@abstract
def name():
    """
    Returns name of current DCC

    :return: Returns name of DCC without any info about version
    :rtype: str
    """

    pass


@reroute
@abstract
def nice_name():
    """
    Returns nice name of current DCC

    :return: Returns formatted DCC name
    :rtype: str
    """

    pass


@reroute
@abstract
def version():
    """
    Returns version of DCC application

    :return: Returns integer number indicating the version of the DCC application
    :rtype: int
    """

    pass


@reroute
@abstract
def extensions():
    """
    Returns a list of available extension for DCC application

    :return: List of available extensions with the following format: .{EXTENSION}
    :rtype: list(str)
    """

    pass


@reroute
@abstract
def scene_name():
    """
    Returns the name of the current scene

    :return: Full file path name of the current scene. If no file is opened, None is returned.
    :rtype: str or None
    """

    pass


@reroute
@abstract
def new_scene(force=True, **kwargs):
    """
    Creates a new scene inside DCC
    :param force: True to skip saving of the current opened DCC scene; False otherwise.
    :return: True if the new scene is created successfully; False otherwise.
    :rtype: bool
    """

    pass


@reroute
@abstract
def scene_is_modified():
    """
    Returns whether or not current opened DCC file has been modified by the user or not

    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def open_scene(file_path, save=True):
    """
    Opens DCC scene file
    :param str file_path: Absolute local file path we want to open in current DCC
    :param bool save: Whether or not save current opened DCC scene file
    :return: True if the save operation was successful; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def save_scene(force=True, **kwargs):
    """
    Saves DCC scene file

    :param bool force: Whether to force the saving operation or not
    :return: True if the save operation was successful; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def import_scene(file_path):
    """
    Opens scene file into current opened DCC scene file
    :param str file_path: Absolute local file path we want to import into current DCC
    :return: True if the import operation was successful; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def reference_scene(file_path, **kwargs):
    """
    References scene file into current opened DCC scene file
    :param str file_path: Absolute local file path we want to reference into current DCC
    :return: True if the reference operation was successful; False otherwise
    :rtype: bool
    """

    pass


@reroute
@abstract
def supports_uri_scheme():
    """
    Returns whether or not current DCC support URI scheme implementation

    :return: True if current DCC supports URI scheme implementation; False otherwise
    """

    pass


@reroute
@abstract
def pass_message_to_main_thread_fn():
    """
    Returns function used by DCC to execute a function in DCC main thread in the next idle event of that thread.

    :return If DCC API supports it, returns function to call a function in main thread from other thread
    """

    pass


@reroute
@abstract
def is_batch():
    """
    Returns whether or not current DCC is being executed in batch mode (no UI)
    :return: True if current DCC session is being executed in batch mode; False otherwise.
    :rtype: bool
    """

    pass


@reroute
@abstract
def clean_path(file_path):
    """
    Cleans given path so it can be properly used by current DCC

    :param str file_path: file path we want to clean
    :return: Cleaned version of the given file path
    :rtype: str
    """

    pass


@reroute
@abstract
def get_installation_paths(versions=None):
    """
    Returns installation path of the given versions of current DCC

    :param list(int) versions: list of versions to find installation paths of. If not given, current DCC version
        installation path will be returned
    :return: List of installation paths of the given DCC versions
    :rtype: list(str)
    """

    pass


@reroute
@abstract
def is_udim_path(file_path):
    """
    Returns whether or not given file path is an UDIM one

    :param str file_path: File path we want to check
    :return: True if the given paths is an UDIM path; False otherwise.
    :rtype: bool
    """

    pass


@reroute
@abstract
def execute_deferred(fn):
    """
    Executes given function in deferred mode (once DCC UI has been loaded)
    :param callable fn: Function to execute in deferred mode
    :return:
    """

    pass


@reroute
@abstract
def register_dcc_resource_path(resources_path):
    """
    Registers path into given DCC so it can find specific resources
    :param resources_path: str, path we want DCC to register
    """

    pass


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


@reroute
@abstract
def get_main_window():
    """
    Returns Qt object that references to the main DCC window we are working on

    :return: An instance of the current DCC Qt main window
    :rtype: QMainWindow or QWidget or None
    """

    pass


@reroute
@abstract
def show_info(title, message):
    """
    Shows an information dialog that users need to accept/reject.

    :param str title: text that is displayed in the title bar of the dialog
    :param str message: text which is shown to the user telling them what operation they need to confirm
    :return: True if the user accepted the operation; False otherwise.
    :rtype: bool
    """

    pass


@reroute
@abstract
def show_question(title, message, cancel=True):
    """
    Shows a question message box that can be used to show question text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str message: text which is shown to the user telling them what operation they need to confirm
    :param bool cancel: Whether or not cancel button should appear in question message box
    :return: True if the user presses the Ok button; False if the user presses the No button; None if the user preses
        the Cancel button
    :rtype: bool or None
    """

    pass


@reroute
@abstract
def show_warning(title, message, print_message=False):
    """
    Shows a warning message box that can be used to show warning text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str message: default text which is placed n the plain text edit
    :param bool print_message: whether or not print message in DCC output command window
    """

    pass


@reroute
@abstract
def show_error(title, message, print_message=False):
    """
    Shows an error message box that can be used to show critical text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str message: default text which is placed n the plain text edit
    :param bool print_message: whether or not print message in DCC output command window
    """

    pass


@reroute
@abstract
def input_comment(title, label, text=''):
    """
    Shows a comment input dialog that users can use to input text.

    :param str title: text that is displayed in the title bar of the dialog
    :param str label: text which is shown to the user telling them what kind of text they need to input
    :param str text: default text which is placed in the comment section
    :return: Tuple containing as the first element the text typed by the user and as the second argument a boolean
        that will be True if the user clicked on the Ok button or False if the user cancelled the operation
    :rtype: tuple(str, bool)
    """

    pass
