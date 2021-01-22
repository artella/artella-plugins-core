#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract scene file parser implementation
"""

from __future__ import print_function, division, absolute_import

from artella import dcc
from artella.core.dcc import reroute
from artella.core.utils import abstract, add_metaclass


class _MetaDccParser(type):

    def __call__(cls, *args, **kwargs):
        if dcc.is_maya():
            from artella.dccs.maya import parser
            return type.__call__(parser.MayaSceneParser, *args, **kwargs)
        else:
            return type.__call__(BaseSceneParser, *args, **kwargs)


class AbstractSceneParser(object):
    """
    Class that defines basic scene parser abstract functions
    """

    @abstract
    @reroute
    def parse(self, file_paths=None):
        """
        Parses all the contents of the given file path looking for file paths

        :param file_paths: list(str) or str or None: Absolute local file path of the DCC file we want to parse.
            If not given, current opened DCC scene file path will be used
        :return:
        """

        pass

    @abstract
    @reroute
    def update_paths(self, file_paths=None):
        """
        Converts all file path of the given DCC file to make sure they point to valid Artella file paths

        :param file_paths: list(str) or str or None: Absolute local file path of the DCC file we want to parse.
            If not given, current opened DCC scene file path will be used
        :return:
        """

        pass


class BaseSceneParser(AbstractSceneParser):
    def parse(self, file_paths=None):
        return list()

    def update_paths(self, file_paths=None):
        return False


@add_metaclass(_MetaDccParser)
class Parser(AbstractSceneParser):
    pass
