#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for Houdini Python API import
"""

from __future__ import print_function, division, absolute_import

# Do not remove
import hou

# We force callback import to make sure that Houdini Callback class is properly registered
from . import plugin
from . import callback
