#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive Qt related utils classes and functions
"""

from __future__ import print_function, division, absolute_import

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import artella
from artella.core import utils

QT_AVAILABLE = True
try:
    from artella.externals.Qt import QtCore, QtWidgets, QtGui, __binding__
except ImportError as exc:
    QT_AVAILABLE = False

if QT_AVAILABLE:

    # Some DCCs do not include shiboken by , we check all possible locations

    if __binding__ in ['PySide2', 'PyQt5']:
        try:
            import shiboken2 as shiboken
        except ImportError:
            from PySide2 import shiboken2 as shiboken
    else:
        try:
            import shiboken
        except ImportError:
            try:
                from Shiboken import shiboken
            except ImportError:
                try:
                    from PySide import shiboken
                except Exception:
                    pass

if utils.is_python3():
    long = int


def is_pyqt():
    """
    Returns whether or not current Qt Python binding available is a PyQt one.

    :return: True if the current Qt binding is PyQt; False otherwise.
    :rtype: bool
    """

    return 'PyQt' in __binding__


def is_pyqt4():
    """
    Returns whether or not current Qt Python binding available is PtQt 4.

    :return: True if the current Qt binding is PyQt4; False otherwise.
    :rtype: bool
    """

    return __binding__ == 'PyQt4'


def is_pyqt5():
    """
    Returns whether or not current Qt Python binding available is PtQt 5.

    :return: True if the current Qt binding is PyQt5; False otherwise.
    :rtype: bool
    """

    return __binding__ == 'PyQt5'


def is_pyside():
    """
    Returns whether or not current Qt Python binding available is PySide.

    :return: rue if the current Qt binding is PySide; False otherwise.
    :rtype: bool
    """

    return __binding__ == 'PySide'


def is_pyside2():
    """
    Returns whether or not current Qt Python binding available is PySide 2.

    :return: True if the current Qt binding is PySide2; False otherwise.
    :rtype: bool
    """

    return __binding__ == 'PySide2'


def wrapinstance(ptr, base=None):
    """
    Wraps given object in a Qt object
    :param ptr:
    :param base: QObject, base QWidget class we want to wrap given object
    :return:
    """

    if ptr is None:
        return None

    ptr = long(ptr)
    if 'shiboken' in globals():
        if base is None:
            qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
            meta_obj = qObj.metaObject()
            cls = meta_obj.className()
            super_cls = meta_obj.superClass().className()
            if hasattr(QtGui, cls):
                base = getattr(QtGui, cls)
            elif hasattr(QtGui, super_cls):
                base = getattr(QtGui, super_cls)
            else:
                base = QtWidgets.QWidget
        try:
            return shiboken.wrapInstance(long(ptr), base)
        except Exception:
            from PySide.shiboken import wrapInstance
            return wrapInstance(long(ptr), base)
    elif 'sip' in globals():
        base = QtCore.QObject
        return shiboken.wrapinstance(long(ptr), base)
    else:
        artella.log_error('Failed to wrap object {} ...'.format(ptr))
        return None


def unwrapinstance(obj):
    """
    Unwraps given object from a Qt object
    :param obj: QObject
    :return:
    """

    return long(shiboken.getCppPointer(obj)[0])


def to_qt_object(long_ptr, qobj=None):
    """
    Returns an instance of the Maya UI element as a QWidget
    :param long_ptr:
    :param qobj:
    :return:
    """

    if not qobj:
        qobj = QtWidgets.QWidget

    return wrapinstance(long_ptr, qobj)


def show_string_input_dialog(title, label, text='', parent=None):
    """
    Shows a line string input dialog that users can use to input text.

    :param str title: text that is displayed in the title bar of the dialog
    :param str label: text which is shown to the user telling them what kind of text they need to input
    :param str text: default text which is placed n the plain text edit
    :param QWidget parent: optional parent widget for the input text dialog. If not given, current DCC main parent
        window will be used.
    :return: Tuple containing as the first element the text typed by the user and as the second argument a boolean
        that will be True if the user clicked on the Ok button or False if the user cancelled the operation
    :rtype: tuple(str, bool)
    """

    import artella.dcc as dcc

    parent = parent if parent else dcc.get_main_window()

    string_dialog = QtWidgets.QInputDialog()
    flags = string_dialog.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.WindowStaysOnTopHint

    typed_string, res = string_dialog.getText(parent, title, label, text=text, flags=flags)

    return typed_string, res


def show_comment_input_dialog(title, label, text='', parent=None):
    """
    Shows a text string input dialog that users can use to input text.

    :param str title: text that is displayed in the title bar of the dialog
    :param str label: text which is shown to the user telling them what kind of text they need to input
    :param str text: default text which is placed in the comment section
    :param QWidget parent: optional parent widget for the input text dialog. If not given, current DCC main parent
        window will be used.
    :return: Tuple containing as the first element the text typed by the user and as the second argument a boolean
        that will be True if the user clicked on the Ok button or False if the user cancelled the operation
    :rtype: tuple(str, bool)
    """

    import artella.dcc as dcc

    parent = parent if parent else dcc.get_main_window()

    comment_dialog = QtWidgets.QInputDialog()
    flags = comment_dialog.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.WindowStaysOnTopHint

    if hasattr(QtWidgets.QInputDialog, 'getMultiLineText'):
        comment, res = comment_dialog.getMultiLineText(parent, title, label, text=text, flags=flags)
    else:
        comment, res = comment_dialog.getText(parent, title, label, text, text=text, flags=flags)

    return comment, res


def show_info_message_box(title, text, parent=None):
    """
    Shows an info message box that can be used to show information text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str text: default text which is placed n the plain text edit
    :param QWidget parent: optional parent widget for the input text dialog. If not given, current DCC main parent
        window will be used.
    """

    import artella.dcc as dcc

    parent = parent if parent else dcc.get_main_window()

    QtWidgets.QMessageBox.information(parent, title, text)


def show_question_message_box(title, text, cancel=True, parent=None):
    """
    Shows a question message box that can be used to show question text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str text: default text which is placed n the plain text edit
    :param bool cancel: Whether or not cancel button should appear in question message box
    :param QWidget parent: optional parent widget for the input text dialog. If not given, current DCC main parent
        window will be used.
    :return: True if the user presses the Ok button; False if the user presses the No button; None if the user preses
        the Cancel button
    :rtype: bool or None
    """

    import artella.dcc as dcc

    parent = parent if parent else dcc.get_main_window()

    message_box = QtWidgets.QMessageBox(parent)
    message_box.setWindowTitle(title)
    flags = message_box.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.WindowStaysOnTopHint
    if text:
        message_box.setText(text)
    if cancel:
        message_box.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
    else:
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    message_box.setWindowFlags(flags)
    result = message_box.exec_()

    if result == QtWidgets.QMessageBox.Yes:
        return True
    elif result == QtWidgets.QMessageBox.No:
        return False
    elif result == QtWidgets.QMessageBox.Cancel:
        return None


def show_warning_message_box(title, text, parent=None):
    """
    Shows a warning message box that can be used to show warning text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str text: default text which is placed n the plain text edit
    :param QWidget parent: optional parent widget for the input text dialog. If not given, current DCC main parent
        window will be used.
    """

    import artella.dcc as dcc

    parent = parent if parent else dcc.get_main_window()

    QtWidgets.QMessageBox.warning(parent, title, text)


def show_error_message_box(title, text, parent=None):
    """
    Shows an error message box that can be used to show critical text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str text: default text which is placed n the plain text edit
    :param QWidget parent: optional parent widget for the input text dialog. If not given, current DCC main parent
        window will be used.
    """

    import artella.dcc as dcc

    parent = parent if parent else dcc.get_main_window()

    QtWidgets.QMessageBox.critical(parent, title, text)
