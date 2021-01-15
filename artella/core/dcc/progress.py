#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC abstract progress bar implementation
"""

from __future__ import print_function, division, absolute_import

from artella import dcc
from artella.core.utils import abstract, add_metaclass


class _MetaProgressBar(type):

    def __call__(cls, *args, **kwargs):
        if dcc.is_maya():
            from artella.dccs.maya import progress as maya_progress
            return type.__call__(maya_progress.MayaProgressBar, *args, **kwargs)
        else:
            return type.__call__(AbstractProgressBar, *args, **kwargs)


class AbstractProgressBar(object):
    """
    Class that defines basic progress bar abstract functions
    """

    @abstract
    def can_be_interrupted(self):
        """
        Returns whether or not DCC progress bar can be interrupted or not
        :return: True if the progress bar can be interrupted by the user; False otherwise.
        :rtype: bool
        """

        pass

    @abstract
    def is_cancelled(self):
        """
        Returns whether or not DCC progress bar has been cancelled by the user

        :return: True if the progres bar has been cancelled by the user; False otherwise.
        :rtype: bool
        """

        pass

    @abstract
    def get_max_progress_value(self):
        """
        Returns the maximum value of the progress bar

        :return: Maximum value progress bar can accept
        :rtype: int
        """

        pass

    def get_min_progress_value(self):
        """
        Returns the minimum value of the progress bar

        :return: Minimum value progress bar can accept
        :rtype: int
        """

        pass

    @abstract
    def set_min_progress_value(self, min_value):
        """
        Sets the minimum value of the progress bar

        :param int min_value: Minimum value progress bar can accept
        """

        pass

    def set_max_progress_value(self, max_value):
        """
        Sets the maximum value of the progress bar

        :param int max_value: Maximum value progress bar can accept
        """

        pass

    @abstract
    def get_progress_value(self):
        """
        Returns current progress value of the progress bar

        :return: current progress value
        :rtype: int
        """

        pass

    @abstract
    def set_progress_value(self, value):
        """
        Sets the current progress value of the progress bar

        :param int value: current progress value
        """

        pass

    @abstract
    def increment_value(self, increment=1):
        """
        Increments current progress value with the given increment

        :param int increment: Increment step we want to apply to current progress bar value
        """

        pass

    @abstract
    def get_status(self):
        """
        Returns current status text of the progress bar

        :return: status text of the progress bar
        :rtype: str
        """

        pass

    @abstract
    def set_status(self, status_text):
        """
        Sets current status text of the progress bar

        :param str status_text: text used by progress bar
        """

        pass

    @abstract
    def start(self, title='', status='', min_count=0, max_count=100):
        """
        Starts progress bar execution
        :param str title: Title of the progress bar (optional)
        :param str status: Initial text used by progress bar (optional)
        :param int min_count: Initial minimum progress bar value (optional)
        :param int max_count: Initial maximum progress bar value (optional)
        """

        pass

    @abstract
    def end(self):
        """
        Ends progress bar execution
        """

        pass


class BaseProgressBar(object):
    def can_be_interrupted(self):
        return False

    def is_cancelled(self):
        return True

    @abstract
    def get_max_progress_value(self):
        return 100

    def get_min_progress_value(self):
        return 0

    @abstract
    def set_min_progress_value(self, min_value):
        pass

    def set_max_progress_value(self, max_value):
        pass

    def get_progress_value(self):
        pass

    def set_progress_value(self, value):
        pass

    def increment_value(self, increment=1):
        pass

    def get_status(self):
        pass

    def set_status(self, status_text):
        pass

    @abstract
    def start(self, title='', status='', min_count=0, max_count=100):
        pass

    @abstract
    def end(self):
        pass


@add_metaclass(_MetaProgressBar)
class ProgressBar(AbstractProgressBar):
    pass
