#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Artella divider widget
"""

from __future__ import print_function, division, absolute_import

from artella.core import qtutils
from artella.widgets import label

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets


if not qtutils.QT_AVAILABLE:
    class ArtellaDivider(object):
        def __init__(self, *args, **kwargs):
            super(ArtellaDivider, self).__init__()
else:
    class ArtellaDivider(QtWidgets.QWidget, object):
        ALIGNMENT = {
            QtCore.Qt.AlignCenter: 50,
            QtCore.Qt.AlignLeft: 20,
            QtCore.Qt.AlignRight: 80,
        }

        def __init__(self, text='', orientation=QtCore.Qt.Horizontal, alignment=QtCore.Qt.AlignCenter, parent=None):
            super(ArtellaDivider, self).__init__(parent)
            self._orient = orientation
            self._text_label = label.ArtellaLabel().secondary()
            self._left_frame = QtWidgets.QFrame()
            self._right_frame = QtWidgets.QFrame()
            self._main_lay = QtWidgets.QHBoxLayout()
            self._main_lay.setContentsMargins(0, 0, 0, 0)
            self._main_lay.setSpacing(0)
            self._main_lay.addWidget(self._left_frame)
            self._main_lay.addWidget(self._text_label)
            self._main_lay.addWidget(self._right_frame)
            self.setLayout(self._main_lay)

            if orientation == QtCore.Qt.Horizontal:
                self._left_frame.setFrameShape(QtWidgets.QFrame.HLine)
                self._left_frame.setFrameShadow(QtWidgets.QFrame.Sunken)
                self._right_frame.setFrameShape(QtWidgets.QFrame.HLine)
                self._right_frame.setFrameShadow(QtWidgets.QFrame.Sunken)
            else:
                self._text_label.setVisible(False)
                self._right_frame.setVisible(False)
                self._left_frame.setFrameShape(QtWidgets.QFrame.VLine)
                self._left_frame.setFrameShadow(QtWidgets.QFrame.Plain)
                self.setFixedWidth(2)
            self._main_lay.setStretchFactor(self._left_frame, self.ALIGNMENT.get(alignment, 50))
            self._main_lay.setStretchFactor(self._right_frame, 100 - self.ALIGNMENT.get(alignment, 50))
            self._text = None
            self.set_artella_text(text)

        def set_artella_text(self, value):
            self._text = value
            self._text_label.setText(value)
            if self._orient == QtCore.Qt.Horizontal:
                self._text_label.setVisible(bool(value))
                self._right_frame.setVisible(bool(value))

        def get_artella_text(self):
            return self._text

        artella_text = QtCore.Property(str, get_artella_text, set_artella_text)

        @classmethod
        def left(cls, text=''):
            return cls(text, alignment=QtCore.Qt.AlignLeft)

        @classmethod
        def right(cls, text=''):
            return cls(text, alignment=QtCore.Qt.AlignRight)

        @classmethod
        def center(cls, text=''):
            return cls(text, alignment=QtCore.Qt.AlignCenter)

        @classmethod
        def vertical(cls):
            return cls(orientation=QtCore.Qt.Vertical)
