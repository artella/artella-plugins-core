#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella Splash widget
"""

from __future__ import print_function, division, absolute_import

import os
import logging

from artella import dcc
from artella.core.dcc import dialog
from artella.core import utils, qtutils, resource
from artella.widgets import stack

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

            self._infinite = False
            self._timer = QtCore.QTimer(self)
            self._timer.timeout.connect(self._on_increase_value)

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

        @property
        def infinite(self):
            return self._infinite

        def set_widget(self, widget):
            self.setTextVisible(False)
            self._main_layout.addWidget(widget)

        def set_infinite(self, flag):
            self._timer.stop()
            if flag:
                self._timer.start(15)
            self._infinite = flag

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

        def _on_increase_value(self):
            new_value = self.value() + 1
            if new_value >= self.maximum():
                new_value = 0
            self.setValue(new_value)


class SplashDialog(dialog.Dialog(), object):
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

        splash_pixmap = resource.pixmap('artella_splash')
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
        pass

        # if event.key() == QtCore.Qt.Key_Escape:
        #     self._is_cancelled = True
        # super(ProgressSplashDialog, self).keyPressEvent(event)

    def setup_ui(self):
        super(ProgressSplashDialog, self).setup_ui()

        self._stack = stack.SlidingOpacityStackedWidget(parent=self)
        self._splash_layout.addStretch()
        self._splash_layout.addWidget(self._stack)

        progress_widget = QtWidgets.QWidget(parent=self)
        progress_layout = QtWidgets.QVBoxLayout()
        progress_widget.setLayout(progress_layout)
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
        progress_layout.addStretch()
        progress_layout.addLayout(progress_lyt)
        progress_layout.addLayout(progress_txt_lyt)

        self._stack.addWidget(progress_widget)

    def set_progress_text(self, text):
        self._progress.setFormat(text)

    def set_infinite(self, flag):
        self._progress.set_infinite(flag)
        if flag:
            self.set_progress_text('Please wait ...')

    def start(self, reset=True, infinite=False):

        if dcc.is_batch():
            self._log_progress()
            return

        if reset:
            self._progress.setValue(0)
            self._progress_text.setText('')

        self.set_infinite(infinite)

        self.exec_()

    def end(self):
        self._log_progress()
        self._progress.set_infinite(False)

        if dcc.is_batch():
            return

        self.fade_close()

    def get_min_progress_value(self):
        return self._progress.minimum()

    def get_max_progress_value(self):
        return self._progress.maximum()

    def set_min_progress_value(self, min_value):
        self._progress.setMinimum(min_value)

    def set_max_progress_value(self, max_value):
        self._progress.setMaximum(max_value)

    def get_progress_value(self):
        return self._progress.value()

    def set_progress_value(self, value, status=''):
        if not self._progress.infinite:
            self._progress.setValue(value)
        self._progress_text.setText(str(status))

    def is_cancelled(self):
        return self._is_cancelled

    def _log_progress(self):
        """
         Internal function that logs current progress into DCC output window
         """

        logger.debug('{} - {}'.format(self._progress_text.text(), self._progress.value()))


class DownloadSplashDialog(ProgressSplashDialog, object):
    def __init__(self, downloader, parent=None, **kwargs):
        super(DownloadSplashDialog, self).__init__(parent, **kwargs)

        self._downloader = downloader
        self._file_items = dict()

    def setup_ui(self):
        super(DownloadSplashDialog, self).setup_ui()

        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_widget.setLayout(main_layout)
        self._stack.addWidget(main_widget)

        download_widget = QtWidgets.QWidget()
        download_layout = QtWidgets.QVBoxLayout()
        download_widget.setLayout(download_layout)
        content_area = QtWidgets.QScrollArea(parent=self)
        content_area.setMinimumHeight(qtutils.dpi_scale(150))
        content_area.setWidgetResizable(True)
        content_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # content_area.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        content_area.setWidget(download_widget)
        content_area.setStyleSheet('background-color: transparent; border: none;')
        self._download_layout = QtWidgets.QVBoxLayout()
        download_layout.addLayout(self._download_layout)

        main_layout.addStretch()
        main_layout.addWidget(content_area)

    def download(self, file_paths):
        if dcc.is_batch():
            self._log_progress()
            return

        # qtutils.clear_layout(self._download_layout)
        # self._file_items.clear()
        # for file_path in file_paths:
        #     file_path = utils.clean_path(file_path)
        #     new_download_item = DownloadItemWidget(file_path, parent=self)
        #     new_download_item.setVisible(False)
        #     self._file_items[file_path] = new_download_item
        #     self._download_layout.addWidget(new_download_item)

        self.exec_()

    def update_download(self, file_path, status, progress):

        pass

        # self._stack.setCurrentIndex(1)
        #
        # if not file_path or not self._file_items:
        #     return
        # file_path = utils.clean_path(file_path)
        # if file_path not in self._file_items:
        #     return
        #
        # download_item = self._file_items[file_path]
        # download_item.set_status(status, progress)
        # download_item.setVisible(True)


if qtutils.QT_AVAILABLE:
    class DownloadItemWidget(QtWidgets.QWidget):
        def __init__(self, file_path, parent=None):
            super(DownloadItemWidget, self).__init__(parent)

            download_layout = QtWidgets.QHBoxLayout()
            self.setLayout(download_layout)

            self._path_label = QtWidgets.QLabel(os.path.basename(file_path))
            self._progress_text = QtWidgets.QLabel('Waiting ...')
            self._progress = ProgressCricle(width=qtutils.dpi_scale(35))
            # self._progress.setTextVisible(False)
            download_layout.addWidget(self._progress)
            download_layout.addWidget(self._path_label)
            download_layout.addStretch()
            download_layout.addWidget(self._progress_text)
            download_layout.addStretch()

            self._progress_text.setVisible(False)

        def set_status(self, status, progress=None):
            status = status or ''
            self._progress_text.setText(str(status))
            if progress is not None:
                self._progress.setValue(progress)
