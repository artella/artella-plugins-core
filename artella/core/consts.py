#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constants definitions used by Artella Drive
"""

from __future__ import print_function, division, absolute_import

# Defines Local Environment Variable that sets Artella root folder location
# This is used as fallback when ArtellaApp/URI is not available
ALR = 'ART_LOCAL_ROOT'

# Defines Local Environment Variables used in old Artella versions
OLD_LOCAL_ROOTS = ['AM_LOCAL_ROOT', 'AM_LOCAL_STORAGE_TOP']

# Defines Local Environment Variable that sets Artella External DCCs location
# This is used to register custom DCC implementations
AED = 'ARTELLA_EXTERNAL_DCCS'

# Defines package namespace where Artella DCC plugins are located
ARTELLA_DCCS_NAMESPACE = 'artella.dccs'

# Defines URI scheme used by Artella
ARTELLA_URI_SCHEME = 'artella'

# Defines default IP host used by the client
DEFAULT_HOST = '127.0.0.1'

# Defines default port used by the client
DEFAULT_PORT = 29282

# Defines default buffer size for web socket requests to Artella Drive App
DEFAULT_BUFFER_SIZE = 2000

# Defines the file name used by Artella Drive App to store project specific metadata
PROJECT_METADATA_FILE = '.artella-folder.yaml'

# Defines authentication header
AUTH_HEADER = 'artella-file-challenge artella-challenge {}'

# Defines default note used by lock operation
DEFAULT_LOCK_NOTE = 'Lock for use by plugin'

# Control codes CL/RF to create new lines.
CRLF = "\r\n"

# Configuration file for Artella Plugins
ARTELLA_PLUGIN_CONFIG = 'artella-plugin.json'
