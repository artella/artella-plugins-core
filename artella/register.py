#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella register functionality
"""

from __future__ import print_function, division, absolute_import


def register_class(cls_name, cls, is_unique=False):
    """
    Registers given class in artella module dictionary.

    :param cls_name: str, name of the class we want to register
    :param cls: class, class we want to register
    :param is_unique: bool, Whether if the class should be updated if new class is registered with the same name
    """

    import artella

    if is_unique:
        if cls_name in artella.__dict__:
            setattr(artella.__dict__, cls_name, getattr(artella.__dict__, cls_name))
    else:
        artella.__dict__[cls_name] = cls
