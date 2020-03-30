#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constants definitions used by Artella Drive
"""

from __future__ import print_function, division, absolute_import

# Defines Local Environment Variable that sets Artella root folder location
# This is used as fallback when ArtellaApp/URI is not available
ALR = 'ARTELLA_FOLDER_ROOT'

# Defines Local Environment Variable that sets Artella External DCCs location
# This is used to register custom DCC implementations
AED = 'ARTELLA_EXTERNAL_DCCS'

# Defines package namespace where Artella DCC plugins are located
ARTELLA_DCC_NAMESPACE = 'artella.dcc'

# Defines URI scheme used by Artella
ARTELLA_URI_SCHEME = 'artella'

# Defines default IP host used by the client
DEFAULT_HOST = '127.0.0.1'

# Defines default port used by the client
DEFAULT_PORT = 29282

# Defines authentication header
AUTH_HEADER = 'artella-file-challenge artella-challenge {}'

# Defines default note used by lock operation
DEFAULT_LOCK_NOTE = 'Lock for use by plugin'

# Control codes CL/RF to create new lines.
CRLF = "\r\n"
