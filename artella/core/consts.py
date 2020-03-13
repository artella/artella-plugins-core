#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constants definitions used by ArtellaApp
"""

# Defines Local Environment Variable that defines Artella root folder location
# This is used as fallback when ArtellaApp/URI is not available
ALR = 'ARTELLA_FOLDER_ROOT'

# Defines URI scheme used by Artella
ARTELLA_URI_SCHEME = 'artella'

# Defines default IP host used by the client
DEFAULT_HOST = '127.0.0.1'

# Defines default port used by the client
DEFAULT_PORT = 29282

# Defines authentication header
AUTH_HEADER = 'artella-file-challenge artella-challenge {}'
