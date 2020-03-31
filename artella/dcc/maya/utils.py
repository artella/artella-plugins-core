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


class TrackNodes(object):
    """
    Helps track new nodes that get added to a scene after a function is called

    track_nodes = TrackNodes()
    track_nodes.load()
    fn()
    new_nodes = track_nodes.get_delta()
    """

    def __init__(self, full_path=False):
        self._nodes = None
        self._node_type = None
        self._delta = None
        self._full_path = full_path

    def load(self, node_type=None):
        """
        Initializes TrackNodes states

        :param str node_type: Maya node type we want to track. If not given, all current scene objects wil lbe tracked
        """

        self._node_type = node_type
        if self._node_type:
            self._nodes = cmds.ls(type=node_type, long=self._full_path)
        else:
            self._nodes = cmds.ls()

    def get_delta(self):
        """
        Returns the new nodes in the Maya scene created after load() was executed

        :return: List with all new nodes available in current DCC scene
        :rtype: list(str)
        """

        if self._node_type:
            current_nodes = cmds.ls(type=self._node_type, long=self._full_path)
        else:
            current_nodes = cmds.ls(long=self._full_path)

        new_set = set(current_nodes).difference(self._nodes)

        return list(new_set)
