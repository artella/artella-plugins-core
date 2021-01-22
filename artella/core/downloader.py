#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains download manager widget for Artella
"""

from __future__ import print_function, division, absolute_import

from artella import dcc
from artella.core import utils


class _MetaDownloader(type):
    def __call__(cls, *args, **kwargs):
        if dcc.is_maya():
            from artella.dccs.maya import downloader
            _DCC_PLUGIN = type.__call__(downloader.MayaDownloader, *args, **kwargs)
        else:
            _DCC_PLUGIN = type.__call__(BaseDownloader, *args, **kwargs)

        return _DCC_PLUGIN


class AbstractDownloader(object):

    @utils.abstract
    def download(self, file_paths, show_dialogs=True):
        pass


class BaseDownloader(AbstractDownloader):

    def download(self, file_paths, show_dialogs=True):
        pass


@utils.add_metaclass(_MetaDownloader)
class Downloader(AbstractDownloader):
    pass
