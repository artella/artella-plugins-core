#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC utils functions
"""

from __future__ import print_function, division, absolute_import

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as OpenMayaUI

import artella
from artella.core import qtutils

from artella.externals.Qt import QtWidgets


def force_mel_stack_trace_on():
    """
    Forces enabling Maya Stack Trace
    """

    try:
        mel.eval('stackTrace -state on')
        cmds.optionVar(intValue=('stackTraceIsOn', True))
        what_is = mel.eval('whatIs "$gLastFocusedCommandReporter"')
        if what_is != 'Unknown':
            last_focused_command_reporter = mel.eval('$tmp = $gLastFocusedCommandReporter')
            if last_focused_command_reporter and last_focused_command_reporter != '':
                mel.eval('synchronizeScriptEditorOption 1 $stackTraceMenuItemSuffix')
    except Exception as exc:
        artella.log_debug(str(exc))


def get_maya_window():
    """
    Returns Qt object wrapping main Maya window object

    :return: window object representing Maya Qt main window
    :rtype: QMainWindow
    """

    ptr = OpenMayaUI.MQtUtil.mainWindow()

    return qtutils.wrapinstance(ptr, QtWidgets.QMainWindow)
