#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive Qt related utils classes and functions
"""

from __future__ import print_function, division, absolute_import

import os
import string
import logging
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from artella.core import utils

QT_AVAILABLE = True
try:
    from artella.externals.Qt import QtCore, QtWidgets, QtGui, __binding__
except ImportError as exc:
    QT_AVAILABLE = False

if QT_AVAILABLE:
    # Some DCCs do not include shiboken, we check all possible locations
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
                except ImportError:
                    pass

    # If QApplication does not exists we force its creation
    try:
        app = QtWidgets.QApplication.instance()
        if not app:
            QtWidgets.QApplication([])
    except TypeError:
        QT_AVAILABLE = False

DEFAULT_DPI = 96

if utils.is_python3():
    long = int

logger = logging.getLogger('artella')


class StyleTemplate(string.Template):
    delimiter = '@'
    idpattern = r'[_a-z][_a-z0-9]*'


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
        logger.error('Failed to wrap object {} ...'.format(ptr))
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


def get_active_window():
    """
    Returns current active window
    :return:
    """

    if not QT_AVAILABLE:
        return None

    return QtWidgets.QApplication.activeWindow()


def icon(icon_path, color=None):
    """
    Returns Qt icon instance

    :param icon_path: Path were icon resource is located
    :param color:
    :return: New instance of a Qt icon
    :rtype: QtGui.QIcon
    """

    icon_pixmap = pixmap(icon_path, color=color)
    new_icon = QtGui.QIcon(icon_pixmap)

    return new_icon


def pixmap(pixmap_path, color=None):
    """
    Returns Qt pixmap instance

    :param pixmap_path: Path were pixmap resource is located
    :param color:
    :return: New instance of a Qt pixmap
    :rtype: QtGui.QPixmap
    """

    if color and isinstance(color, str):
        from artella.widgets import color as artella_color
        color = artella_color.from_string(color)

    new_pixmap = QtGui.QPixmap(pixmap_path)

    if not new_pixmap.isNull() and color:
        painter = QtGui.QPainter(new_pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawRect(new_pixmap.rect())
        painter.end()

    return new_pixmap


def style(style_path):
    """
    Returns Qt style instance
    :param style_path: Path where style resource is located
    :return: str
    """

    loaded_style = ''
    if not style_path or not os.path.isfile(style_path):
        return loaded_style

    with open(style_path, 'r') as f:
        loaded_style = StyleTemplate(f.read())

    return loaded_style


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

    if not QT_AVAILABLE:
        return '', False

    from artella import dcc

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

    if not QT_AVAILABLE:
        return '', False

    from artella import dcc

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

    if not QT_AVAILABLE:
        return

    from artella import dcc

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

    if not QT_AVAILABLE:
        return None

    from artella import dcc

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

    if not QT_AVAILABLE:
        return

    from artella import dcc
    from artella.core import resource

    parent = parent if parent else dcc.get_main_window()
    window_icon = resource.icon('artella')

    message_box = QtWidgets.QMessageBox(parent)
    message_box.setWindowTitle(title)
    message_box.setWindowIcon(window_icon)
    message_box.setIcon(message_box.Icon.Warning)
    flags = message_box.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.WindowStaysOnTopHint
    if text:
        message_box.setText(text)
    message_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    message_box.setWindowFlags(flags)
    message_box.exec_()


def show_error_message_box(title, text, parent=None):
    """
    Shows an error message box that can be used to show critical text to users.

    :param str title: text that is displayed in the title bar of the dialog
    :param str text: default text which is placed n the plain text edit
    :param QWidget parent: optional parent widget for the input text dialog. If not given, current DCC main parent
        window will be used.
    """

    if not QT_AVAILABLE:
        return

    from artella import dcc
    from artella.core import resource

    parent = parent if parent else dcc.get_main_window()
    window_icon = resource.icon('artella')

    message_box = QtWidgets.QMessageBox(parent)
    message_box.setWindowTitle(title)
    message_box.setWindowIcon(window_icon)
    message_box.setIcon(message_box.Icon.Critical)
    flags = message_box.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.WindowStaysOnTopHint
    if text:
        message_box.setText(text)
    message_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    message_box.setWindowFlags(flags)
    message_box.exec_()


def dpi_multiplier():
    """
    Returns current application DPI multiplier

    :return: float
    """

    return max(1, float(QtWidgets.QApplication.desktop().logicalDpiY()) / float(DEFAULT_DPI))


def dpi_scale(value):
    """
    Resizes by value based on current DPI

    :param int value: value default 2k size in pixels
    :return: size in pixels now DPI monitor is (4k 2k etc)
    :rtype: int
    """

    mult = dpi_multiplier()
    return value * mult


def clear_layout(layout):
    """
    Removes all the widgets added in the given layout
    :param layout: QLayout
    """

    while layout.count():
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout())


def is_stackable(widget):
    """
    Returns whether or not given widget is stackable
    :param widget: QWidget
    :return: bool
    """

    return issubclass(widget, QtWidgets.QWidget) and hasattr(widget, 'widget') and hasattr(widget, 'currentChanged')
