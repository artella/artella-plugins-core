#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for Blender Python API import
"""

from __future__ import print_function, division, absolute_import

# Do not remove
import bpy

# We force callback import to make sure that Blender Callback class is properly registered
from . import plugin
from . import callback
