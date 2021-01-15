#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive Qt related utils classes and functions
"""

from __future__ import print_function, division, absolute_import

import os

from artella import dcc
from artella.core import utils, qtutils

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtGui


class ResourceTypes(object):
    ICON = 'icon'
    PIXMAP = 'pixmap'
    STYLE = 'style'


_RESOURCES_PATHS = list()
_RESOURCES_CACHE = {
    ResourceTypes.ICON: dict(), ResourceTypes.PIXMAP: dict(), ResourceTypes.STYLE: dict()
}


def register_resources_path(resources_path):
    """
    Registers a path where resources will be searched
    :param str resources_path: Path to search resources in
    """

    if not resources_path or not os.path.isdir(resources_path):
        return

    resources_path = utils.clean_path(resources_path)
    if resources_path in _RESOURCES_PATHS:
        return

    _RESOURCES_PATHS.append(resources_path)

    dcc.register_dcc_resource_path(resources_path)
    icons_path = os.path.join(resources_path, 'icons')
    if os.path.isdir(icons_path):
        dcc.register_dcc_resource_path(icons_path)


def get(resource_type, name, extension, **kwargs):
    """
    Internal function that returns a resource based on its type
    :param resource_type:
    :return: object
    """

    color = kwargs.get('color', '')
    file_name = '{}{}'.format(name, extension)
    file_key = '{}{}'.format(file_name.lower(), color)

    if not qtutils.QT_AVAILABLE or not _RESOURCES_PATHS or resource_type not in _RESOURCES_CACHE:
        return None

    if not extension.startswith('.'):
        extension = '.{}'.format(extension)

    if file_key in _RESOURCES_CACHE[resource_type]:
        return _RESOURCES_CACHE[resource_type][file_key]

    for resource_path in _RESOURCES_PATHS:
        for root, dirs, files in os.walk(resource_path):
            for path in files:
                path_name, path_ext = os.path.splitext(path)
                if path_name == name and path_ext == extension:
                    res_path = os.path.join(root, path)
                    new_res = None
                    if resource_type == ResourceTypes.ICON:
                        new_res = qtutils.icon(res_path, color=color)
                    elif resource_type == ResourceTypes.PIXMAP:
                        new_res = qtutils.pixmap(res_path, color=color)
                    elif resource_type == ResourceTypes.STYLE:
                        new_res = qtutils.style(res_path)
                    if not new_res:
                        return None

                    if hasattr(new_res, 'isNull'):
                        if not new_res.isNull():
                            _RESOURCES_CACHE[resource_type][file_key] = new_res
                    else:
                        _RESOURCES_CACHE[resource_type][file_key] = new_res

                    return new_res

    return None


def icon(name, extension='png', color=None):
    """
    Returns Artella icon
    :param name:
    :param extension:
    :param color:
    :return: QIcon
    """

    new_icon = get(ResourceTypes.ICON, name=name, extension=extension, color=color)
    if not new_icon:
        return None if not qtutils.QT_AVAILABLE else QtGui.QIcon()

    return new_icon


def pixmap(name, extension='png', color=None):
    """
    Returns Artella pixmap resource
    :param name:
    :param extension:
    :param color:
    :return:
    """

    new_pixmap = get(ResourceTypes.PIXMAP, name=name, extension=extension, color=color)
    if not new_pixmap:
        return None if not qtutils.QT_AVAILABLE else QtGui.QPixmap()

    return new_pixmap


def style(name, extension='css'):
    """
    Returns Artella style resource
    :param name:
    :param extension:
    :return:
    """

    new_style = get(ResourceTypes.STYLE, name=name, extension=extension)
    if not new_style:
        return None

    return new_style
