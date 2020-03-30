#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for 3ds Max Python API import
"""

from __future__ import print_function, division, absolute_import

# Do not remove
import MaxPlus

# We force import of some modules to make sure that Maya Callback class is properly registered
from . import plugin
from . import callback
