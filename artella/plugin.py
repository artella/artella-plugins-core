#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella Plugin functionality
"""

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
        dcc.add_menu_item(menu_item_name='Save to Cloud', menu_item_command='import artella; print(artella.Plugin().ping())', parent_menu=artella_menu)
        dcc.add_menu_item(menu_item_name='Get Dependencies', menu_item_command='', parent_menu=artella_menu)
        dcc.add_menu_item(menu_item_name='Convert File Paths', menu_item_command='', parent_menu=artella_menu)

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

        :param json_data:
        :return:
        """

        pass

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
        elif command_name in ['version-check', 'progress-summary']:
            pass
        else:
            artella.log_warning('unknown command on websocket: {}'.format(command_name))

    def ping(self):
        """
         Test call that returns whether the Artella Drive is valid or not

         :return: Returns a success response or auth failure message
         :rtype: dict
         """

        artella_drive_client = self.get_client()

        return artella_drive_client.ping()

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


artella.register_class('Plugin', ArtellaPlugin)
