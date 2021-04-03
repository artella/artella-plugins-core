#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella Snackbar widget
"""

from __future__ import print_function, division, absolute_import

from artella import dcc
from artella.core import qtutils, resource
from artella.widgets import image, label, button, divider, theme

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets


class SnackBarTypes(object):
    ARTELLA = 'artella'
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'


if not qtutils.QT_AVAILABLE:
    class SnackBarMessage(object):
        def __init__(self, *args, **kwargs):
            pass
else:
    class SnackBarMessage(QtWidgets.QWidget, object):

        closed = QtCore.Signal()

        DEFAULT_DURATION = 6
        DEFAULT_TOP = 180

        def __init__(self, text='', title='', duration=None, artella_type=None, closable=False, parent=None):

            if parent is None:
                parent = dcc.get_main_window()
            current_type = artella_type or SnackBarTypes.ARTELLA

            super(SnackBarMessage, self).__init__(parent)

            self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog | QtCore.Qt.WA_DeleteOnClose)
            self.setAttribute(QtCore.Qt.WA_StyledBackground)
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

            main_layout = QtWidgets.QVBoxLayout()
            main_layout.setContentsMargins(2, 2, 2, 2)
            main_layout.setSpacing(2)
            self.setLayout(main_layout)

            main_frame = QtWidgets.QFrame()
            main_frame.setObjectName('mainFrame')
            frame_layout = QtWidgets.QVBoxLayout()
            frame_layout.setContentsMargins(5, 5, 5, 5)
            frame_layout.setSpacing(5)

            main_frame.setLayout(frame_layout)
            main_layout.addWidget(main_frame)

            info_layout = QtWidgets.QHBoxLayout()

            artella_label_layout = QtWidgets.QHBoxLayout()
            artella_label = image.ArtellaImage.small()
            artella_label.set_artella_image(resource.pixmap('artella_white'))
            self._close_btn = button.ArtellaToolButton(parent=self).image('close').tiny().icon_only()
            self._close_btn.setVisible(closable or False)
            self._close_btn.clicked.connect(self.close)
            if closable:
                artella_label_layout.addSpacing(20)
            artella_label_layout.addStretch()
            artella_label_layout.addWidget(artella_label)
            artella_label_layout.addStretch()
            artella_label_layout.addWidget(self._close_btn)
            title_layout = QtWidgets.QHBoxLayout()
            self._title_label = label.ArtellaLabel(parent=self).strong()
            self._title_label.setText(title)
            self._title_label.setVisible(bool(text))
            title_layout.addStretch()
            title_layout.addWidget(self._title_label)
            title_layout.addStretch()

            self._icon_label = image.ArtellaImage.small()
            self._icon_label.set_artella_image(
               resource.pixmap('{}'.format(current_type), color=vars(theme.theme()).get(current_type + '_color')))

            self._content_label = label.ArtellaLabel(parent=self)
            self._content_label.setText(text)
            info_layout.addStretch()
            info_layout.addWidget(self._icon_label)
            info_layout.addWidget(self._content_label)
            info_layout.addStretch()

            frame_layout.addLayout(artella_label_layout)
            frame_layout.addWidget(divider.ArtellaDivider())
            frame_layout.addLayout(title_layout)
            frame_layout.addLayout(info_layout)

            self._setup_timers(duration)

            self._on_fade_in()

        @property
        def text(self):
            return self._text

        @text.setter
        def text(self, text):
            self._text = str(text)
            self._label.setText(self._text)
            self.setVisible(bool(self._text))

        @classmethod
        def artella(cls, text, title='', parent=None, duration=None, closable=None):
            inst = cls(text, title=title, artella_type=SnackBarTypes.ARTELLA,
                       duration=duration, closable=closable, parent=parent)
            theme.theme().apply(inst)
            inst.show()

            return inst

        @classmethod
        def info(cls, text, title='', parent=None, duration=None, closable=None):
            inst = cls(text, title=title, artella_type=SnackBarTypes.INFO,
                       duration=duration, closable=closable, parent=parent)
            theme.theme().apply(inst)
            inst.show()

            return inst

        @classmethod
        def success(cls, text, title='', parent=None, duration=None, closable=None):
            inst = cls(text, title=title, artella_type=SnackBarTypes.SUCCESS,
                       duration=duration, closable=closable, parent=parent)
            theme.theme().apply(inst)
            inst.show()

            return inst

        @classmethod
        def warning(cls, text, title='', parent=None, duration=None, closable=None):
            inst = cls(text, title=title, artella_type=SnackBarTypes.WARNING,
                       duration=duration, closable=closable, parent=parent)
            theme.theme().apply(inst)
            inst.show()

            return inst

        @classmethod
        def error(cls, text, title='', parent=None, duration=None, closable=None):
            inst = cls(text, title=title, artella_type=SnackBarTypes.ERROR,
                       duration=duration, closable=closable, parent=parent)
            theme.theme().apply(inst)
            inst.show()

            return inst

        def _setup_timers(self, duration):
            close_timer = QtCore.QTimer(self)
            anim_timer = QtCore.QTimer(self)
            close_timer.setSingleShot(True)
            close_timer.timeout.connect(self.close)
            close_timer.timeout.connect(self.closed.emit)
            anim_timer.timeout.connect(self._on_fade_out)
            close_timer.setInterval((duration or self.DEFAULT_DURATION) * 1000)
            anim_timer.setInterval((duration or self.DEFAULT_DURATION) * 1000 - 300)

            close_timer.start()
            anim_timer.start()

            self._pos_anim = QtCore.QPropertyAnimation(self)
            self._pos_anim.setTargetObject(self)
            self._pos_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            self._pos_anim.setDuration(300)
            self._pos_anim.setPropertyName(b'pos')

            self._opacity_anim = QtCore.QPropertyAnimation(self)
            self._opacity_anim = QtCore.QPropertyAnimation()
            self._opacity_anim.setTargetObject(self)
            self._opacity_anim.setDuration(300)
            self._opacity_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            self._opacity_anim.setPropertyName(b'windowOpacity')
            self._opacity_anim.setStartValue(0.0)
            self._opacity_anim.setEndValue(1.0)

        def resizeEvent(self, event):
            self.updateGeometry()
            self._calculate_position()
            super(SnackBarMessage, self).resizeEvent(event)

        def _calculate_position(self, parent=None):
            """
            Internal function that calculates a proper position for the snack bar relative to its parent
            """

            parent = parent or self.parent()
            parent_geo = parent.geometry()
            pos = parent_geo.topLeft() if parent.parent() is None else parent.mapToGlobal(parent_geo.topLeft())
            offset = 0
            for child in parent.children():
                if isinstance(child, SnackBarMessage) and child.isVisible():
                    offset = max(offset, child.y() + 10 + child.geometry().height() / 2)
            base_pos = pos.y() + SnackBarMessage.DEFAULT_TOP
            target_x = pos.x() + parent_geo.width() / 2 - self.size().width() / 2
            target_y = (offset + 50) if offset else base_pos
            self._pos_anim.setStartValue(QtCore.QPoint(target_x, target_y - 40))
            self._pos_anim.setEndValue(QtCore.QPoint(target_x, target_y))

        def _on_fade_out(self):
            """
            Internal callback function that fades out snack bar widget
            """

            try:
                self._pos_anim.setDirection(QtCore.QAbstractAnimation.Backward)
                self._pos_anim.start()
                self._opacity_anim.setDirection(QtCore.QAbstractAnimation.Backward)
                self._opacity_anim.start()
            except Exception:
                pass

        def _on_fade_in(self):
            """
            Internal callback function that fades in snack bar widget
            """

            try:
                self._pos_anim.start()
                self._opacity_anim.start()
            except Exception:
                pass
