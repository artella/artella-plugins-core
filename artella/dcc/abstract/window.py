#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract window implementation
"""

from __future__ import print_function, division, absolute_import

from artella import register
from artella.core import qtutils

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtWidgets

if not qtutils.QT_AVAILABLE:
    class AbstractWindow(object):
        pass
else:
    class AbstractWindow(QtWidgets.QMainWindow):
        def __init__(self, parent=None, **kwargs):

            if not parent:
                from artella import dcc
                parent = dcc.get_main_window()

            super(AbstractWindow, self).__init__(parent, **kwargs)


register.register_class('Window', AbstractWindow)
