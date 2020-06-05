#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella API implementation
"""

from __future__ import print_function, division, absolute_import

import artella


def _get_client():
    """
    Returns current Artella Drive Client being used by Artella DCC plugin
    :return: Instance of current Artella Drive Client being used
    :rtype: ArtellaDriveClient
    """

    artella_drive_client = artella.DccPlugin().get_client()
    if not artella_drive_client:
        return None

    return artella_drive_client


def ping():
    """
    Test call that returns whether the Artella Drive is valid or not

    :return: Returns a success response or auth failure message
    :rtype: dict
    :example:
    >>> self.ping()
    {
        message: 'OK';
        response: true;
        status_code: 200;
    }
    """

    client = _get_client()
    return client.ping()


def get_local_root():
    """
    Returns the local storage root path for this machine by asking to remote server.
    .. note::
        If local root cannot be retrieved from server (this can happen because server is down or because user
        doesn't have a working internet connection) then this function will try to retrieve the local root path
        from ARTELLA_FOLDER_ROOT environment variable. This environment variable must be defined by users manually
        to point to local root path.

    :return: Absolute path where files are stored locally
    :rtype: str or None
    :example:
    >>> self.get_local_root()
    "C:/Users/artella/artella-files"
    """

    client = _get_client()
    return client.get_local_root()


def get_local_projects():
    """
    Returns all available project files found in the local user machine

    :return: List of dictionaries containing all the information of the current available
    Artella on local user machine projects
    :rtype: dict(str, dict(str, str))
    """

    client = _get_client()
    return client.get_local_projects()


def download_file(file_path, show_dialogs=True):
    """
    Downloads a file from Artella server

    :param str file_path: File we want to download from Artella server
    :param bool show_dialogs: Whether UI dialogs should appear or not.
    :return: True if the download operation was successful; False otherwise.
    :example:
    >>> self.download_file("C:/Users/artella/artella-files/ProjectA/Assets/test/model/hello.a")
    True
    """

    return artella.DccPlugin().download_file(file_path=file_path, show_dialogs=show_dialogs)





if __name__ == '__main__':
    pass
