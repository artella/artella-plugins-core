#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive Qt related utils classes and functions
"""

from __future__ import print_function, division, absolute_import

import os

import artella.dcc as dcc
from artella import register
from artella.core import utils, qtutils

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtGui


class ResourcesManager(object):
    def __init__(self):
        super(ResourcesManager, self).__init__()

        self._resources_paths = list()
        self._resources_cache = {
            'icon': {}, 'pixmap': {}, 'style': {}
        }

    def register_resources_path(self, resources_path):
        """
        Registers a path where resources will be searched
        :param str resources_path: Path to search resources in
        """

        if not resources_path or not os.path.isdir(resources_path):
            return

        resources_path = utils.clean_path(resources_path)
        if resources_path in self._resources_paths:
            return

        self._resources_paths.append(resources_path)

        dcc.register_dcc_resource_path(resources_path)
        icons_path = os.path.join(resources_path, 'icons')
        if os.path.isdir(icons_path):
            dcc.register_dcc_resource_path(icons_path)

    def icon(self, name, extension='png', color=None):
        """
        Returns Artella icon
        :param name:
        :param extension:
        :param color:
        :return: QIcon
        """

        resource_type = 'icon'

        new_icon, resource_key = self._get_resource(resource_type, name=name, extension=extension, color=color)
        if not new_icon:
            return None if not qtutils.QT_AVAILABLE else QtGui.QIcon()

        if not new_icon.isNull():
            self._register_resource(resource_type, resource_key, new_icon)

        return new_icon

    def pixmap(self, name, extension='png', color=None):
        """
        Returns Artella pixmap resource
        :param name:
        :param extension:
        :param color:
        :return:
        """

        resource_type = 'pixmap'

        new_pixmap, resource_key = self._get_resource(resource_type, name=name, extension=extension, color=color)
        if not new_pixmap:
            return None if not qtutils.QT_AVAILABLE else QtGui.QPixmap()

        if not new_pixmap.isNull():
            self._register_resource(resource_type, resource_key, new_pixmap)

        return new_pixmap

    def style(self, name, extension='css'):
        """
        Returns Artella style resource
        :param name:
        :param extension:
        :return:
        """

        resource_type = 'style'

        new_style, resource_key = self._get_resource('style', name=name, extension=extension)
        if not new_style:
            return None

        self._register_resource(resource_type, resource_key, new_style)

        return new_style

    def _get_resource(self, resource_type, name, extension, **kwargs):
        """
        Internal function that returns a resource based on its type
        :param resource_type:
        :return: object
        """

        color = kwargs.get('color', '')
        file_name = '{}{}'.format(name, extension)
        file_key = '{}{}'.format(file_name.lower(), color)

        if not qtutils.QT_AVAILABLE or not self._resources_paths or resource_type not in self._resources_cache:
            return None, file_key

        if not extension.startswith('.'):
            extension = '.{}'.format(extension)

        if file_key in self._resources_cache[resource_type]:
            return self._resources_cache[resource_type][file_key], file_key

        for resource_path in self._resources_paths:
            for root, dirs, files in os.walk(resource_path):
                for path in files:
                    path_name, path_ext = os.path.splitext(path)
                    if path_name == name and path_ext == extension:
                        res_path = os.path.join(root, path)
                        new_res = getattr(self, '_{}'.format(resource_type))(res_path, color=color)
                        return new_res, file_key

        return None, file_key

    def _register_resource(self, resource_type, resource_key, resource):
        """
        Internal function used to register resources in its proper cache
        :param resource_type: str
        :param resource_key: str
        :param resource: object
        :return:
        """

        if resource_type not in self._resources_cache:
            return

        self._resources_cache[resource_type][resource_key] = resource

    def _icon(self, icon_path, color=None, **kwargs):
        """
        Internal function returns an Artella icon resource
        :param icon_path:
        :param color:
        :return: QIcon
        """

        new_icon = qtutils.icon(icon_path, color=color)

        return new_icon

    def _pixmap(self, pixmap_path, color=None, **kwargs):
        """
        Internal function returns an Artella pixmap resource
        :param file_key: str
        :param pixmap_path: str
        :param color:
        :return:
        """

        new_pixmap = qtutils.pixmap(pixmap_path, color=color)

        return new_pixmap

    def _style(self, style_path, **kwargs):
        """
        Internal function returns an Artella style resource
        :param style_path: str
        :return:
        """

        new_style = qtutils.style(style_path)

        return new_style


@utils.Singleton
class ArtellaResourcesManagerSingleton(ResourcesManager, object):
    def __init__(self):
        ResourcesManager.__init__(self)


register.register_class('ResourcesMgr', ArtellaResourcesManagerSingleton)
