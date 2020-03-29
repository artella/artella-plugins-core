#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive utils classes and functions
"""

from __future__ import print_function, division, absolute_import

import sys
import inspect
from functools import wraps


def is_python2():
    """
    Returns whether or not current version is Python 2
    :return: bool
    """

    return sys.version_info.major == 2


def is_python3():
    """
    Returns whether or not current version is Python 3
    :return: bool
    """

    return sys.version_info.major == 3


def clear_list(list_to_clear):
    """
    Clears given Python list. Works fine for both Python 2 and Python 3.

    :param list_to_clear: list
    """

    if is_python2():
        del list_to_clear[:]
    else:
        list_to_clear.clear()


def force_list(var, remove_duplicates=False):
    """
    Returns given variable as a list

    :param object var: variable we want to convert into a list
    :param bool remove_duplicates: whether or not duplicated element should be removed from output list
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

    if remove_duplicates:
        var = list(set(var))

    return var


def debug_object_string(obj, msg):
    """
    Returns a debug string depending of the type of the object

    :param object obj: Python object
    :param str msg: message to log
    :return: debug string
    :rtype: str
    """

    if inspect.ismodule(obj):
        return '[%s module] :: %s' % (obj.__name__, msg)
    elif inspect.isclass(obj):
        return '[%s.%s class] :: %s' % (obj.__module__, obj.__name__, msg)
    elif inspect.ismethod(obj):
        return '[%s.%s.%s method] :: %s' % (obj.im_class.__module__, obj.im_class.__name__, obj.__name__, msg)
    elif inspect.isfunction(obj):
        return '[%s.%s function] :: %s' % (obj.__module__, obj.__name__, msg)


def abstract(fn):
    """
    Decorator that indicates that decorated function should be override
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        msg = 'DCC Abstract function {} has not been overridden.'.format(fn)
        raise NotImplementedError(debug_object_string(fn, msg))

    return wrapper


class Singleton(object):
    """
    Class that implements Singleton  pattern design as a class decorator in Python
    """

    all_instances = list()

    @staticmethod
    def destroy_all():
        for instance in Singleton.all_instances:
            instance.destroy()

    def __init__(self, cls):
        self.cls = cls
        self.instance = None
        self.all_instances.append(self)

    def destroy(self):
        del self.instance
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.cls(*args, **kwargs)

        return self.instance
