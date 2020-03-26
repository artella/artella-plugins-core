#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC utils functions
"""

from __future__ import print_function, division, absolute_import

import maya.cmds as cmds
import maya.mel as mel


def force_mel_stack_trace_on():
    """
    Forces enabling Maya Stack Trace
    """

    mel.eval('stackTrace -state on')
    cmds.optionVar(intValue=('stackTraceIsOn', True))
    what_is = mel.eval('whatIs "$gLastFocusedCommandReporter"')
    if what_is != 'Unknown':
        last_focused_command_reporter = mel.eval('$tmp = $gLastFocusedCommandReporter')
        if last_focused_command_reporter and last_focused_command_reporter != '':
            mel.eval('synchronizeScriptEditorOption 1 $stackTraceMenuItemSuffix')
