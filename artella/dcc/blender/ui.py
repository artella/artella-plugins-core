#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Blender DCC UI implementation
"""

from __future__ import print_function, division, absolute_import

import bpy


def get_main_window():
    """
    Returns Qt object that references to the main DCC window we are working on

    :return: An instance of the current DCC Qt main window
    :rtype: QMainWindow or QWidget or None
    """

    return None


def show_info(title, message):
    """
    Shows a confirmation dialog that users need to accept/reject.
    :param str title: text that is displayed in the title bar of the dialog
    :param str message: text which is shown to the user telling them what operation they need to confirm

    :return: True if the user accepted the operation; False otherwise.
    :rtype: bool
    """

    def _text(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(_text, title=title, icon='INFO')


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

    raise NotImplementedError('Not implemented yet')


def show_warning(title, message, print_message=False):
    """
    Shows a warning message box that can be used to show warning text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str message: default text which is placed n the plain text edit
    :param bool print_message: whether or not print message in DCC output command window
    """

    def _text(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(_text, title=title, icon='ERROR')


def show_error(title, message, print_message=False):
    """
    Shows an error message box that can be used to show critical text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str message: default text which is placed n the plain text edit
    :param bool print_message: whether or not print message in DCC output command window
    """

    def _text(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(_text, title=title, icon='ERROR')
