#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget to show images
"""

from __future__ import print_function, division, absolute_import

from artella.core import qtutils, resource
from artella.widgets import theme

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets, QtGui


if not qtutils.QT_AVAILABLE:
    class ArtellaImage(object):
        def __init__(self, *args, **kwargs):
            pass
else:
    class ArtellaImage(QtWidgets.QLabel, object):
        def __init__(self, parent=None):
            super(ArtellaImage, self).__init__(parent)

            self._default_pixmap = resource.pixmap('artella')
            self._pixmap = self._default_pixmap
            self._artella_size = 0
            self.set_artella_size(theme.theme().default_size)

        def set_artella_size(self, value):
            self._artella_size = value
            self._set_artella_size()

        def _set_artella_size(self):
            self.setFixedSize(QtCore.QSize(self._artella_size, self._artella_size))
            self._set_artella_image()

        def _set_artella_image(self):
            self.setPixmap(self._pixmap.scaledToWidth(self.height(), QtCore.Qt.SmoothTransformation))

        def set_artella_image(self, value):
            """
            Set avatar image.
            :param value: QPixmap or None.
            :return: None
            """
            if value is None:
                self._pixmap = self._default_pixmap
            elif isinstance(value, QtGui.QPixmap):
                self._pixmap = value
            else:
                raise TypeError("Input argument 'value' should be QPixmap or None, but get {}".format(type(value)))
            self._set_artella_image()

        def get_artella_image(self):
            return self._pixmap

        def get_artella_size(self):
            return self._artella_size

        artella_image = QtCore.Property(QtGui.QPixmap, get_artella_image, set_artella_image)
        artella_size = QtCore.Property(int, get_artella_size, set_artella_size)

        @classmethod
        def tiny(cls, image=None):
            inst = cls()
            inst.set_artella_size(theme.theme().tiny)
            inst.set_artella_image(image)
            return inst

        @classmethod
        def small(cls, image=None):
            inst = cls()
            inst.set_artella_size(theme.theme().small)
            inst.set_artella_image(image)
            return inst

        @classmethod
        def medium(cls, image=None):
            inst = cls()
            inst.set_artella_size(theme.theme().medium)
            inst.set_artella_image(image)
            return inst

        @classmethod
        def large(cls, image=None):
            inst = cls()
            inst.set_artella_size(theme.theme().large)
            inst.set_artella_image(image)
            return inst

        @classmethod
        def huge(cls, image=None):
            inst = cls()
            inst.set_artella_size(theme.theme().huge)
            inst.set_artella_image(image)
            return inst
