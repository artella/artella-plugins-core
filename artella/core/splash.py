#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella Splash widget
"""

from __future__ import print_function, division, absolute_import

import logging

import artella
from artella.core import qtutils, utils

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets, QtGui

logger = logging.getLogger('artella')


if not qtutils.QT_AVAILABLE:
    class SplashScreen(object):
        def __init__(self, *args, **kwargs):
            pass

    class ProgressCricle(object):
        def __init__(self, *args, **kwargs):
            pass
else:
    class SplashScreen(QtWidgets.QSplashScreen, object):
        def __init__(self, *args, **kwargs):
            super(SplashScreen, self).__init__(*args, **kwargs)

        def mousePressEvent(self, event):
            pass

    class ProgressCricle(QtWidgets.QProgressBar, object):
        def __init__(self, parent=None, **kwargs):
            super(ProgressCricle, self).__init__(parent)

            self._main_layout = QtWidgets.QHBoxLayout()
            self._default_label = QtWidgets.QLabel()
            self._default_label.setAlignment(QtCore.Qt.AlignCenter)
            self._main_layout.addWidget(self._default_label)
            self.setLayout(self._main_layout)
            self._color = QtGui.QColor(221, 235, 230)
            self._width = kwargs.get('width', 140)

            self.setTextDirection(self.Direction.BottomToTop)

            self._start_angle = 90 * 16
            self._max_delta_angle = 360 * 16
            self._height_factor = 1.0
            self._width_factor = 1.0

            self.setFixedSize(QtCore.QSize(self._width * self._width_factor, self._width * self._height_factor))

        def set_widget(self, widget):
            self.setTextVisible(False)
            self._main_layout.addWidget(widget)

        def paintEvent(self, event):
            if self.text() != self._default_label.text():
                self._default_label.setText(self.text())
            if self.isTextVisible() != self._default_label.isVisible():
                self._default_label.setVisible(self.isTextVisible())

            percent = utils.get_percent(self.value(), self.minimum(), self.maximum())
            total_width = self._width
            pen_width = int(3 * total_width / 50.0)
            radius = total_width - pen_width - 1

            painter = QtGui.QPainter(self)
            painter.setRenderHints(QtGui.QPainter.Antialiasing)

            # draw background circle
            pen_background = QtGui.QPen()
            pen_background.setWidth(pen_width)
            pen_background.setColor(QtGui.QColor(80, 120, 110))
            pen_background.setCapStyle(QtCore.Qt.RoundCap)
            painter.setPen(pen_background)
            painter.drawArc(pen_width / 2.0 + 1,
                            pen_width / 2.0 + 1,
                            radius,
                            radius,
                            self._start_angle,
                            -self._max_delta_angle)

            # draw foreground circle
            pen_foreground = QtGui.QPen()
            pen_foreground.setWidth(pen_width)
            pen_foreground.setColor(self._color)
            pen_foreground.setCapStyle(QtCore.Qt.RoundCap)
            painter.setPen(pen_foreground)
            painter.drawArc(
                pen_width / 2.0 + 1, pen_width / 2.0 + 1, radius, radius,
                self._start_angle, -percent * 0.01 * self._max_delta_angle)
            painter.end()


class SplashDialog(artella.Dialog, object):
    def __init__(self, parent=None, **kwargs):
        super(SplashDialog, self).__init__(parent, use_artella_header=False, **kwargs)

    def get_main_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        return main_layout

    def setup_ui(self):
        super(SplashDialog, self).setup_ui()

        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WA_DeleteOnClose)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        splash_pixmap = artella.ResourcesMgr().pixmap('artella_splash')
        splash = SplashScreen(splash_pixmap)
        splash.setMask(splash_pixmap.mask())
        self._splash_layout = QtWidgets.QVBoxLayout()
        self._splash_layout.setAlignment(QtCore.Qt.AlignBottom)
        splash.setLayout(self._splash_layout)
        self.main_layout.addWidget(splash)

        size_width = splash_pixmap.size().width() + 20
        size_height = splash_pixmap.size().height() + 20
        self.setFixedSize(QtCore.QSize(size_width, size_height))

        shadow_effect = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow_effect.setBlurRadius(qtutils.dpi_scale(15))
        shadow_effect.setColor(QtGui.QColor(0, 0, 0, 150))
        shadow_effect.setOffset(qtutils.dpi_scale(0))
        self.setGraphicsEffect(shadow_effect)


class InfoSplashDialog(SplashDialog, object):
    def __init__(self, parent=None, **kwargs):
        super(InfoSplashDialog, self).__init__(parent, **kwargs)

    def setup_ui(self):
        super(InfoSplashDialog, self).setup_ui()

        self._progress_text = QtWidgets.QLabel('Wait please ...')
        progress_text_layout = QtWidgets.QHBoxLayout()
        progress_text_layout.addStretch()
        progress_text_layout.addWidget(self._progress_text)
        progress_text_layout.addStretch()

        self._splash_layout.addLayout(progress_text_layout)

    def set_text(self, text):
        self._progress_text.setText(text)


class ProgressSplashDialog(SplashDialog, object):
    def __init__(self, parent=None, **kwargs):

        self._is_cancelled = False

        super(ProgressSplashDialog, self).__init__(parent, **kwargs)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self._is_cancelled = True
        super(ProgressSplashDialog, self).keyPressEvent(event)

    def setup_ui(self):
        super(ProgressSplashDialog, self).setup_ui()

        self._progress = ProgressCricle()
        progress_lyt = QtWidgets.QHBoxLayout()
        progress_lyt.addStretch()
        progress_lyt.addWidget(self._progress)
        progress_lyt.addStretch()

        self._progress_text = QtWidgets.QLabel('Wait please ...')
        progress_txt_lyt = QtWidgets.QHBoxLayout()
        progress_txt_lyt.addStretch()
        progress_txt_lyt.addWidget(self._progress_text)
        progress_txt_lyt.addStretch()

        self._splash_layout.addLayout(progress_lyt)
        self._splash_layout.addLayout(progress_txt_lyt)

    def set_progress_text(self, text):
        self._progress.setFormat(text)

    def start(self):

        from artella import dcc

        self._progress.setValue(0)
        self._progress_text.setText('')

        if dcc.is_batch():
            self._log_progress()
            return

        self.show()

    def end(self):
        from artella import dcc

        self._log_progress()

        if dcc.is_batch():
            return

        self.fade_close()

    def get_max_progress_value(self):
        return self._progress.maximum()

    def set_max_progress_value(self, max_value):
        self._progress.setMaximum(max_value)

    def get_progress_value(self):
        return self._progress.value()

    def set_progress_value(self, value, status=''):
        self._progress.setValue(value)
        self._progress_text.setText(str(status))

    def is_cancelled(self):
        return self._is_cancelled

    def _log_progress(self):
        """
         Internal function that logs current progress into DCC output window
         """

        logger.debug('{} - {}'.format(self._progress_text.text(), self._progress.value()))
