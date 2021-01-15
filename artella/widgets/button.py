#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella button widgets
"""

from __future__ import print_function, division, absolute_import

from artella.core import qtutils, resource
from artella.widgets import theme

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets


if not qtutils.QT_AVAILABLE:
    class ArtellaToolButton(object):
        def __init__(self, *args, **kwargs):
            super(ArtellaToolButton, self).__init__()
else:
    class ArtellaToolButton(QtWidgets.QToolButton):
        def __init__(self, parent=None):
            super(ArtellaToolButton, self).__init__(parent=parent)

            self._artella_image = None
            self._artella_size = theme.theme().default_size

            self.setAutoExclusive(False)
            self.setAutoRaise(True)
            self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

            self._polish_icon()
            self.toggled.connect(self._polish_icon)

        def enterEvent(self, event):
            if self._artella_image:
                self.setIcon(resource.icon(self._artella_image, color=theme.theme().main_color))
            return super(ArtellaToolButton, self).enterEvent(event)

        def leaveEvent(self, event):
            self._polish_icon()
            return super(ArtellaToolButton, self).leaveEvent(event)

        def get_artella_size(self):
            return self._artella_size

        def set_artella_size(self, value):
            self._artella_size = value
            self.style().polish(self)
            if self.toolButtonStyle() == QtCore.Qt.ToolButtonIconOnly:
                self.setFixedSize(QtCore.QSize(self._artella_size, self._artella_size))

        def get_artella_image(self):
            return self._artella_image

        def set_artella_image(self, path):
            self._artella_image = path
            self._polish_icon()

        artella_size = QtCore.Property(int, get_artella_size, set_artella_size)

        def huge(self):
            self.set_artella_size(theme.theme().huge)
            return self

        def large(self):
            self.set_artella_size(theme.theme().large)
            return self

        def medium(self):
            self.set_artella_size(theme.theme().medium)
            return self

        def small(self):
            self.set_artella_size(theme.theme().small)
            return self

        def tiny(self):
            self.set_artella_size(theme.theme().tiny)
            return self

        def image(self, path):
            self.set_artella_image(path)
            return self

        def icon_only(self):
            self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
            self.setFixedSize(QtCore.QSize(self._artella_size, self._artella_size))
            return self

        def text_only(self):
            self.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
            return self

        def text_beside_icon(self):
            self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
            return self

        def text_under_icon(self):
            self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            return self

        def _polish_icon(self, *args, **kwargs):
            if self._artella_image:
                if self.isCheckable() and self.isChecked():
                    self.setIcon(resource.icon(self._artella_image, color=theme.theme().main_color))
                else:
                    self.setIcon(resource.icon(self._artella_image))
