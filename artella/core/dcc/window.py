#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract window implementation
"""

from __future__ import print_function, division, absolute_import

from artella import dcc
from artella.core import utils, qtutils, resource
from artella.widgets import theme

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets


class _MetaWindow(type):

    def __call__(cls, *args, **kwargs):
        if dcc.is_maya():
            from artella.dccs.maya import window
            return window.MayaWindow
        else:
            return BaseWindow


class AbstractWindow(object):

    @utils.abstract
    def get_main_layout(self):
        pass

    @utils.abstract
    def setup_ui(self):
        pass


if not qtutils.QT_AVAILABLE:
    class BaseWindow(object):
        pass
else:
    class BaseWindow(QtWidgets.QMainWindow):
        def __init__(self, parent=None, **kwargs):
            if not parent:
                from artella import dcc
                parent = dcc.get_main_window()

            super(BaseWindow, self).__init__(parent, **kwargs)

            self._pos_anim = QtCore.QPropertyAnimation(self)
            self._pos_anim.setTargetObject(self)
            self._pos_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            self._pos_anim.setDuration(300)
            self._pos_anim.setPropertyName(b'pos')

            self._opacity_anim = QtCore.QPropertyAnimation()
            self._opacity_anim.setTargetObject(self)
            self._opacity_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            self._opacity_anim.setDuration(300)
            self._opacity_anim.setPropertyName(b'windowOpacity')
            self._opacity_anim.setStartValue(0.0)
            self._opacity_anim.setEndValue(1.0)

            self.setup_ui()
            theme.theme().apply(self)

            self._fade_in()

        def get_main_layout(self):
            main_layout = QtWidgets.QVBoxLayout()
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            return main_layout

        def setup_ui(self):
            main_widget = QtWidgets.QWidget()
            self.main_layout = self.get_main_layout()
            main_widget.setLayout(self.main_layout)
            self.setCentralWidget(main_widget)

            artella_frame = QtWidgets.QFrame()
            artella_frame.setObjectName('artellaFrame')
            artella_frame_layout = QtWidgets.QHBoxLayout()
            artella_frame.setLayout(artella_frame_layout)

            artella_header = QtWidgets.QLabel()
            artella_header_pixmap = resource.pixmap('artella_header')
            artella_header.setPixmap(artella_header_pixmap)
            artella_frame_layout.addStretch()
            artella_frame_layout.addWidget(artella_header)
            artella_frame_layout.addStretch()

            self.main_layout.addWidget(artella_frame)

        def fade_close(self):
            self._fade_out()

        # =================================================================================================================
        # INTERNAL
        # =================================================================================================================

        def _fade_out(self):
            self._opacity_anim.finished.connect(self.close)
            self._pos_anim.setDirection(QtCore.QAbstractAnimation.Backward)
            self._pos_anim.start()
            self._opacity_anim.setDirection(QtCore.QAbstractAnimation.Backward)
            self._opacity_anim.start()

        def _fade_in(self):
            self._pos_anim.start()
            self._opacity_anim.start()


@utils.add_metaclass(_MetaWindow)
class Window(AbstractWindow):
    pass
