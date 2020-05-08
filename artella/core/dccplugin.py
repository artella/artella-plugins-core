#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella DCC Plugin functionality
"""

from __future__ import print_function, division, absolute_import

import os
import time

import artella
from artella import dcc
from artella import logger
from artella import register
from artella.core import utils


class ArtellaDccPlugin(object):

    MENU_NAME = 'Artella'

    def __init__(self, artella_drive_client):
        super(ArtellaDccPlugin, self).__init__()

        self._artella_drive_client = artella_drive_client
        self._main_menu = None

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

    def register_extensions(self):
        """
        Register specific extensions for this DCC
        This function should be override in specific DCC plugin implementation
        Is not an abstract function because its implementation is not mandatory
        """

        dcc_extensions = dcc.extensions()
        if not dcc_extensions:
            return

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            logger.log_warning(
                'Artella Drive was not initialized. Impossible to register extensions: {}'.format(dcc_extensions))
            return

        artella_drive_client.register_extensions(dcc_extensions)

    def init(self):
        """
        Initializes Artella plugin in current DCC
        :return: True if the initialization was successful; False otherwise
        :rtype: bool
        """

        # Initialize Artella callbacks
        self.setup_callbacks()

        # Create Artella DCC Menu
        self.create_menus()

        artella_drive_client = self.get_client()
        if artella_drive_client:
            artella_drive_client.artella_drive_listen()
            self.setup_project(artella_drive_client.get_local_root())
        else:
            logger.log_warning(
                'Artella Drive Client was not initialized. Artella server '
                'dependant functionality will not be available!')

        return True

    def shutdown(self):
        """
        Shutdown/Uninitialize Artella plugin in current DCC
        :return: True if the shutdown was successful; False otherwise
        :rtype: bool
        """

        # Remove Artella callbacks
        self.remove_callbacks()

        # Remove Artella DCC Menu
        self.remove_menus()

        # Finish Artella Drive Client thread
        if self._artella_drive_client:
            self._artella_drive_client.artella_drive_disconnect()
            self._artella_drive_client = None

        return True

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

        artella_menu = dcc.add_menu(self.MENU_NAME)
        if not artella_menu:
            return False

        self._main_menu = artella_menu

        # dcc.add_menu_item(
        #     menu_item_name='Save to Cloud',
        #     menu_item_command='import artella; artella.DccPlugin().make_new_version(show_dialogs=True)',
        #     parent_menu=artella_menu)
        # dcc.add_menu_item(
        #     menu_item_name='Get Dependencies',
        #     menu_item_command='import artella; artella.DccPlugin().get_dependencies(show_dialogs=True)',
        #     parent_menu=artella_menu)

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

        import artella.core.callback as callback

        callback.initialize_callbacks()

    def remove_callbacks(self):
        """
        Removes all DCC Artella callbacks previously created
        :return:
        """

        import artella.core.callback as callback

        callback.uninitialize_callbacks()

    def validate_environment_for_callback(self, callback_name):
        """
        Checks that all necessary parts are available before executing a Maya callback

        :param str callback_name: name of the callback to validate
        """

        logger.log_info('validate_environment_for_callback for {}'.format(callback_name))
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

    def get_client(self):
        """
        Returns current Artella Drive Client being used by Artella Plugin

        :return: Instance of current ArtellaDriveClient being used; None if not Artella Drive Client is being used.
        :rtype: ArtellaDriveClient or None
        """

        if not self._artella_drive_client:
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

        logger.log_debug('Passing message to {}: {}'.format(dcc.name(), json_data))
        dcc.pass_message_to_main_thread(self.handle_message, json_data)

    def handle_message(self, msg):
        """
        Internal function that handles the response received from Artella Drive App

        :param dict msg: Dictionary containing the response from Artella server
        """

        logger.log_debug('Handling realtime message: {}'.format(msg))
        if not isinstance(msg, dict):
            logger.log_warning('Malformed realtime message: {}'.format(msg))
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
            logger.log_debug('websocket connection successful.')
        elif command_name == 'open':
            file_path = msg['data']['ARTELLA_FILE']
            self._handle_open_message(file_path)
        else:
            pass

    def artella_info(self):
        """
        Function that prints useful information related with current Artella Plugin status
        """

        logger.log_info('Artella Plugin Status Info ...')
        artella_drive_client = self.get_client()
        logger.log_info(artella_drive_client.get_metadata())
        logger.log_info(artella_drive_client.get_storage_id())
        logger.log_info(artella_drive_client.ping())
        logger.log_info(artella_drive_client.artella_drive_connect())
        logger.log_info('Local Root: {}'.format(artella_drive_client.get_local_root()))

    # ==============================================================================================================
    # FILE PATHS
    # ==============================================================================================================

    def local_path_to_uri(self, file_path, prefix=None):
        """
        Translates a local file path to its URI format
        :param str file_path: Absolute local file path we want to translate to URI
        :param str prefix:

        :return: path in its URI format if current DCC supports this feature; path without any change otherwise
        :rtype: str
        """

        if prefix:
            # TODO: (dave): Handle TCL based path strings from Pixar nodes
            raise NotImplementedError('Support for TCL not implemented yet!')

        if not dcc.supports_uri_scheme():
            logger.log_warning('Current DCC {} does not supports Artella URI scheme!'.format(dcc.name()))
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

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return file_path

        return artella_drive_client.translate_path(file_path)

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

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return file_path

        return artella_drive_client.convert_path(file_path)

    def update_paths(self, file_path=None, show_dialogs=True, call_post_function=True, skip_save=True):
        """
        Updates all file paths of the given file path to make sure that they point to valid Artella file paths
        :param file_path:
        :param show_dialogs:
        :param call_post_function:
        :param skip_save:
        :return:
        """

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return False

        if not file_path:
            file_path = dcc.scene_name()
        if not file_path:
            msg = 'No file paths given to convert. Impossible to update paths.'
            logger.log_warning(msg)
            if show_dialogs:
                dcc.show_warning(title='Artella - Failed to update paths', message=msg)
            return False

        file_paths = utils.force_list(file_path, remove_duplicates=True)

        for file_path in file_paths:

            local_path = artella_drive_client.translate_path(file_path)

            ext = os.path.splitext(local_path)[-1]
            if ext not in dcc.extensions() or not os.path.isfile(local_path):
                logger.log_info('Skipping non DCC scene file path from conversion: "{}"'.format(local_path))
                continue

            can_lock = artella.DccPlugin().can_lock_file(local_path, show_dialogs=False)
            if not can_lock:
                logger.log_warning(
                    'File "{}" cannot be locked and paths cannot be updated. Skipping ...'.format(local_path))
                continue

            if dcc.scene_name() != file_path:
                dcc.open_scene(file_path, save=True)

            parser = artella.Parser()
            valid_convert = parser.update_paths(local_path)

            if valid_convert and not skip_save:
                dcc.save_scene()

        if call_post_function:
            self._post_update_paths()

    # ==============================================================================================================
    # VERSIONS
    # ==============================================================================================================

    def make_new_version(self, file_path=None, comment=None):
        """
        Uploads a new file/folder or a new version of current opened DCC scene file

        :param str file_path: Optional path of the file we want to create new version of. If not given, current
            opened DCC scene file path will be used.
        :param str comment: Optional comment to add to new version metadata. If not given, a generic message will be
            used.
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
                logger.log_warning(msg)
                return False

        can_lock = artella_drive_client.can_lock_file(file_path=file_path)
        if not can_lock:
            msg = 'Unable to lock file to make new version. File is already locked by other user.'
            dcc.show_error('File already locked by other user', msg)
            logger.log_error(msg)
            return False

        version_created = True

        comment = str(comment) if comment else 'New file version'

        file_version = artella_drive_client.file_current_version(file_path)
        next_version = file_version + 1

        is_locked, _, _, _ = artella_drive_client.check_lock(file_path)

        if not is_locked:
            valid_lock = self.lock_file()
            if not valid_lock:
                msg = 'Unable to lock file to make new version ({})'.format(next_version)
                logger.log_error(msg)
                return False

        logger.log_info('Saving current scene: {}'.format(file_path))
        valid_save = dcc.save_scene()
        if not valid_save:
            logger.log_error('Unable to save current scene: "{}"'.format(file_path))
            version_created = False
        else:
            uri_path = self.local_path_to_uri(file_path)
            rsp = artella_drive_client.upload(uri_path, comment=comment)
            if rsp.get('error'):
                msg = 'Unable to upload a new version of file: "{}"\n{}\n{}'.format(
                    os.path.basename(file_path), rsp.get('url'), rsp.get('error'))
                version_created = False

        if not is_locked:
            self.unlock_file(show_dialogs=False)

        return version_created

    # ==============================================================================================================
    # LOCK/UNLOCK STATUS
    # ==============================================================================================================

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

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return False

        if not file_path:
            file_path = dcc.scene_name()
        if not file_path:
            msg = 'File "{}" does not exists. Impossible to check lock status!'.format(file_path)
            logger.log_warning(msg)
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

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return False

        if not file_path:
            file_path = dcc.scene_name()
            if not file_path:
                msg = 'Unable to get file name, has it been created!?'
                logger.log_warning(msg)
                if show_dialogs:
                    dcc.show_warning(title='Artella - Failed to lock file', message=msg)
                return False

        if not file_path or not os.path.isfile(file_path):
            msg = 'File "{}" does not exists. Impossible to lock.'.format(file_path)
            logger.log_warning(msg)
            if show_dialogs:
                dcc.show_error('Artella - Failed to lock File', msg)
            return False

        file_version = artella_drive_client.file_current_version(file_path)
        if file_version <= 0:
            logger.log_info('File "{}" is not versioned yet. No need to lock.'.format(file_path))
            return True

        is_locked, is_locked_by_me, is_locked_by_name, remote_record_found = artella_drive_client.check_lock(file_path)
        can_write = os.access(file_path, os.W_OK)
        if not can_write and is_locked_by_me:
            logger.log_warning('Unable to determine local write permissions for file: "{}"'.format(file_path))
        if is_locked and not is_locked_by_me:
            msg = 'This file is locked by another user ({}). The file must be unlocked in order to save a new version.'
            logger.log_warning(msg)
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
            logger.log_warning(msg)
            dcc.show_warning('Artella - Failed to lock file', msg)
            return False

        return True

    def unlock_file(self, file_path=None, show_dialogs=True):
        """
        Unlocks given file path in Artella Drive.

        :param str or None file_path: Absolute local file path we want to lock. If not given, current DCC scene file
            will be unlocked.
        :param bool show_dialogs: Whether UI dialogs should appear or not.
        :return: True if the lock operation was successful; False otherwise
        :rtype: bool
        """

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return False

        if not file_path:
            file_path = dcc.scene_name()
            if not file_path:
                msg = 'Unable to get file name, has it been created!?'
                logger.log_warning(msg)
                if show_dialogs:
                    dcc.show_warning(title='Artella - Failed to lock file', message=msg)
                return False

        if not file_path or not os.path.isfile(file_path):
            msg = 'File "{}" does not exists. Impossible to unlock.'.format(file_path)
            logger.log_warning(msg)
            if show_dialogs:
                dcc.show_error('Artella - Failed to unlock file', msg)
            return False

        result = True
        if show_dialogs:
            msg = 'You have file "{}" locked in Artella.\nUnlock it now?'.format(os.path.basename(file_path))
            result = dcc.show_question('Artella - Unlock File', msg, cancel=False)
        if result is not True:
            return False

        uri_path = self.local_path_to_uri(file_path)
        valid_unlock = artella_drive_client.unlock_file(uri_path)
        if not valid_unlock:
            msg = 'Failed to unlock the file: "{}"\nTry unlocking it from the Artella ' \
                  'Drive area in the web browser'.format(os.path.basename(file_path))
            logger.log_warning(msg)
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

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return False

        local_path = artella_drive_client.translate_path(file_path)

        dcc_progress_bar = artella.ProgressBar()
        dcc_progress_bar.start()

        artella_drive_client.download(local_path)
        time.sleep(1.0)

        valid_download = True
        while True:
            if show_dialogs:
                if dcc_progress_bar.is_cancelled():
                    artella_drive_client.pause_downloads()
                    valid_download = False
                    break
            progress, fd, ft, bd, bt = artella_drive_client.get_progress()
            progress_status = '{} of {} KiB downloaded\n{} of {} files downloaded'.format(
                    int(bd / 1024), int(bt / 1024), fd, ft)
            if show_dialogs:
                dcc_progress_bar.set_progress_value(value=progress, status=progress_status)
            if progress >= 100 or bd == bt:
                break

        dcc_progress_bar.end()

        return valid_download

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


@utils.Singleton
class ArtellaDccPluginSingleton(ArtellaDccPlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaDccPlugin.__init__(self, artella_drive_client=artella_drive_client)


register.register_class('DccPlugin', ArtellaDccPluginSingleton)
