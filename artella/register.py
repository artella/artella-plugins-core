#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella register functionality
"""

from __future__ import print_function, division, absolute_import

import artella

# =================================================================================

REGISTER_ATTR = '_registered_classes'

# =================================================================================


def register_class(cls_name, cls, is_unique=True):
    """
    Registers given class in artella module dictionary.

    :param cls_name: str, name of the class we want to register
    :param cls: class, class we want to register
    :param is_unique: bool, Whether if the class should be updated if new class is registered with the same name
    """

    if REGISTER_ATTR not in artella.__dict__:
        artella.__dict__[REGISTER_ATTR] = list()

    if not is_unique and cls_name in artella.__dict__:
        return

    artella.__dict__[cls_name] = cls
    artella.__dict__[REGISTER_ATTR].append(cls_name)


def cleanup():

    if REGISTER_ATTR not in artella.__dict__:
        return

    for cls_name in artella.__dict__[REGISTER_ATTR]:
        if cls_name not in artella.__dict__:
            continue
        del artella.__dict__[cls_name]
    del artella.__dict__[REGISTER_ATTR]
