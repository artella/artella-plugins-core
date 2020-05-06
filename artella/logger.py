#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logger module for Artella
"""

from __future__ import print_function, division, absolute_import

import logging

logging.basicConfig(filename='artella.log', level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')


def log_debug(msg):
    """
    Uses Artella logger to log a debug message

    :param str msg: debug message to log
    """

    logging.debug(msg)


def log_info(msg):
    """
    Uses Artella logger to log an info message

    :param str msg: info message to log
    """

    logging.info(msg)


def log_warning(msg):
    """
    Uses Artella logger to log a warning message

    :param str msg: warning message to log
    """

    logging.warning(msg)


def log_error(msg):
    """
    Uses Artella logger to log a error message

    :param str msg: error message to log
    """

    logging.error(msg)


def log_exception(msg):
    """
    Uses Artella logger to log an exception message

    :param str msg: error message to log
    """

    logging.error(msg, exc_info=True)