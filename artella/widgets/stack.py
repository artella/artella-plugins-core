#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains opacity stack widget implementation
"""

from __future__ import print_function, division, absolute_import

from artella.core import qtutils

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets


def stacked_opacity_animation_mixin(cls):
    """
    Decorators for stacked widget
    When stacked widget index changes, show opacity and position animation for current widget
    :param cls:
    :return:
    """

    if not qtutils.is_stackable(cls):
        return cls

    old_init = cls.__init__

    def _new_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        self._prev_index = 0
        self._to_show_pos_anim = QtCore.QPropertyAnimation()
        self._to_show_pos_anim.setDuration(400)
        self._to_show_pos_anim.setPropertyName(b'pos')
        self._to_show_pos_anim.setEndValue(QtCore.QPoint(0, 0))
        self._to_show_pos_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._to_hide_pos_anim = QtCore.QPropertyAnimation()
        self._to_hide_pos_anim.setDuration(400)
        self._to_hide_pos_anim.setPropertyName(b'pos')
        self._to_hide_pos_anim.setEndValue(QtCore.QPoint(0, 0))
        self._to_hide_pos_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        self._opacity_anim = QtCore.QPropertyAnimation()
        self._opacity_anim.setDuration(400)
        self._opacity_anim.setEasingCurve(QtCore.QEasingCurve.InCubic)
        self._opacity_anim.setPropertyName(b'opacity')
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.setTargetObject(self._opacity_effect)
        self._opacity_anim.finished.connect(self._on_disable_opacity)
        self.currentChanged.connect(self._on_play_anim)

    def _on_play_anim(self, index):
        current_widget = self.widget(index)
        if self._prev_index < index:
            self._to_show_pos_anim.setStartValue(QtCore.QPoint(self.width(), 0))
            self._to_show_pos_anim.setTargetObject(current_widget)
            self._to_show_pos_anim.start()
        else:
            self._to_hide_pos_anim.setStartValue(QtCore.QPoint(-self.width(), 0))
            self._to_hide_pos_anim.setTargetObject(current_widget)
            self._to_hide_pos_anim.start()
        current_widget.setGraphicsEffect(self._opacity_effect)
        current_widget.graphicsEffect().setEnabled(True)
        self._opacity_anim.start()
        self._prev_index = index

    def _on_disable_opacity(self):
        self.currentWidget().graphicsEffect().setEnabled(False)

    setattr(cls, '__init__', _new_init)
    setattr(cls, '_on_play_anim', _on_play_anim)
    setattr(cls, '_on_disable_opacity', _on_disable_opacity)

    return cls


if qtutils.QT_AVAILABLE:
    @stacked_opacity_animation_mixin
    class SlidingOpacityStackedWidget(QtWidgets.QStackedWidget, object):
        """
        Custom stack widget that activates opacity animation when current stack index changes
        """

        def __init__(self, parent=None):
            super(SlidingOpacityStackedWidget, self).__init__(parent)
else:
    class SlidingOpacityStackedWidget(object):
        pass
