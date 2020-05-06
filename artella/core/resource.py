#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive Qt related utils classes and functions
"""

from __future__ import print_function, division, absolute_import

import os

import artella
from artella.core import qtutils


def get_resources_path():
    """
    Returns path where Artella resources are located

    :return: Path where Artella resources are located
    :rtype: str
    """

    return os.path.join(os.path.dirname(os.path.abspath(artella.__file__)), 'resources')


def icon(name, extension='png'):
    """
    Returns Artella icon
    :return: QIcon
    """

    extension = extension if extension else 'png'
    if not extension.startswith('.'):
        extension = '.{}'.format(extension)

    resources_path = get_resources_path()
    icon_path = os.path.join(resources_path, 'icons', '{}{}'.format(name, extension))

    return qtutils.icon(icon_path)
