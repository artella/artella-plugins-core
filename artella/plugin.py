#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella Plugin functionality
"""

from __future__ import print_function, division, absolute_import

import os

import artella
import artella.dcc as dcc
from artella.core.utils import abstract, Singleton


class ArtellaPlugin(object):

    MENU_NAME = 'Artella'

    def __init__(self, artella_drive_client):
        super(ArtellaPlugin, self).__init__()

        self._artella_drive_client = artella_drive_client

    # ==============================================================================================================
    # INITIALIZATION / SHUTDOWN
    # ==============================================================================================================

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
        artella_drive_client.artella_drive_listen()

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
        dcc.add_menu_item(
            menu_item_name='Save to Cloud',
            menu_item_command='import artella; artella.Plugin().make_new_version()', parent_menu=artella_menu)
        dcc.add_menu_item(
            menu_item_name='Get Dependencies',
            menu_item_command='import artella; artella.Plugin().get_dependencies()', parent_menu=artella_menu)

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

        artella.log_debug('Passing message to {}: {}'.format(dcc.name(), json_data))
        dcc.pass_message_to_main_thread(self.handle_message, json_data)

    def handle_message(self, msg):
        """
        Internal function that handles the response received from Artella Drive App

        :param dict msg: Dictionary containing the response from Artella server
        """

        artella.log_debug('Handling realtime message: {}'.format(msg))
        if not isinstance(msg, dict):
            artella.log_warning('Malformed realtime message: {}'.format(msg))
            return

        command_name = msg.get('type')

        if command_name == 'authorization-ok':
            artella.log_info('websocket connection successful.')
        elif command_name in ['version-check', 'progress-summary', 'transfer-status-change']:
            pass
        else:
            artella.log_warning('unknown command on websocket: {}'.format(command_name))

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
            artella.log_warning('Current DCC {} does not supports Artella URI scheme!'.format(dcc.name()))
            return file_path

        return file_path

    def ping(self):
        """
         Test call that returns whether the Artella Drive is valid or not

         :return: Returns a success response or auth failure message
         :rtype: dict
         """

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return dict()

        return artella_drive_client.ping()

    def get_version_comment(self, current_file):
        """
        Retrieves comment version in a DCC specific way.
        This class can be override to retrieve the version comment on different ways

        :param str current_file: Absolute local file path we want to create new comment for
        :return: Typed comment write by the user
        :rtype: str
        """

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return False

        file_version = artella_drive_client.file_current_version(current_file)[0]
        next_version = file_version + 1
        comment, ok = dcc.input_comment(
            'Artella - Save to Cloud', 'Saving {} (version {})\n\nComment:'.format(
                os.path.basename(current_file), next_version))
        if not ok:
            artella.log_info('Cancelled Save to Cloud operation by user.')
            return False

        return comment

    def make_new_version(self, show_dialogs=False):
        """
        Uploads a new file/folder or a new version of current opened DCC scene file

        :param bool show_dialogs: Whether UI dialogs should appear or not.
        :return: True if the operation was successful; False otherwise
        :rtype: bool
        """

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return False

        current_file = dcc.scene_name()
        if not current_file:
            msg = 'Unable to get file name, has it been created!?'
            artella.log_warning(msg)
            if show_dialogs:
                dcc.show_warning(title='Artella Failed to make new version', message=msg)
            return False

        can_lock = self.can_lock_file(show_dialogs=False)
        if not can_lock:
            artella.log_error('Unable to lock file to make new version')
            return False

        comment = self.get_version_comment(current_file=current_file)

        file_version = artella_drive_client.file_current_version(current_file)[0]
        next_version = file_version + 1
        valid_lock = self.lock_file()
        if not valid_lock:
            msg = 'Unable to lock file to make new version ({})'.format(next_version)
            artella.log_error('Unable to lock file to make new version')
            if show_dialogs:
                dcc.show_error('Artella - Failed to make new version', msg)
            return False

        artella.log_info('Saving current scene: {}'.format(current_file))
        valid_save = dcc.save_scene()
        if not valid_save:
            artella.log_error('Unable to save current scene: "{}"'.format(current_file))
            return False

        uri_path = self.local_path_to_uri(current_file)
        rsp = artella_drive_client.upload(uri_path, comment=comment)
        if rsp.get('error'):
            msg = 'Unable to upload a new version of file: "{}"\n{}\n{}'.format(
                os.path.basename(current_file), rsp.get('url'), rsp.get('error'))
            dcc.show_error('Artella - Failed to make new version', msg)
            return False

        self.unlock_file(show_dialogs=False)

        return True

    def can_lock_file(self, show_dialogs=True):
        """
        Returns whether or not current opened DCC file can locked or not
        A file only can be locked if it is not already locked by other user.

        :param bool show_dialogs: Whether UI dialogs should appear or not.
        :return: True if the file can be locked by current user; False otherwise.
        :rtype: bool
        """

        artella_drive_client = self.get_client()
        if not artella_drive_client:
            return False

        current_file = dcc.scene_name()
        if not current_file:
            msg = 'Unable to get file name, has it been created!?'
            artella.log_warning(msg)
            if show_dialogs:
                dcc.show_warning(title='Artella - Failed to lock file', message=msg)
            return False

        file_version = artella_drive_client.file_current_version(current_file)
        if not file_version:
            return False

        file_version = file_version[0]
        if file_version <= 0:
            artella.log_info('File "{}" is not versioned yet. No need to lock.'.format(current_file))
            return True

        is_locked, is_locked_by_me, is_locked_by_name = artella_drive_client.file_is_locked(current_file)

        if not is_locked or (is_locked and is_locked_by_me):
            return True

        return False

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
                artella.log_warning(msg)
                if show_dialogs:
                    dcc.show_warning(title='Artella - Failed to lock file', message=msg)
                return False

        if not file_path or not os.path.isfile(file_path):
            msg = 'File "{}" does not exists. Impossible to lock.'.format(file_path)
            artella.log_warning(msg)
            if show_dialogs:
                dcc.show_error('Artella - Failed to lock File', msg)
            return False

        file_version = artella_drive_client.file_current_version(file_path)[0]
        if file_version <= 0:
            artella.log_info('File "{}" is not versioned yet. No need to lock.'.format(file_path))
            return True

        is_locked, is_locked_by_me, is_locked_by_name = artella_drive_client.file_is_locked(file_path)
        can_write = os.access(file_path, os.W_OK)
        if not can_write and is_locked_by_me:
            artella.log_warning('Unable to determine local write permissions for file: "{}"'.format(file_path))
        if is_locked and not is_locked_by_me:
            msg = 'This file is locked by another user ({}). The file must be unlocked in order to save a new version.'
            artella.log_warning(msg)
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
            artella.log_warning(msg)
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
                artella.log_warning(msg)
                if show_dialogs:
                    dcc.show_warning(title='Artella - Failed to lock file', message=msg)
                return False

        if not file_path or not os.path.isfile(file_path):
            msg = 'File "{}" does not exists. Impossible to unlock.'.format(file_path)
            artella.log_warning(msg)
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
            artella.log_warning(msg)
            if show_dialogs:
                dcc.show_error('Artella - Failed to unlock file', msg)
            return False

        return True

    def get_dependencies(self):
        """
        Downloads from Artella server the latest versions available of all current DCC dependencies files
        """

        dcc.show_info('Artella - Get Dependencies', 'Get Dependnecies functionality is not implemented yet!')

        return False

    # ==============================================================================================================
    # ABSTRACT
    # ==============================================================================================================

    @abstract
    def register_uri_resolver(self):
        """
        Function that registers DCC specific Artella URI resolver
        This function must be implemented in those DCCs that support this feature
        """

        pass


@Singleton
class ArtellaPluginSingleton(ArtellaPlugin, object):
    def __init__(self, artella_drive_client=None):
        ArtellaPlugin.__init__(self, artella_drive_client=artella_drive_client)


artella.register_class('Plugin', ArtellaPluginSingleton)
