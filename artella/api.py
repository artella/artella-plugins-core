#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella API implementation
"""

from __future__ import print_function, division, absolute_import

from artella.core import dccplugin


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

    client = get_client()
    if not client:
        return

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

    client = get_client()
    if not client:
        return

    return client.get_local_root()


def get_local_projects():
    """
    Returns all available project files found in the local user machine

    :return: List of dictionaries containing all the information of the current available
    Artella on local user machine projects
    :rtype: dict(str, dict(str, str))
    """

    client = get_client()
    if not client:
        return

    return client.get_local_projects()


def update_paths(file_path=None, show_dialogs=True, call_post_function=True, skip_save=True):
    """
    Updates all file paths of the given file path to make sure that they point to valid Artella file paths

    :param  str or list(str) file_path:
    :param bool show_dialogs:
    :param bool call_post_function:
    :param bool skip_save:
    :return:
    """

    return dccplugin.DccPlugin().update_paths(
        file_path=file_path, show_dialogs=show_dialogs, call_post_function=call_post_function, skip_save=skip_save)


def relative_path_to_absolute_path(relative_path, project_id=None):
    """
    Converts a relative path to an absolute local file path taking into account the given project id

    :param str relative_path: Relative path to a file
    :param str or None project_id: project id the relative path file belongs to
    :return: Absolute local file path of the relative path in the given project
    :rtype: str
    """

    client = get_client()
    if not client:
        return

    return client.relative_path_to_absolute_path(relative_path, project_id=project_id)


def translate_path(file_path):
    """
    Converts a file path to a local file path taking into account the available projects.

    :param str file_path: File path we want to to translate to its user local version
    :return: User local version of the given path
    :rtype: str
    :example:
    >>> self.translate_path("C:/Users/Bobby/artella-files/ProjectA/Assets/Characters/A/Model/a.ma")
    "C:/Users/Tomi/artella/data/ProjectA/Assets/Characters/A/Model/a.ma"
    >>> self.translate_path("/ProjectA/Assets/Characters/A/Model/a.ma")
    "C:/Users/Tomi/artella/data/ProjectA/Assets/Characters/A/Model/a.ma"
    """

    return dccplugin.DccPlugin().translate_path(file_path)


def is_artella_path(file_path=None):
    """
    Returns whether or not given file path is an Artella file path or not
    A path is considered to be an Artella path if the path is located inside the Artella project folder
    in the user machine

    :param str file_path: path to check. If not given, current DCC scene file path will be used
    :return: True if the given file path is an Artella path; False otherwise.
    :rtype: bool
    """

    return dccplugin.DccPlugin().is_artella_path(file_path)


def is_path_translated(file_path):
    """
    Returns whether or not given path is already translated to a valid Artella path

    :param file_path: str, path you want to check translation validation
    :return: True if the given path is an already translated Artella path; False otherwise
    :rtype: bool
    :example:
    >>> self.is_path_translated("C:/Users/Bobby/artella-files/ProjectA/Assets/Characters/A/Model/a.ma")
    False
    >>> self.is_path_translated("$ART_LOCAL_ROOT/ProjectA/refs/ref.png")
    True
    """

    return dccplugin.DccPlugin().is_path_translated(file_path)


def convert_path(file_path):
    """
    Converts given path to a path that Artella can understand

    :param str file_path: File path we want to convert
    :return: str
    :rtype: str
    :example:
    >>> self.translate_path("C:/Users/Bobby/artella-files/ProjectA/Assets/Characters/A/Model/a.ma")
    "$$ART_LOCAL_ROOT/ProjectA/Assets/Characters/A/Model/a.ma"
    >>> self.translate_path("/ProjectA/Assets/Characters/A/Model/a.ma")
    "$ART_LOCAL_ROOT/ProjectA/Assets/Characters/A/Model/a.ma"
    """

    return dccplugin.DccPlugin().convert_path(file_path)


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

    return dccplugin.DccPlugin().download_file(file_path=file_path, show_dialogs=show_dialogs)


def make_new_version(file_path=None, comment=None, do_lock=False):
    """
    Uploads a new file/folder or a new version of current opened DCC scene file

    :param str file_path: Optional path of the file we want to create new version of. If not given, current
        opened DCC scene file path will be used.
    :param str comment: Optional comment to add to new version metadata. If not given, a generic message will be
        used.
    :param bool do_lock: Whether or not to force the lock of the file to make a new version. With new Artella
        version this is not mandatory.
    :return: True if the make new version operation is completed successfully; False otherwise.
    :rtype: bool
    """

    return dccplugin.DccPlugin().make_new_version(file_path=file_path, comment=comment, do_lock=do_lock)


def file_current_version(file_path):
    """
    Returns current version of the given file

    :param str file_path: Absolute local file path to retrieve current local version of
    :param str _status: new file status
    :return: Current local version of the given file path
    :rtype: int
    """

    client = get_client()
    if not client:
        return

    return client.file_current_version(file_path)


def file_is_latest_version(file_path):
    """
    Returns whether or not given local file path is updated to the latest version available in Artella server.

    :param str file_path: Absolute local file path or URI path we want to check version of
    :return: True if the file is updated to the latest version available; False otherwise.
    :rtype: bool
    """

    client = get_client()
    if not client:
        return

    return client.file_is_latest_version(file_path)


def file_status(file_paths, include_remote=False):
    """
    Returns the status of a file from the remote server

    :param str or list(str) file_paths: Local path(s) or Resolved URI path(s) of a folder/file or list of
        folders/files
    :param bool include_remote: Whether to include remote server information into the response. Take into account
        that this call can slow down the server response.
    :return:
    :rtype: dict
    :example:
    >>> self.status('artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png')
    >>> self.status('C:/Users/artella/artella-files/projects/refs/ref.png')
    {
        'project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png':
        {
            'local_info':
            {
                'content_length': 390223,
                'remote_version': 1,
                'name': u'Area.png',
                'modified_time': '2020-03-11T23:38:01.3985577+01:00',
                'mode': u'0666',
                'signature':
                'sha1:f67817bdfa6a828ab3a80110d2e52ca8a430afb7',
                'path': u'C:\\Users\\artella\\artella-files\\project\\refs\\ref.png'
            }
        }
    }
    """

    client = get_client()
    if not client:
        return

    return client.status(file_paths, include_remote=include_remote)


def async_execute_in_main_thread(fn, *args, **kwargs):
    """
    Executes the given function in the main thread when called from a non-main thread. This call will return
    immediately and will not wait for the code to be executed in the main thread.

    :param fn: function to call
    :param args:
    :param kwargs:
    :return:
    """

    return dccplugin.DccPlugin().async_execute_in_main_thread(fn=fn, *args, **kwargs)


def show_success_message(text, title='', duration=None, closable=True):
    """
    Shows an info message

    :param text: str, success text to show
    :param title: str, title of the success message
    :param duration: float or None, if given, message only will appear the specified seconds
    :param closable: bool, Whether the message can be closed by the user or not (when duration is given)
    """

    return dccplugin.DccPlugin().show_success_message(text=text, title=title, duration=duration, closable=closable)


def show_info_message(text, title='', duration=None, closable=True):
    """
    Shows an info message

    :param text: str, info text to show
    :param title: str, title of the info message
    :param duration: float or None, if given, message only will appear the specified seconds
    :param closable: bool, Whether the message can be closed by the user or not (when duration is given)
    """

    return dccplugin.DccPlugin().show_info_message(text=text, title=title, duration=duration, closable=closable)


def show_warning_message(text, title='', duration=None, closable=True):
    """
    Shows a warning message

    :param text: str, warning text to show
    :param title: str, title of the warning message
    :param duration: float or None, if given, message only will appear the specified seconds
    :param closable: bool, Whether the message can be closed by the user or not (when duration is given)
    """

    return dccplugin.DccPlugin().show_warning_message(text=text, title=title, duration=duration, closable=closable)


def show_error_message(text, title='', duration=None, closable=True):
    """
    Shows an error message

    :param text: str, error text to show
    :param title: str, title of the error message
    :param duration: float or None, if given, message only will appear the specified seconds
    :param closable: bool, Whether the message can be closed by the user or not (when duration is given)
    :return:
    """

    return dccplugin.DccPlugin().show_error_message(text=text, title=title, duration=duration, closable=closable)


def is_client_available(update=False):
    """
    Returns whether or not current client is available

    :param update: bool, Whether or not remote sessions should be updated
        :return: True if the client is available and running; False otherwise.
    :rtype: ArtellaDriveClient
    """

    artella_drive_client = dccplugin.DccPlugin().get_client()
    if not artella_drive_client or not artella_drive_client.check(update=update):
        return False

    return True


def get_client(check=False, update=False):
    """
    Returns current Artella Drive Client being used by Artella DCC plugin

    :param check: bool, Whether check or not client is available and running
    :param update: bool, Whether or not remote sessions should be updated
    :return: Instance of current Artella Drive Client being used
    :rtype: ArtellaDriveClient
    """

    artella_drive_client = dccplugin.DccPlugin().get_client()
    if check and not artella_drive_client.check(update=update):
        return None
    if not artella_drive_client:
        return None

    return artella_drive_client


if __name__ == '__main__':
    pass
