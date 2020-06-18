#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella exceptions
"""

from __future__ import print_function, division, absolute_import

import logging

from artella.core import qtutils

logger = logging.getLogger('artella')


class ArtellaException(Exception):
    def __init__(self, message, title='Artella - Error', *args):

        artella_message = 'Artella >>> {}'.format(message)
        logger.error(artella_message)

        super(ArtellaException, self).__init__(artella_message, *args)

        qtutils.show_error_message_box(title, message)


class ArtellaDriveNotAvailable(ArtellaException):
    def __init__(self):
        super(ArtellaDriveNotAvailable, self).__init__(
            'Local Artella Drive is not available. Please launch Artella Drive App.', 'Artella Drive App not available'
        )


class RemoteSessionsNotAvailable(ArtellaException):
    def __init__(self):
        super(RemoteSessionsNotAvailable, self).__init__(
            'No remote sessions available. Please visit your Project Drive in Artella Web App and try again!'
        )


class BadRemoteResponse(ArtellaException):
    def __init__(self, message):
        super(BadRemoteResponse, self).__init__(message)
