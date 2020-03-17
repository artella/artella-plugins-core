#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive utils classes and functions
"""

from __future__ import print_function, division, absolute_import


def force_list(var):
    """
    Returns given variable as a list
    :param object var: variable we want to convert into a list
    :return: Adds given variable into a list if the variable is not already a list. If the variable is None, an empty
        list is returned. If the variable is a tuple, the tuple is converted into a list
    :rtype: list(object)
    """

    if var is None:
        return list()

    if type(var) is not list:
        if type(var) in [tuple]:
            var = list(var)
        else:
            var = [var]

    return var
