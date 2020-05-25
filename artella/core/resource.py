#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive Qt related utils classes and functions
"""

from __future__ import print_function, division, absolute_import

import os

from artella import register
from artella.core import utils, qtutils

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtGui


class ResourcesManager(object):
    def __init__(self):
        super(ResourcesManager, self).__init__()

        self._resources_paths = list()
        self._resources_cache = {
            'icons': {}, 'pixmaps': {}, 'styles': {}
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

    def icon(self, name, extension='png', color=None):
        """
        Returns Artella icon
        :param name:
        :param extension:
        :param color:
        :return: QIcon
        """

        if not qtutils.QT_AVAILABLE:
            return None

        if not self._resources_paths:
            return QtGui.QIcon()

        extension = extension if extension else 'png'
        if not extension.startswith('.'):
            extension = '.{}'.format(extension)

        file_name = '{}{}'.format(name, extension)
        file_key = '{}{}'.format(file_name.lower(), color or '')
        if file_key in self._resources_cache['icons']:
            return self._resources_cache['icons'][file_key]

        for resource_path in self._resources_paths:
            for root, dirs, files in os.walk(resource_path):
                for path in files:
                    path_name, path_ext = os.path.splitext(path)
                    if path_name == name and path_ext == extension:
                        icon_path = os.path.join(root, path)
                        new_icon = qtutils.icon(icon_path, color=color)
                        if not new_icon.isNull():
                            self._resources_cache['icons'][file_key] = new_icon
                        return new_icon

    def pixmap(self, name, extension='png', color=None):
        """
        Returns Artella pixmap resource
        :param name:
        :param extension:
        :param color:
        :return:
        """

        if not qtutils.QT_AVAILABLE:
            return None

        if not self._resources_paths:
            return QtGui.QPixmap()

        extension = extension if extension else 'png'
        if not extension.startswith('.'):
            extension = '.{}'.format(extension)

        file_name = '{}{}'.format(name, extension)
        file_key = '{}{}'.format(file_name.lower(), color or '')
        if file_key in self._resources_cache['pixmaps']:
            return self._resources_cache['pixmaps'][file_key]

        for resource_path in self._resources_paths:
            for root, dirs, files in os.walk(resource_path):
                for path in files:
                    path_name, path_ext = os.path.splitext(path)
                    if path_name == name and path_ext == extension:
                        pixmap_path = os.path.join(root, path)
                        new_pixmap = qtutils.pixmap(pixmap_path, color=color)
                        if not new_pixmap.isNull():
                            self._resources_cache['pixmaps'][file_key] = new_pixmap
                        return new_pixmap

    def style(self, name, extension='css'):
        """
        Returns Artella style resource
        :param name:
        :param extension:
        :return:
        """

        if not qtutils.QT_AVAILABLE:
            return None

        if not self._resources_paths:
            return None

        extension = extension if extension else 'css'
        if not extension.startswith('.'):
            extension = '.{}'.format(extension)

        file_name = '{}{}'.format(name, extension)
        if file_name in self._resources_cache['styles']:
            return self._resources_cache['styles'][file_name]

        for resource_path in self._resources_paths:
            for root, dirs, files in os.walk(resource_path):
                for path in files:
                    path_name, path_ext = os.path.splitext(path)
                    if path_name == name and path_ext == extension:
                        style_path = os.path.join(root, path)
                        new_style = qtutils.style(style_path)
                        if new_style:
                            self._resources_cache['styles'][file_name] = new_style
                        return new_style


@utils.Singleton
class ArtellaResourcesManagerSingleton(ResourcesManager, object):
    def __init__(self):
        ResourcesManager.__init__(self)


register.register_class('ResourcesMgr', ArtellaResourcesManagerSingleton)
