#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for artella
"""

from __future__ import print_function, division, absolute_import

import os
import sys


def init(init_client=True, plugin_paths=None, extensions=None):
    """
    Initializes Artella Plugin

    :param bool init_client: Whether or not Artella Drive Client should be initialized during initialization.
        Useful to avoid to connect to Artella client when developing DCC specific functionality.
    :return: True if Artella initialization was successful; False otherwise.
    :rtype: bool
    """

    import artella
    from artella import dcc
    from artella.core import dcc as core_dcc
    from artella.core import client
    from artella.core import plugin     # Import to force the creation of Plugins Manager

    plugins_path = plugin_paths if plugin_paths is not None else list()
    extensions = extensions if extensions is not None else list()

    # Make sure that Artella Drive client and DCC are cached during initialization
    core_dcc.current_dcc()

    # Specific DCC extensions are managed by the client
    dcc_extensions = dcc.extensions()
    extensions.extend(dcc_extensions)

    artella_drive_client = client.ArtellaDriveClient.get(extensions=extensions) if init_client else None
    artella.DccPlugin(artella_drive_client).init()

    artella.PluginsMgr().register_paths(plugin_paths)
    artella.PluginsMgr().load_registered_plugins()

    return True


def shutdown():
    """
    Shutdown Artella Plugin

    :return: True if Artella shutdown was successful; False otherwise.
    :rtype: bool
    """

    import artella
    from artella.core import dcc
    from artella.core import plugin     # Import to force the creation of Plugins Manager

    # Make sure that Artella Drive client and DCC are cached during initialization
    dcc.current_dcc()

    artella.PluginsMgr().shutdown()
    artella.DccPlugin().shutdown()

    return True


def _reload():
    """
    Function to be used during development. Can be used to "reload" Artella modules.
    Useful when working inside DCC envs.
    """

    # Make sure that DCC and its related modules are imported before doing the reload
    # current_dcc()

    # We make sure that plugin is shutdown before doing reload
    shutdown()

    to_clean = [m for m in sys.modules.keys() if 'artella' in m]
    for t in to_clean:
        os.sys.modules.pop(t)

    global CURRENT_DCC
    CURRENT_DCC = None
