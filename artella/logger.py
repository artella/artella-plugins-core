#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logger module for Artella
"""

from __future__ import print_function, division, absolute_import

import os
import logging.config

artella_logger = None


def create_logger():

    global artella_logger
    if artella_logger:
        return artella_logger

    logger_path = os.path.normpath(os.path.join(os.path.expanduser('~'), 'artella', 'logs'))
    if not os.path.isdir(logger_path):
        os.makedirs(logger_path)

    logging.config.fileConfig(
        os.path.normpath(os.path.join(os.path.dirname(__file__), 'logging.ini')), disable_existing_loggers=False)
    artella_logger = logging.getLogger('artella')

    return artella_logger


def log_debug(msg):
    """
    Uses Artella logger to log a debug message

    :param str msg: debug message to log
    """

    artella_logger.debug(msg)


def log_info(msg):
    """
    Uses Artella logger to log an info message

    :param str msg: info message to log
    """

    artella_logger.info(msg)


def log_warning(msg):
    """
    Uses Artella logger to log a warning message

    :param str msg: warning message to log
    """

    artella_logger.warning(msg)


def log_error(msg):
    """
    Uses Artella logger to log a error message

    :param str msg: error message to log
    """

    artella_logger.error(msg)


def log_exception(msg):
    """
    Uses Artella logger to log an exception message

    :param str msg: error message to log
    """

    artella_logger.error(msg, exc_info=True)
