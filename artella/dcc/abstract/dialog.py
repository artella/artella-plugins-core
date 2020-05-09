#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract dialog implementation
"""

from __future__ import print_function, division, absolute_import

from artella import register
from artella.core import qtutils

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets

if not qtutils.QT_AVAILABLE:
    class AbstractDialog(object):
        pass
else:
    class AbstractDialog(QtWidgets.QDialog, object):

        closed = QtCore.Signal()

        def __init__(self, parent=None, **kwargs):
            if not parent:
                from artella import dcc
                parent = dcc.get_main_window()

            super(AbstractDialog, self).__init__(parent, **kwargs)

            self._pos_anim = QtCore.QPropertyAnimation(self)
            self._pos_anim.setTargetObject(self)
            self._pos_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            self._pos_anim.setDuration(300)
            self._pos_anim.setPropertyName('pos')

            self._opacity_anim = QtCore.QPropertyAnimation()
            self._opacity_anim.setTargetObject(self)
            self._opacity_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            self._opacity_anim.setDuration(300)
            self._opacity_anim.setPropertyName('windowOpacity')
            self._opacity_anim.setStartValue(0.0)
            self._opacity_anim.setEndValue(1.0)

            self.setup_ui()

            self._fade_in()

        def get_main_layout(self):
            main_layout = QtWidgets.QVBoxLayout()
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            return main_layout

        def setup_ui(self):
            self.main_layout = self.get_main_layout()
            self.setLayout(self.main_layout)

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


register.register_class('Dialog', AbstractDialog)
