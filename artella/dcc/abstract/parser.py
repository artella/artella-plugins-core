#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract scene file parser implementation
"""

from __future__ import print_function, division, absolute_import

from artella import register
from artella.core.dcc import reroute
from artella.core.utils import abstract


class AbstractSceneParser(object):
    """
    Class that defines basic scene parser abstract functions
    """

    @abstract
    @reroute
    def parse(self, file_path=None):
        """
        Parses all the contents of the given file path looking for file paths

        :param str or None file_path: Absolute local file path of the DCC file we want to parse. If not given,
            current opened DCC scene file path will be used
        :return:
        """

        pass

    @abstract
    @reroute
    def update_paths(self, file_path=None):
        """
        Converts all file path of the given DCC file to make sure they point to valid Artella file paths

        :param str or None file_path: Absolute local file path of the DCC file we want to parse. If not given,
            current opened DCC scene file path will be used
        :return:
        """

        pass


register.register_class('Parser', AbstractSceneParser)
