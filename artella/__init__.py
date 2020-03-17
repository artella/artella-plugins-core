#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import logging
from functools import wraps
from importlib import import_module


# Directory where DCCs implementations are located. New implementations MUST be located in this folder
DCCS_DIR = os.path.join(os.path.dirname(__file__), 'dcc')

# Cached list of available dccs. This listed is cached in import time because we assume that no new DCCs
# implementations will be added in runtime
DCCS = os.listdir(DCCS_DIR)

# Defines package namespace where Artella DCC plugins are located
ARTELLA_DCC_NAMESPACE = 'artella.dcc'

# Cached active DCC. We use it to avoid repetitive checks. We assume that a DCC environment will not change
# during a session.
CURRENT_DCC = None

# Cached used to store all the reroute paths done during a session. We assume DCC reroutes will not change
# during a session.
DCC_REROUTE_CACHE = dict()


LOGGER = logging.getLogger(__name__)


def _reload():
    """
    Function to be used during development. Can be used to "reload" Artella modules.
    Useful when working inside DCC envs.
    """

    to_clean = list()
    for m in os.sys.modules.keys():
        if 'artella' in m:
            to_clean.append(m)
    for t in to_clean:
        os.sys.modules.pop(t)


def dccs():
    """
    Returns a list with all supported DCCs

    :return: List with the names of all supported DCCs
    :rtype: list(str)
    """

    return [dcc for dcc in DCCS if dcc != 'abstract']


def current_dcc():
    """
    Returns the DCC loaded in current session for current environment
    If the current DCC is not already cached it will be automatically detected taking into account available DCC
    implementations. Otherwise, cached DCC is returned.

    :return: Name of the current used DCC
    :rtype: str
    """

    # If active DCC is already cache, we use it
    global CURRENT_DCC
    if CURRENT_DCC:
        return CURRENT_DCC

    # Loop through all available DCCs and check which one is available in current session
    for dcc_name in dccs():
        dcc_module_name = '{}.{}'.format(ARTELLA_DCC_NAMESPACE, dcc_name)
        try:
            import_module(dcc_module_name)
            CURRENT_DCC = dcc_name
            return CURRENT_DCC
        except Exception as exc:
            continue


def reroute(fn):
    """
    Decorator that reroutes the function call on runtime to the specific DCC implementation of the function
    Rerouted function calls are cached, and are only loaded once.
    The used DCC API will be retrieved from the current session, taking into account the current available
    implementations

    :param fn:
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):

        global DCC_REROUTE_CACHE

        dcc = current_dcc()

        # From the current function and DCC we retrieve module path where DCC implementation should be located
        fn_split = fn.__module__.split('.')
        dcc_reroute_path = '{}.{}.{}'.format(ARTELLA_DCC_NAMESPACE, dcc, '.'.join(fn_split[3:]))
        dcc_reroute_fn_path = '{}.{}'.format(dcc_reroute_path, fn.__name__)
        if dcc_reroute_fn_path not in DCC_REROUTE_CACHE:
            try:
                dcc_reroute_module = import_module(dcc_reroute_path)
            except ImportError:
                raise NotImplementedError('{} | Function {} not implemented!'.format(dcc, dcc_reroute_fn_path))
            except Exception as exc:
                raise exc

            # Cache reroute call, next calls to that function will use cache data
            dcc_reroute_fn = getattr(dcc_reroute_module, fn.__name__)
            DCC_REROUTE_CACHE[dcc_reroute_fn_path] = dcc_reroute_fn

        return DCC_REROUTE_CACHE[dcc_reroute_fn_path](*args, **kwargs)

    return wrapper
