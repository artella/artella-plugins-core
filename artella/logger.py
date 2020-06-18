#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logger module for Artella
"""

from __future__ import print_function, division, absolute_import

import os
import logging.config


def create_logger():

    logger_path = os.path.normpath(os.path.join(os.path.expanduser('~'), 'artella', 'logs'))
    if not os.path.isdir(logger_path):
        os.makedirs(logger_path)

    logging.config.fileConfig(
        os.path.normpath(os.path.join(os.path.dirname(__file__), 'logging.ini')), disable_existing_loggers=False)

