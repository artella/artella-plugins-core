#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella label widgets
"""

from __future__ import print_function, division, absolute_import

from artella.core import qtutils

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets


class ArtellaLabelTypes(object):
    SECONDARY = 'secondary'
    WARNING = 'warning'
    DANGER = 'danger'
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4


if not qtutils.QT_AVAILABLE:
    class ArtellaLabel(object):
        def __init__(self, *args, **kwargs):
            pass
else:

    class ArtellaLabel(QtWidgets.QLabel, object):
        def __init__(self, text='', parent=None):
            super(ArtellaLabel, self).__init__(text, parent)

            self._actual_text = text
            self._artella_type = ''
            self._artella_underline = False
            self._artella_mark = False
            self._artella_delete = False
            self._artella_strong = False
            self._artella_code = False
            self._artella_level = 0
            self._elide_mode = QtCore.Qt.ElideNone
            self.setProperty('artella_text', text)

            self.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction | QtCore.Qt.LinksAccessibleByMouse)
            self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)

        def get_artella_level(self):
            return self._artella_level

        def set_artella_level(self, value):
            self._artella_level = value
            self.style().polish(self)

        def set_artella_underline(self, value):
            self._artella_underline = value
            self.style().polish(self)

        def get_artella_underline(self):
            return self._artella_underline

        def set_artella_delete(self, value):
            self._artella_delete = value
            self.style().polish(self)

        def get_artella_delete(self):
            return self._artella_delete

        def set_artella_strong(self, value):
            self._artella_strong = value
            self.style().polish(self)

        def get_artella_strong(self):
            return self._artella_strong

        def set_artella_mark(self, value):
            self._artella_mark = value
            self.style().polish(self)

        def get_artella_mark(self):
            return self._artella_mark

        def set_artella_code(self, value):
            self._artella_code = value
            self.style().polish(self)

        def get_artella_code(self):
            return self._artella_code

        def get_elide_mode(self):
            return self._elide_mode

        def set_elide_mode(self, value):
            self._elide_mode = value
            self._update_elided_text()

        def get_artella_type(self):
            return self._artella_type

        def set_artella_type(self, value):
            self._artella_type = value
            self.style().polish(self)

        artella_level = QtCore.Property(int, get_artella_level, set_artella_level)
        artella_type = QtCore.Property(str, get_artella_type, set_artella_type)
        artella_underline = QtCore.Property(bool, get_artella_underline, set_artella_underline)
        artella_delete = QtCore.Property(bool, get_artella_delete, set_artella_delete)
        artella_strong = QtCore.Property(bool, get_artella_strong, set_artella_strong)
        artella_mark = QtCore.Property(bool, get_artella_mark, set_artella_mark)
        artella_code = QtCore.Property(bool, get_artella_code, set_artella_code)
        artella_elide_mod = QtCore.Property(QtCore.Qt.TextElideMode, get_artella_code, set_artella_code)

        def minimumSizeHint(self):
            return QtCore.QSize(1, self.fontMetrics().height())

        def text(self):
            return self._actual_text

        def setText(self, text):
            self._actual_text = text
            self._update_elided_text()
            self.setToolTip(text)

        def _update_elided_text(self):
            _font_metrics = self.fontMetrics()
            _elided_text = _font_metrics.elidedText(self._actual_text, self._elide_mode,
                                                    self.width() - 2 * 2)
            super(ArtellaLabel, self).setText(_elided_text)

        def resizeEvent(self, event):
            self._update_elided_text()

        def h1(self):
            self.set_artella_level(ArtellaLabelTypes.H1)
            return self

        def h2(self):
            self.set_artella_level(ArtellaLabelTypes.H2)
            return self

        def h3(self):
            self.set_artella_level(ArtellaLabelTypes.H3)
            return self

        def h4(self):
            self.set_artella_level(ArtellaLabelTypes.H4)
            return self

        def secondary(self):
            self.set_artella_type(ArtellaLabelTypes.SECONDARY)
            return self

        def warning(self):
            self.set_artella_type(ArtellaLabelTypes.WARNING)
            return self

        def danger(self):
            self.set_artella_type(ArtellaLabel.DangerType)
            return self

        def strong(self):
            """Set QLabel with strong style."""
            self.set_artella_strong(True)
            return self

        def mark(self):
            self.set_artella_mark(True)
            return self

        def code(self):
            self.set_artella_code(True)
            return self

        def delete(self):
            self.set_artella_delete(True)
            return self

        def underline(self):
            self.set_artella_underline(True)
            return self

        # def event(self, event):
        #     if event.type() == QEvent.DynamicPropertyChange and event.propertyName() == 'artella_text':
        #         self.setText(self.property('artella_text'))
        #     return super(MLabel, self).event(event)
