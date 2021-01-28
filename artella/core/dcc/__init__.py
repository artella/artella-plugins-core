#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains dcc module initialization
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import logging
from functools import wraps
from importlib import import_module

from artella.core import consts, utils

logger = logging.getLogger('artella')

# Directories where DCCs implementations are located.
DCCS_DIRS = list()

# Cached dict of available dcc. This listed is cached in import time because we assume that no new DCCs
# implementations will be added in runtime
DCCS = dict()

# Cached active DCC. We use it to avoid repetitive checks. We assume that a DCC environment will not change
# during a session.
CURRENT_DCC = None

# Cached active DCC module name.
CURRENT_DCC_MODULE = None

# Cached used to store all the reroute paths done during a session. We assume DCC reroutes will not change
# during a session.
DCC_REROUTE_CACHE = dict()


def dccs():
    """
    Returns a list with all supported DCCs

    :return: List with the names of all supported DCCs
    :rtype: list(str)
    """

    return DCCS.keys()


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
    global CURRENT_DCC_MODULE
    if CURRENT_DCC:
        return CURRENT_DCC

    # If DCC is not available we make sure that we check all available dirs where DCC implementation can be located
    global DCCS_DIRS
    global DCCS
    dcc_paths_str = os.environ.get(consts.AED, '')
    if dcc_paths_str:
        dcc_paths_split = [utils.clean_path(pth) for pth in dcc_paths_str.split(';')]
        for dcc_path in dcc_paths_split:
            if not dcc_path or not os.path.isdir(dcc_path) or dcc_path in DCCS_DIRS:
                continue
            DCCS_DIRS.append(dcc_path)
    if DCCS_DIRS:
        for dcc_dir in DCCS_DIRS:
            for dcc_folder in os.listdir(dcc_dir):
                if not dcc_folder.startswith('__') and not dcc_folder.endswith('__') and dcc_folder != 'abstract':
                    DCCS[dcc_folder] = utils.clean_path(os.path.join(dcc_dir, dcc_folder))
                    if DCCS[dcc_folder] not in sys.path:
                        sys.path.append(DCCS[dcc_folder])

    # Loop through all available DCCs and check which one is available in current session
    for dcc_name, dcc_dir in DCCS.items():
        dcc_namespace_split = dcc_name.split('-')
        dcc_names = [dcc_name, dcc_namespace_split[-1]] if dcc_namespace_split else [dcc_name]
        for dcc in dcc_names:
            if dcc.startswith('artella'):
                continue
            try:
                dcc_module_name = '{}.{}'.format(consts.ARTELLA_DCCS_NAMESPACE, dcc)
                import_module(dcc_module_name)
                CURRENT_DCC = dcc
                CURRENT_DCC_MODULE = dcc_module_name
                logger.info('Current DCC: {}'.format(CURRENT_DCC))
                return CURRENT_DCC
            except ImportError as exc:
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
        if not dcc:
            return None

        # From the current function and DCC we retrieve module path where DCC implementation should be located
        fn_split = fn.__module__.split('.')
        dcc_reroute_path = '{}.{}.{}'.format(consts.ARTELLA_DCCS_NAMESPACE, dcc, fn_split[-1])
        dcc_reroute_fn_path = '{}.{}'.format(dcc_reroute_path, fn.__name__)
        if dcc_reroute_fn_path not in DCC_REROUTE_CACHE:
            try:
                dcc_reroute_module = import_module(dcc_reroute_path)
            except ImportError as exc:
                raise NotImplementedError(
                    '{} | Function {} not implemented! {}'.format(dcc, dcc_reroute_fn_path, exc))
            except Exception as exc:
                raise exc

            # Cache reroute call, next calls to that function will use cache data
            dcc_reroute_fn = getattr(dcc_reroute_module, fn.__name__)
            DCC_REROUTE_CACHE[dcc_reroute_fn_path] = dcc_reroute_fn

        return DCC_REROUTE_CACHE[dcc_reroute_fn_path](*args, **kwargs)

    return wrapper


def callbacks():
    """
    Returns a list of callbacks based on DCC available callbacks
    :return: List of available DCC callbacks
    :rtype: list
    """

    callbacks_list = list()
    for k, v in DccCallbacks.__dict__.items():
        if k.startswith('__') or k.endswith('__'):
            continue
        callbacks_list.append(v[0])

    return callbacks_list


class DccCallbacks(object):
    """
    Class that contains all callbacks that can be supported by DCCs
    """

    Shutdown = ('Shutdown', {'type': 'simple'})
    BeforeOpenCheck = ('BeforeOpenCheck', {'type': 'simple'})
    AfterOpen = ('AfterOpen', {'type': 'simple'})
    SceneBeforeSave = ('SceneBeforeSave', {'type': 'simple'})
    SceneCreated = ('SceneCreated', {'type': 'simple'})
    AfterLoadReference = ('AfterLoadReference', {'type': 'simple'})
    BeforeCreateReferenceCheck = ('BeforeCreateReferenceCheck', {'type': 'simple'})
