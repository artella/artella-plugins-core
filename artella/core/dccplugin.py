#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella DCC Plugin functionality
"""

from __future__ import print_function, division, absolute_import

import os
import time
import logging
import threading

from artella import dcc
from artella.core.dcc import parser
from artella.core import utils, qtutils, callbacks, splash
from artella.widgets import snackbar

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtWidgets

logger = logging.getLogger('artella')

_DCC_PLUGIN = None


class _MetaDccPlugin(type):

    def __call__(cls, *args, **kwargs):

        global _DCC_PLUGIN
        if _DCC_PLUGIN:
            return _DCC_PLUGIN

        if dcc.is_maya():
            from artella.dccs.maya import plugin
            _DCC_PLUGIN = type.__call__(plugin.ArtellaMayaPlugin, *args, **kwargs)
        elif dcc.is_unreal():
            from artella.dccs.unreal import plugin
            _DCC_PLUGIN = type.__call__(plugin.ArtellaUnrealPlugin, *args, **kwargs)
        else:
            _DCC_PLUGIN = type.__call__(BaseArtellaDccPlugin, *args, **kwargs)

        return _DCC_PLUGIN


class BaseArtellaDccPlugin(object):

    MENU_NAME = 'Artella'
    _ASYNC_INVOKER, _SYNC_INVOKER = range(2)

    def __init__(self, artella_drive_client):
        super(BaseArtellaDccPlugin, self).__init__()

        self._artella_drive_client = artella_drive_client
        self._dev = False
        self._main_menu = None

        self._main_thread_invoker, self._main_thread_async_invoker = self._create_main_thread_invokers()

    # ==============================================================================================================
    # PROPERTIES
    # ==============================================================================================================

    @property
    def dev(self):
        """
        Returns whether Artella DCC plugin is being executed in dev mode or not
        :return: True if dev mode is enabled; False otherwise.
        :rtype: bool
        """

        return self._dev

    # ==============================================================================================================
    # INITIALIZATION / SHUTDOWN
    # ==============================================================================================================

    def setup_project(self, artella_local_root_path):
        """
        Setup Artella local root as current DCC active project
        This function should be override in specific DCC plugin implementation
        Is not an abstract function because its implementation is not mandatory

        :param str artella_local_root_path: current user Artella local root path
        """

        pass

    def get_version_variable_name(self):
        """
        Returns the environment variable name used to store current Arqtella DCC plugin version

        :return: Environment version name
        :rtype: str
        """

        return 'ARTELLA_{}_PLUGIN'.format(dcc.name())

    def get_version(self, force_update=False):
        """
        Returns current DCC plugin version

        :param bool force_update: Where or not force the update of the current Artella DCC plugin version
        :return: Version in string format (MAJOR.MINOR.PATH) of the current Artella DCC plugin
        :rtype: str or None
        """

        version_var = self.get_version_variable_name()
        plugin_version = os.environ.get(version_var, None)

        return plugin_version

    def init(self, dev=False, show_dialogs=True, create_menu=True, create_callbacks=True,  *args, **kwargs):
        """
        Initializes Artella plugin in current DCC.

        :param bool dev: Whether plugin is initialized in development mode or not
        :param bool show_dialogs: Whether dialogs should appear during plugin initialization or not
        :param bool create_menu: Whether menu should be created or not
        :param bool create_callbacks: Whether or not DCC callbacks should be created
        :return: True if the initialization was successful; False otherwise.
        :rtype: bool
        """

        self._dev = dev

        # Initialize DCC plugin version
        self.get_version(force_update=True)

        # Initialize Artella callbacks
        if create_callbacks:
            self.setup_callbacks()

        # Create Artella DCC Menu
        if create_menu:
            dcc.execute_deferred(self.create_menus)

        # Initialize Artella Drive client
        _init_client = kwargs.pop('init_client', True)
        if _init_client:
            self.init_client(show_dialogs=show_dialogs)

        logger.debug('trying to create quit signal ...')
        if qtutils.QT_AVAILABLE:
            app = QtWidgets.QApplication.instance()
            logger.debug('connecting dcc app to signal: {}'.format(app))
            if app:
                app.aboutToQuit.connect(self._on_quit_app)
            else:
                logger.debug('Impossible to connect because app does not exists')
        else:
            logger.debug('Impossible to create signal because qt is not available')

        return True

    def init_client(self, show_dialogs=True):
        """
        Initializes Artella Drive Client.

        :param bool show_dialogs: Whether dialogs should appear during plugin initialization or not
        :return: True if the Artella Drive client initialization was successful; False otherwise.
        :rtype: bool
        """

        artella_drive_client = self._artella_drive_client or self.get_client(show_dialogs=show_dialogs)
        if artella_drive_client:
            self.setup_project(artella_drive_client.get_local_root())
            artella_drive_client.artella_drive_listen()
        else:
            logger.warning(
                'Artella Drive Client was not initialized. Artella server '
                'dependant functionality will not be available!')
            return False

        return True

    def shutdown(self, dev=False):
        """
        Shutdown/Uninitialize Artella plugin in current DCC
        :return: True if the shutdown was successful; False otherwise
        :rtype: bool
        """

        # Remove Artella callbacks
        self.remove_callbacks()

        # Remove Artella DCC Menu
        if dev:
            self.remove_menus()
        else:
            dcc.execute_deferred(self.remove_menus)

        if not self._artella_drive_client:
            return False

        self._artella_drive_client.artella_drive_disconnect()
        self._artella_drive_client = None

        return True

    # ==============================================================================================================
    #  EXECUTION
    # ==============================================================================================================

    def execute_in_main_thread(self, fn, *args, **kwargs):
        """
        Executes the given function in the main thread when called from a non-main thread. This will block the
        calling thread until the function returns.

        .. warning: This can introduce a deadlock if the main thread is waiting for a background thread and the
            this thread is invoking this method. Since the main thread is waiting for the background thread to finish,
            Qt's event loop won't be able to process the request to execute in the main thread
        :param fn: function to call
        :param args:
        :param kwargs:
        :return:
        """

        return self._execute_in_main_thread(self._SYNC_INVOKER, fn, *args, **kwargs)

    def async_execute_in_main_thread(self, fn, *args, **kwargs):
        """
        Executes the given function in the main thread when called from a non-main thread. This call will return
        immediately and will not wait for the code to be executed in the main thread.

        :param fn: function to call
        :param args:
        :param kwargs:
        :return:
        """

        return self._execute_in_main_thread(self._ASYNC_INVOKER, fn, *args, **kwargs)

    # ==============================================================================================================
    #  MENU
    # ==============================================================================================================

    def get_main_menu(self):
        """
        Returns instance of Artella main menu
        :return:
        """

        return self._main_menu

    def create_menus(self):
        """
        Setup DCC Artella menu.
        If the menu already exists, it will be deleted and recreated.
        :return: True if the menu was created successfully; False otherwise
        :rtype: bool
        """

        if dcc.check_menu_exists(self.MENU_NAME):
            dcc.remove_menu(self.MENU_NAME)

        artella_menu = dcc.add_menu(self.MENU_NAME, icon='artella.png')
        if not artella_menu:
            return False

        self._main_menu = artella_menu

        return True

    def remove_menus(self):
        """
        Removes already created DCC Artella menu
        :return: True if the menu was removed successfully; False otherwise
        :rtype: bool
        """

        if not dcc.check_menu_exists(self.MENU_NAME):
            return False

        dcc.remove_menu(self.MENU_NAME)

        return True

    # ==============================================================================================================
    # CALLBACKS
    # ==============================================================================================================

    def setup_callbacks(self):
        """
        Setup DCC Artella callbacks
        :return:
        """

        callbacks.initialize_callbacks()

    def remove_callbacks(self):
        """
        Removes all DCC Artella callbacks previously created
        :return:
        """

        callbacks.uninitialize_callbacks()

    def validate_environment_for_callback(self, callback_name):
        """
        Checks that all necessary parts are available before executing a Maya callback

        :param str callback_name: name of the callback to validate
        """

        logger.info('validate_environment_for_callback for {}'.format(callback_name))
        client = self.get_client()
        local_root = dcc.clean_path()

    # ==============================================================================================================
    # ARTELLA DRIVE APP
    # ==============================================================================================================

    def update_auth_challenge(self):
        """
        Updates the authentication header by checking challenge file (if available)

        :return: True if the authenticator header was read successfully; False otherwise.
        :rtype: bool
        """

        if not self._artella_drive_client:
            return False

        auth_header = self._artella_drive_client.update_auth_challenge()

        return True if auth_header else False

    def get_client(self, show_dialogs=True):
        """
        Returns current Artella Drive Client being used by Artella Plugin

        :return: Instance of current ArtellaDriveClient being used; None if not Artella Drive Client is being used.
        :rtype: ArtellaDriveClient or None
        """

        # To avoid cyclic imports
        from artella.core import client

        if not self._artella_drive_client:
            # TODO: Here we are not taking into account custom extensions (check loader). We should store them
            # TODO: in an env variable and access them here
            dcc_extensions = dcc.extensions()
            artella_drive_client = client.ArtellaDriveClient.get(extensions=dcc_extensions)
            if not artella_drive_client:
                if show_dialogs:
                    self.show_warning_message(
                        'Local Drive Client not available. Please launch Artella Drive App', 'Artella Drive App')
                return None
            else:
                self._artella_drive_client = artella_drive_client
                self.init_client()
        else:
            if not self._artella_drive_client.is_running:
                self.init_client()

        if not self._artella_drive_client.is_available:
            self._artella_drive_client.update_remotes_sessions(show_dialogs=False)
            if not self._artella_drive_client.is_available:
                if show_dialogs:
                    self.show_warning_message(
                        'Local Drive Client not available. Please launch Artella Drive App', 'Artella Drive App')
                return None

        # The challenge value gets updated when the Artella Drive App restarts.
        # We must check auth each time in case Artella Drive is restarted but Maya didn't
        self.update_auth_challenge()

        return self._artella_drive_client

    def pass_message(self, json_data):
        """
        Executes handle message Artella plugin functionality in specific DCC thread to make sure that it does not
        conflicts with main DCC UI thread
        :param json_data:

        """

        logger.debug('Passing message to {}: {}'.format(dcc.name(), json_data))
        self.execute_in_main_thread(self.handle_message, json_data)

    def handle_message(self, msg):
        """
        Internal function that handles the response received from Artella Drive App

        :param dict msg: Dictionary containing the response from Artella server
        """

        logger.debug('Handling realtime message: {}'.format(msg))
        if not isinstance(msg, dict):
            logger.warning('Malformed realtime message: {}'.format(msg))
            return

        command_name = msg.get('type')
        dcc_name = dcc.name()

        if command_name.startswith(dcc_name):
            dcc_operation = command_name.split('-')[-1]
            file_path = msg['data']['ARTELLA_FILE']
            if dcc_operation == 'import':
                self._handle_import_message(file_path)
            elif dcc_operation == 'reference':
                self._handle_reference_message(file_path)
        elif command_name == 'authorization-ok':
            logger.debug('websocket connection successful.')
        elif command_name == 'open':
            file_path = msg['data']['ARTELLA_FILE']
            self._handle_open_message(file_path)
        else:
            pass

    def artella_info(self):
        """
        Function that prints useful information related with current Artella Plugin status
        """

        logger.info('Artella Plugin Status Info ...')
        artella_drive_client = self.get_client()
        logger.info(artella_drive_client.get_metadata())
        logger.info(artella_drive_client.get_storage_id())
        logger.info(artella_drive_client.ping())
        logger.info(artella_drive_client.artella_drive_connect())
        logger.info('Local Root: {}'.format(artella_drive_client.get_local_root()))

    # ==============================================================================================================
    # FILE PATHS
    # ==============================================================================================================

    def is_artella_path(self, file_path=None):
        """
        Returns whether or not given file path is an Artella file path or not
        A path is considered to be an Artella path if the path is located inside the Artella project folder
        in the user machine

        :param str file_path: path to check. If not given, current DCC scene file path will be used
        :return: True if the given file path is an Artella path; False otherwise.
        :rtype: bool
        """

        artella_drive_client = self.get_client(show_dialogs=False)
        if not artella_drive_client:
            return False

        file_path = file_path or dcc.scene_name()

        return artella_drive_client.is_artella_path(file_path)

    def local_path_to_uri(self, file_path):
        """
        Translates a local file path to its URI format
        :param str file_path: Absolute local file path we want to translate to URI
        :param str prefix:

        :return: path in its URI format if current DCC supports this feature; path without any change otherwise
        :rtype: str
        """

        if not dcc.supports_uri_scheme():
            logger.warning('Current DCC {} does not supports Artella URI scheme!'.format(dcc.name()))
            return file_path

        return file_path

    def translate_path(self, file_path):
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

        artella_drive_client = self.get_client(show_dialogs=False)
        if not artella_drive_client:
            return file_path

        return artella_drive_client.translate_path(file_path)

    def is_path_translated(self, file_path):
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

        artella_drive_client = self.get_client(show_dialogs=False)
        if not artella_drive_client:
            return False

        return artella_drive_client.is_path_translated(file_path)

    def convert_path(self, file_path):
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

        artella_drive_client = self.get_client(show_dialogs=False)
        if not artella_drive_client:
            return file_path

        return artella_drive_client.convert_path(file_path)

    @utils.timestamp
    def update_paths(self, file_path=None, show_dialogs=True, call_post_function=True, skip_save=True):
        """
        Updates all file paths of the given file path to make sure that they point to valid Artella file paths

        :param str file_path:
        :param bool show_dialogs:
        :param bool call_post_function:
        :param bool skip_save:
        :return:
        """

        artella_drive_client = self.get_client(show_dialogs=False)
        if not artella_drive_client:
            return False

        if not file_path:
            file_path = dcc.scene_name()
        if not file_path:
            msg = 'No file paths given to convert. Impossible to update paths.'
            logger.warning(msg)
            if show_dialogs:
                dcc.show_warning(title='Artella - Failed to update paths', message=msg)
            return False

        file_paths = utils.force_list(file_path, remove_duplicates=True)

        converted_paths = list()
        for file_path in file_paths:

            local_path = artella_drive_client.translate_path(file_path)

            ext = os.path.splitext(local_path)[-1]
            if ext not in dcc.extensions() or not os.path.isfile(local_path):
                logger.info('Skipping non DCC scene file path from conversion: "{}"'.format(local_path))
                continue

            can_lock = self.can_lock_file(local_path, show_dialogs=False)
            if not can_lock:
                logger.warning(
                    'File "{}" cannot be locked and paths cannot be updated. Skipping ...'.format(local_path))
                continue

            if dcc.scene_name() != file_path:
                dcc.open_scene(file_path, save=True)

            dcc_parser = parser.Parser()
            valid_convert, updated_paths = dcc_parser.update_paths(local_path)
            updated_paths = utils.force_list(updated_paths)
            converted_paths.extend(updated_paths)

            if valid_convert and updated_paths and not skip_save:
                dcc.save_scene()

        converted_paths = list(set(converted_paths))
        if call_post_function and converted_paths:
            self._post_update_paths(files_updated=converted_paths)

    # ==============================================================================================================
    # VERSIONS
    # ==============================================================================================================

    def make_new_version(self, file_path=None, comment=None, do_lock=False):
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

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return False

        if not file_path:
            file_path = dcc.scene_name()
            if not file_path:
                msg = 'Please open a file before creating a new version'
                logger.warning(msg)
                return False

        can_lock = artella_drive_client.can_lock_file(file_path=file_path)
        if not can_lock:
            msg = 'Unable to lock file to make new version. File is already locked by other user.'
            dcc.show_error('File already locked by other user', msg)
            logger.error(msg)
            return False

        version_created = True

        comment = str(comment) if comment else 'New file version'

        file_version = artella_drive_client.file_current_version(file_path)
        if file_version is None:
            self.show_warning_message('Unable to retrieve version from current scene')
            return False

        next_version = file_version + 1

        is_locked, _, _, _ = artella_drive_client.check_lock(file_path)
        if not is_locked and do_lock:
            valid_lock = self.lock_file()
            if not valid_lock:
                self.show_error_message('Unable to lock file to make new version ({})'.format(next_version))
                return False

        logger.info('Saving current scene: {}'.format(file_path))
        valid_save = dcc.save_scene()
        if not valid_save:
            self.show_error_message('Unable to save current scene: "{}"'.format(file_path))
            version_created = False
        else:
            uri_path = self.local_path_to_uri(file_path)
            rsp = artella_drive_client.upload(uri_path, comment=comment)
            if rsp.get('error'):
                msg = 'Unable to upload a new version of file: "{}"\n{}\n{}'.format(
                    os.path.basename(file_path), rsp.get('url'), rsp.get('error'))
                self.show_error_message(msg)
                version_created = False

        if not is_locked and do_lock:
            self.unlock_file(show_dialogs=False)

        return version_created

    # ==============================================================================================================
    # LOCK/UNLOCK STATUS
    # ==============================================================================================================

    def check_lock(self, file_path=None, show_dialogs=True):
        """
        Returns whether or not the given file is locked and whether or not current user is the one that has the file
        locked.

        :param str file_path: Absolute local file path to check lock status of
        :return: Returns a tuple with the following fields:
            - is_locked: True if the given file is locked; False otherwise
            - is_locked_by_me: True if the given file is locked by current user; False otherwise
            - locked_by_name: Name of the user that currently has the file locked
            - remote_record_found: Indicates whether the request relates to an existing remote file record or not
        :param bool show_dialogs: Whether UI dialogs should appear or not.
        :rtype: tuple(bool, bool, str)
        """

        artella_drive_client = self.get_client(show_dialogs=show_dialogs)
        if not artella_drive_client:
            return False, False, '', False

        if not file_path:
            file_path = dcc.scene_name()
        if not file_path:
            msg = 'File "{}" does not exists. Impossible to check lock status!'.format(file_path)
            logger.warning(msg)
            if show_dialogs:
                dcc.show_warning(title='Artella - Failed to check lost status', message=msg)
            return False, False, '', False

        return artella_drive_client.check_lock(file_path)

    def can_lock_file(self, file_path=None, show_dialogs=True):
        """
        Returns whether or not current opened DCC file can locked or not
        A file only can be locked if it is not already locked by other user.

        :param str or None file_path: Absolute local file path we want to check if can be locked or not. If not given,
            current DCC scene file will be locked.
        :param bool show_dialogs: Whether UI dialogs should appear or not.
        :return: True if the file can be locked by current user; False otherwise.
        :rtype: bool
        """

        artella_drive_client = self.get_client(show_dialogs=show_dialogs)
        if not artella_drive_client:
            return False

        if not file_path:
            file_path = dcc.scene_name()
        if not file_path:
            msg = 'File "{}" does not exists. Impossible to check if file can be locked or not!'.format(file_path)
            logger.warning(msg)
            if show_dialogs:
                dcc.show_warning(title='Artella - Failed to check lost status', message=msg)
            return False

        return artella_drive_client.can_lock_file(file_path)

    def lock_file(self, file_path=None, force=False, show_dialogs=True):
        """
        Locks given file path in Artella Drive.

        :param str or None file_path: Absolute local file path we want to lock. If not given, current DCC scene file
            will be locked.
        :param bool force: Whether to force the lock operation. If the file is locked by other user, the lock is break.
        :param bool show_dialogs: Whether UI dialogs should appear or not.
        :return: True if the lock operation was successful; False otherwise
        :rtype: bool
        """

        artella_drive_client = self.get_client(show_dialogs=show_dialogs)
        if not artella_drive_client:
            return False

        if not file_path:
            file_path = dcc.scene_name()
            if not file_path:
                msg = 'Unable to get file name, has it been created!?'
                logger.warning(msg)
                if show_dialogs:
                    dcc.show_warning(title='Artella - Failed to lock file', message=msg)
                return False

        if not file_path or not os.path.isfile(file_path):
            msg = 'File "{}" does not exists. Impossible to lock.'.format(file_path)
            logger.warning(msg)
            if show_dialogs:
                dcc.show_error('Artella - Failed to lock File', msg)
            return False

        file_version = artella_drive_client.file_current_version(file_path)
        if file_version <= 0:
            logger.info('File "{}" is not versioned yet. No need to lock.'.format(file_path))
            return True

        is_locked, is_locked_by_me, is_locked_by_name, remote_record_found = artella_drive_client.check_lock(file_path)
        can_write = os.access(file_path, os.W_OK)
        if not can_write and is_locked_by_me:
            logger.warning('Unable to determine local write permissions for file: "{}"'.format(file_path))
        if is_locked and not is_locked_by_me:
            msg = 'This file is locked by another user ({}). The file must be unlocked in order to save a new version.'
            logger.warning(msg)
            if show_dialogs:
                dcc.show_warning('Artella - Failed to lock file', msg)
            return False
        elif force or not is_locked:
            msg = '"{}" needs to be locked in order to save your file. ' \
                  'Would you like to lock the file now?'.format(os.path.basename(file_path))
            result = True
            if show_dialogs:
                result = dcc.show_question('Artella - lock file', msg, cancel=False)
            if result is not True:
                return False

        valid_lock = artella_drive_client.lock_file(file_path)
        if not valid_lock:
            msg = 'Failed to lock "{}"'.format(file_path)
            logger.warning(msg)
            dcc.show_warning('Artella - Failed to lock file', msg)
            return False

        return True

    def unlock_file(self, file_path=None, show_dialogs=True, force=False):
        """
        Unlocks given file path in Artella Drive.

        :param str or None file_path: Absolute local file path we want to lock. If not given, current DCC scene file
            will be unlocked.
        :param bool show_dialogs: Whether UI dialogs should appear or not.
        :param bool force: Whether or not unlock operation should be done without asking the user
        :return: True if the lock operation was successful; False otherwise
        :rtype: bool
        """

        artella_drive_client = self.get_client(show_dialogs=show_dialogs)
        if not artella_drive_client:
            return False

        if not file_path:
            file_path = dcc.scene_name()
            if not file_path:
                msg = 'Unable to get file name, has it been created!?'
                logger.warning(msg)
                if show_dialogs:
                    dcc.show_warning(title='Artella - Failed to lock file', message=msg)
                return False

        if not file_path or not os.path.isfile(file_path):
            msg = 'File "{}" does not exists. Impossible to unlock.'.format(file_path)
            logger.warning(msg)
            if show_dialogs:
                dcc.show_error('Artella - Failed to unlock file', msg)
            return False

        result = True
        if show_dialogs and not force:
            msg = 'You have file "{}" locked in Artella.\nUnlock it now?'.format(os.path.basename(file_path))
            result = dcc.show_question('Artella - Unlock File', msg, cancel=False)
        if result is not True:
            return False

        uri_path = self.local_path_to_uri(file_path)
        valid_unlock = artella_drive_client.unlock_file(uri_path)
        if not valid_unlock:
            msg = 'Failed to unlock the file: "{}"\nTry unlocking it from the Artella ' \
                  'Drive area in the web browser'.format(os.path.basename(file_path))
            logger.warning(msg)
            if show_dialogs:
                dcc.show_error('Artella - Failed to unlock file', msg)
            return False

        return True

    # ==============================================================================================================
    # DOWNLOAD
    # ==============================================================================================================

    def download_file(self, file_path, show_dialogs=True):
        """
        Downloads a file from Artella server

        :param str file_path: File we want to download from Artella server
        :param bool show_dialogs: Whether UI dialogs should appear or not.
        :return: True if the download operation was successful; False otherwise.
        :example:
        >>> self.download_file("C:/Users/artella/artella-files/ProjectA/Assets/test/model/hello.a")
        True
        """

        artella_drive_client = self.get_client(show_dialogs=show_dialogs)
        if not artella_drive_client:
            return False

        local_path = artella_drive_client.translate_path(file_path)

        remote_file_size = 0
        file_status = artella_drive_client.status(local_path, include_remote=True)
        if not file_status:
            logger.warning('File "{}" not found in remote'.format(file_status))
            return False
        file_status = file_status[0]
        for version_id, version_data in file_status.items():
            if not version_id or not version_id.startswith('project__'):
                continue
            remote_file_size = version_data.get('remote_info', dict()).get('content_length', 0)
            break
        if not remote_file_size:
            logger.warning('File "{}" in remote has not a valid file size: {}'.format(local_path, remote_file_size))
            return False

        if show_dialogs:
            dcc_progress_bar = splash.ProgressSplashDialog()
            dcc_progress_bar.start()
            if qtutils.QT_AVAILABLE:
                QtWidgets.QApplication.instance().processEvents()

        artella_drive_client.download(local_path)
        time.sleep(1.0)

        valid_download = True
        while True:
            if show_dialogs:
                dcc_progress_bar.repaint()
                if dcc_progress_bar.is_cancelled():
                    artella_drive_client.pause_downloads()
                    valid_download = False
                    break
            progress, fd, ft, bd, bt = artella_drive_client.get_progress()
            progress_status = '{} | {} of {} KiB downloaded\n{} of {} files downloaded'.format(
                    os.path.basename(file_path), int(bd / 1024), int(bt / 1024), fd, ft)
            if show_dialogs:
                dcc_progress_bar.set_progress_value(value=progress, status=progress_status)
                if qtutils.QT_AVAILABLE:
                    QtWidgets.QApplication.instance().processEvents()
            if progress >= 100 or bd == bt:
                break

        if show_dialogs:
            dcc_progress_bar.end()

        total_checks = 0
        if valid_download:
            while not os.path.exists(local_path) and total_checks < 5:
                time.sleep(1.0)
                total_checks += 1
            if not os.path.exists(local_path):
                return False
            total_checks = 0
            file_size = os.path.getsize(local_path)
            while file_size != remote_file_size and total_checks < 5:
                file_size = os.path.getsize(local_path)
                time.sleep(1.0)
                total_checks += 1
            if file_size != remote_file_size:
                return False

        return valid_download

    # ==============================================================================================================
    # UI
    # ==============================================================================================================

    def show_artella_message(self, text, title='', duration=None, closable=True):
        """
        Shows an Artella message

        :param text: str, artella text to show
        :param title: str, title of the artella message
        :param duration: float or None, if given, message only will appear the specified seconds
        :param closable: bool, Whether the message can be closed by the user or not (when duration is given)
        """

        logger.debug(str(text))
        if not qtutils.QT_AVAILABLE:
            return

        snackbar.SnackBarMessage.artella(text=text, title=title, duration=duration, closable=closable)

    def show_success_message(self, text, title='', duration=None, closable=True):
        """
        Shows a success message

        :param text: str, success text to show
        :param title: str, title of the success message
        :param duration: float or None, if given, message only will appear the specified seconds
        :param closable: bool, Whether the message can be closed by the user or not (when duration is given)
        """

        logger.info(str(text))
        if not qtutils.QT_AVAILABLE:
            return

        snackbar.SnackBarMessage.success(text=text, title=title, duration=duration, closable=closable)

    def show_info_message(self, text, title='', duration=None, closable=True):
        """
        Shows an info message

        :param text: str, info text to show
        :param title: str, title of the info message
        :param duration: float or None, if given, message only will appear the specified seconds
        :param closable: bool, Whether the message can be closed by the user or not (when duration is given)
        """

        logger.info(str(text))
        if not qtutils.QT_AVAILABLE:
            return

        snackbar.SnackBarMessage.info(text=text, title=title, duration=duration, closable=closable)

    def show_warning_message(self, text, title='', duration=None, closable=True):
        """
        Shows a warning message

        :param text: str, warning text to show
        :param title: str, title of the warning message
        :param duration: float or None, if given, message only will appear the specified seconds
        :param closable: bool, Whether the message can be closed by the user or not (when duration is given)
        """

        logger.warning(str(text))
        if not qtutils.QT_AVAILABLE:
            return

        snackbar.SnackBarMessage.warning(text=text, title=title, duration=duration, closable=closable)

    def show_error_message(self, text, title='', duration=None, closable=True):
        """
        Shows an error message

        :param text: str, error text to show
        :param title: str, title of the error message
        :param duration: float or None, if given, message only will appear the specified seconds
        :param closable: bool, Whether the message can be closed by the user or not (when duration is given)
        :return:
        """

        logger.error(str(text))
        if not qtutils.QT_AVAILABLE:
            return

        snackbar.SnackBarMessage.error(text=text, title=title, duration=duration, closable=closable)

    # ==============================================================================================================
    # INTERNAL
    # ==============================================================================================================

    def _post_update_paths(self, **kwargs):
        """
        Internal function that is called after update paths functionality is over. Can be override in custom DCC
        plugins.
        """

        pass

    def _handle_open_message(self, file_path):
        """
        Internal function that is called when websocket receives a message to open a file in DCC

        :param str file_path: Absolute local file path we need to open in current DCC
        :return:
        """

        return dcc.open_scene(file_path=file_path, save=False)

    def _handle_import_message(self, file_path):
        """
        Internal function that is called when websocket receives a message to import a file in DCC

        :param str file_path: Absolute local file path we need to import into current DCC
        :return:
        """

        return dcc.import_scene(file_path=file_path)

    def _handle_reference_message(self, file_path):
        """
        Internal function that is called when websocket receives a message to reference a file in DCC

        :param str file_path: Absolute local file path we need to reference into current DCC
        :return:
        """

        return dcc.reference_scene(file_path=file_path)

    def _execute_in_main_thread(self, invoker_id, fn, *args, **kwargs):
        """
        Internal function that executes the given function and arguments with the given invoker. If the invoker
        is not ready or if the calling thread is the main thread, the function is called immediately with given
        arguments.

        :param int invoker_id: _SYNC_INVOKER or _ASYNC_INVOKER
        :param callable fn: function to call
        :param args:
        :param kwargs:
        :return: Return value from the invoker
        :rtype: object
        """

        dcc_main_thread_fn = dcc.pass_message_to_main_thread_fn()
        if not qtutils.QT_AVAILABLE and not dcc_main_thread_fn:
            return fn(*args, **kwargs)

        # If DCC has a specific function to invoke functions in main thread, we use it
        if dcc_main_thread_fn:
            return dcc_main_thread_fn(fn, *args, **kwargs)
        else:
            invoker = (
                self._main_thread_invoker if invoker_id == self._SYNC_INVOKER else self._main_thread_async_invoker)
            if invoker:
                if QtWidgets.QApplication.instance() and (
                        QtCore.QThread.currentThread() != QtWidgets.QApplication.instance().thread()):
                    return invoker.invoke(fn, *args, **kwargs)
                else:
                    return fn(*args, **kwargs)
            else:
                return fn(*args, **kwargs)

    def _create_main_thread_invokers(self):
        """
        Internal function that creates invoker objects that allow to invoke function calls on the main thread when
        called from a different thread
        """

        invoker = None
        async_invoker = None

        if qtutils.QT_AVAILABLE:

            class MainThreadInvoker(QtCore.QObject):
                """
                Class that implements a mechanism to execute a function with arbitrary arguments in main thread for DCCs
                that support Qt
                """

                def __init__(self):
                    super(MainThreadInvoker, self).__init__()

                    self._lock = threading.Lock()
                    self._fn = None
                    self._res = None

                def invoke(self, fn, *args, **kwargs):
                    """
                    Invoke the given function with the given arguments and keyword arguments in the main thread

                    :param function fn: function to execute in main thread
                    :param tuple args: args for the function
                    :param dict kwargs: Named arguments for the function
                    :return: Returns the result returned by the function
                    :rtype: object
                    """

                    # Acquire lock to make sure that both function and result are not overwritten by synchronous calls
                    # to this method from different threads
                    self._lock.acquire()

                    try:
                        self._fn = lambda: fn(*args, **kwargs)
                        self._res = None

                        # Invoke the internal function that will run the function.
                        # NOTE: We cannot pass/return arguments through invokeMethod as
                        # this isn't properly supported by PySide
                        QtCore.QMetaObject.invokeMethod(self, '_do_invoke', QtCore.Qt.BlockingQueuedConnection)

                        return self._res
                    finally:
                        self._lock.release()

                @QtCore.Slot()
                def _do_invoke(self):
                    """
                    Internal function that executes the function
                    """

                    self._res = self._fn()

            class MainThreadAsyncInvoker(QtCore.QObject):
                """
                Class that implements a mechanism to execute a function with arbitrary arguments in main
                thread asynchronously
                for DCCs that support Qt
                """

                __signal = QtCore.Signal(object)

                def __init__(self):
                    super(MainThreadAsyncInvoker, self).__init__()

                    self.__signal.connect(self.__execute_in_main_thread)

                def invoke(self, fn, *args, **kwargs):
                    """
                     Invoke the given function with the given arguments and keyword arguments in the main thread

                     :param function fn: function to execute in main thread
                     :param tuple args: args for the function
                     :param dict kwargs: Named arguments for the function
                     :return: Returns the result returned by the function
                     :rtype: object
                     """

                    self._signal.emit(lambda: fn(*args, **kwargs))

                def __execute_in_main_thread(self, fn):
                    """
                    Internal function that executes the function
                    """

                    fn()

            # Make sure invoker exists in main thread
            invoker = MainThreadInvoker()
            async_invoker = MainThreadAsyncInvoker()
            if QtCore.QCoreApplication.instance():
                invoker.moveToThread(QtCore.QCoreApplication.instance().thread())
                async_invoker.moveToThread(QtCore.QCoreApplication.instance().thread())

        return invoker, async_invoker

    # ==============================================================================================================
    # CALLBACKS
    # ==============================================================================================================

    def _on_quit_app(self):
        """
        Internal callback function is called when a DCC with Qt support is closed. We use it to make sure that
        Artella Drive Client is stopped.
        """

        logger.debug('Quiting app ...')

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return

        artella_drive_client.artella_drive_disconnect()

    # ==============================================================================================================
    # ABSTRACT
    # ==============================================================================================================

    @utils.abstract
    def register_uri_resolver(self):
        """
        Function that registers DCC specific Artella URI resolver
        This function must be implemented in those dcc.that support this feature
        """

        pass


@utils.add_metaclass(_MetaDccPlugin)
class DccPlugin(object):
    pass
