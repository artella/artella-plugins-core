#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive Python client implementation
"""

from __future__ import print_function, division, absolute_import

import os
import json
import time
import codecs
import socket
import base64
import random
import hashlib
import logging
import threading
import traceback
from collections import OrderedDict
try:
    from urllib.parse import urlparse, urlencode, urlunparse
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urlparse import urlparse, urlunparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError, URLError

from artella import dcc
from artella.core import consts, utils, exceptions, dccplugin

logger = logging.getLogger('artella')


class ArtellaDriveClient(object):
    """
    Class used to interact with ArtellaDrive application on client side
    """

    _challenge_path = None

    def __init__(self, host=consts.DEFAULT_HOST, port=consts.DEFAULT_PORT, extensions=None):
        self._host = host               # Contains default IP host used by the client.
        self._port = port               # Contains default port used by the client.
        self._auth_header = ''          # Contains authentication header read from challenge file.
        self._remote_sessions = list()  # Contains list of available remote sessions.
        self._local_projects = dict()   # Contains dictionary of all available user local Artella projects.
        self._remote_projects = dict()  # Contains a dictionary of all available user remote Artella projects.
        self._batch_ids = set()         # Contains a list that tracks all calls made to the client during a session.
        self._socket_buffer = None      # Contains instance of the socket buffer used to communicate with Artella App.
        self._running = False           # Flag that is True while Artella Drive thread is running.
        self._available = True          # Flag that is True while Artella Drive is available.
        self._exception = None          # Contains exception caused while Artella Drive is running.
        self._extensions = extensions   # Contains a list with all extensions managed by the client.
        self._client_thread = None      # Contains Python client thread

    # ==============================================================================================================
    # PROPERTIES
    # ==============================================================================================================

    @property
    def is_running(self):
        """
        Returns whether or not current Artella Drive thread is running.
        While Artella Drive thread is running, it listens responses from Artella Drive

        :return: True if the Artella Drive thread is running; False otherwise.
        :rtype: bool
        """

        return self._running

    @property
    def is_available(self):
        """
        Returns whether or not current Artella Drive client is available.
        Artella Drive Client is not available, for example, is the user closes Artella Drive App manually.

        :return: True if Artella Drive Client is available; False otherwise.
        :rtype: bool
        """

        return self._available

    # ==============================================================================================================
    # CLASS FUNCTIONS
    # ==============================================================================================================

    @classmethod
    def get(cls, extensions=None):
        """
        Returns a new instance of ArtellaDriveClient making sure that authorization is valid

        :param list(str) extensions: List of extensions
        :return: New instance of Artella Drive object
        :rtype: ArtellaDriveClient
        """

        artella_client = cls(extensions=extensions)

        # Challenge value gets updated when the Artella drive restarts.
        # We need to check this each time in case the local server got restarted
        auth_header = artella_client.update_auth_challenge()
        if not auth_header:
            logger.warning('Local Artella Drive is not available. Please launch Artella Drive App.')
            return None

        # Updates the list of available remotes
        artella_client.update_remotes_sessions(show_dialogs=False)

        return artella_client

    # ==============================================================================================================
    # CHALLENGE FILE
    # ==============================================================================================================

    def check(self, update=False):
        """
        Checks whether or not current client is available and running

        :param update: bool, Whether or not remote sessions should be updated
        :return: True if the client is available and running; False otherwise.
        :rtype: bool
        """

        return self._available and self._running and self.get_remote_sessions(update=update)

    def get_challenge_file_path(self):
        """
        Returns path where challenge file is located in local desktop machine

        :return: dictionary containing challenge file path
        :rtype: dict
        :example:
        >>> self.get_challenge_file_path()
        {
            "challenge_file_path": "C:\\users\\artella\\Application Data\\artella\\artella-challenge"
        }
        """

        req = Request('http://{}:{}/v2/localserve/auth/challenge-file-path'.format(self._host, self._port))
        rsp = self._communicate(req, skip_auth=True)

        return rsp

    def update_auth_challenge(self):
        """
        Collects some data from a local file to confirm we are running on the same that Artella drive is running.

        :return: string containing authentication header for current session or None if authentication was invalid
        :rtype: str or None
        """

        if not ArtellaDriveClient._challenge_path:
            rsp = self.get_challenge_file_path()
            if not rsp or 'error' in rsp:
                logger.error('Unable to get challenge file path "{}"'.format(rsp))
                self._auth_header = None
                return self._auth_header
            ArtellaDriveClient._challenge_path = rsp.get('challenge_file_path')

        if not os.path.exists(ArtellaDriveClient._challenge_path):
            logger.error('Challenge file not found: "{}"'.format(ArtellaDriveClient._challenge_path))
            self._auth_header = None
            return self._auth_header

        with open(os.path.expanduser(ArtellaDriveClient._challenge_path), 'rb') as fp:
            base_auth_header = fp.read()

        self._auth_header = consts.AUTH_HEADER.format(codecs.encode(base_auth_header[:64], 'hex').decode('ascii'))

        return self._auth_header

    def has_remote_sessions(self):
        """
        Returns whether or not current Artella Drive Client has remote sessions available or not
        :return: bool
        """

        return self._remote_sessions and len(self._remote_sessions) > 0

    def get_remote_sessions(self, update=False):
        """
        Returns a list with all available remote sessions

        :return: List of cached remote sessions in current Artella Drive Client
        :rtype: list(str)
        """

        if not self._remote_sessions and update:
            self.update_remotes_sessions()

        return self._remote_sessions

    def update_remotes_sessions(self, show_dialogs=True):
        """
        Collects all available remote servers available.

        :return: List of available remote sessions received from Artella Drive App.
        :rtype: list(str)
        """

        def _ping_remote_sessions():
            rsp = self.ping()
            if 'error' in rsp:
                msg = 'Attempting to retrieve remote sessions: "{}" '.format(rsp.get('error'))
                logger.error(msg)
            self._remote_sessions = rsp.get('remote_sessions', list())

        utils.clear_list(self._remote_sessions)

        if not self.update_auth_challenge():
            msg = 'Unable to authenticate to Artella Drive App.'
            logger.error(msg)
            if show_dialogs:
                dcc.show_error('Artella - Authentication error', msg)
            return

        _ping_remote_sessions()

        # If not remote sessions found, we recheck after 1 second to make sure Artella Drive App is running.
        if not self._remote_sessions:
            time.sleep(1)
            _ping_remote_sessions()
            if not self._remote_sessions:
                msg = 'No remote sessions available. Please visit your Project Drive in Artella Web App and try again!'
                logger.error(msg)

        return self._remote_sessions

    # ==============================================================================================================
    # SESSION
    # ==============================================================================================================

    def get_storage_id(self):
        """
        Returns storage ID of the machine this client is running on

        :return: ID indicating this desktop instance
        :rtype: str
        :example:
        >>> self.get_storage_id()
        "d7apalzl2rdnphe5wuccytqq3i"
        """

        req = Request('http://{}:{}/v2/localserve/kv/settings/machine-id'.format(self._host, self._port))
        storage_id = self._communicate(req)

        return storage_id

    def get_metadata(self):
        """
        Returns general data related with current session by asking remote server

        :return: Returns a dictionary containing all keys and values in kv namespace
        :rtype: dict
        :example:
        >>> self.get_metadata()
        {
            "machine-id": "d7apalzl2rdnphe5wuccytqq3i",
            "workspace": "C:/Users/artella/artella-files",
            "openers.log": "C:/Users/artella/AppData/Roaming/artella/openers.log"
        }
        """

        params = urlencode({'dump': 'true'})
        req = Request('http://{}:{}/v2/localserve/kv/settings?{}'.format(self._host, self._port, params))
        rsp = self._communicate(req)

        return rsp

    # ==============================================================================================================
    # PROJECTS
    # ==============================================================================================================

    def get_local_projects(self, force_update=False):
        """
        Returns all available project files found in the local user machine

        :param bool force_update: Whether to force the cache of the current available local projects
        :return: List of dictionaries containing all the information of the current available
        Artella on local user machine projects
        :rtype: dict(str, dict(str, str))
        """

        if self._local_projects and not force_update:
            return self._local_projects

        local_root = self.get_local_root()
        if not local_root or not os.path.isdir(local_root):
            logger.warning(
                'Impossible to retrieve current available projects because local root is not valid: {}'.format(
                    local_root))
            return list()

        project_files = utils.get_files(local_root, pattern=consts.PROJECT_METADATA_FILE)

        for project_file in project_files:
            project_dir = os.path.dirname(project_file)
            project_name = os.path.basename(project_dir)
            self._local_projects.setdefault(project_name, None)
            with open(project_file, 'r') as fh:
                lines = fh.readlines()
                project_data = {
                    'directory': project_dir
                }
                for line in lines:
                    line_split = line.split(': ')
                    if not line_split:
                        continue
                    project_data[line_split[0]] = line_split[1].strip()
                if project_data:
                    self._local_projects[project_name] = project_data

        return self._local_projects

    def get_remote_projects(self, force_update=False):
        """
        Returns all available projects in Artella

        :param bool force_update: Whether to force the cache of the current available remote projects
        :return: Dictionary that contains all projects for each one of the available remote sessions
        :rtype: dict(str, list(str))
        """

        if self._remote_projects and not force_update:
            return self._remote_projects

        if not self._remote_sessions:
            return dict()

        for remote_session in self._remote_sessions:
            remote_session_api = remote_session.get('api', None)
            if not remote_session_api:
                continue
            remote_session_projects = remote_session.get('projects', dict())
            self._remote_projects[remote_session_api] = remote_session_projects

        return self._remote_projects

    def get_project_name(self, project_id, remote_session=None):
        """
        Returns the project name giving its remote Artella ID

        :param str project_id: ID of the project in remote Artella server
        :param str remote_session: Remote session we want to search project on. If not given, the project will be
            search in all available remote sessions
        :return: Name of the project
        :rtype: str
        """

        remote_projects = self.get_remote_projects()
        if not remote_projects:
            logger.warning('No remote projects available to search project name for: "{}"'.format(project_id))
            return ''

        project_name = ''
        if remote_session:
            if remote_session not in remote_projects:
                logger.warning(
                    'Given remote session: "{}" is not available. Impossible to retrieve name for project: "{}"'.format(
                        remote_session, project_id))
                return project_name

            if project_id not in remote_projects[remote_session]:
                logger.warning('Project ID "{}" not found in remote session: "{}"'.format(
                    project_id, remote_session))
                return project_name

            project_name = remote_projects[remote_session][project_id].get('name', '')
        else:
            for remote_id, remote_data in remote_projects.items():
                for remote_project_id, project_data in remote_data.items():
                    if project_id != remote_project_id:
                        continue
                    project_name = project_data.get('name', '')
                    break

        if not project_name:
            logger.warning('No project name found for project: "{}"'.format(project_id))

        return project_name

    # ==============================================================================================================
    # PATHS
    # ==============================================================================================================

    def is_artella_path(self, file_path):
        """
        Returns whether or not given file path is an Artella file path or not
        A path is considered to be an Artella path if the path is located inside the Artella project folder
        in the user machine

        :param str file_path: path to check. If not given, current DCC scene file path will be used
        :return: True if the given file path is an Artella path; False otherwise.
        :rtype: bool
        """

        if not file_path or not os.path.exists(file_path):
            return False

        local_root = os.path.normpath(os.path.abspath(self.get_local_root()))
        file_path = os.path.normpath(os.path.abspath(file_path))

        return file_path.startswith(local_root)

    def get_local_root(self):
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

        req = Request('http://{}:{}/v2/localserve/kv/settings/workspace'.format(self._host, self._port))
        local_root = self._communicate(req)
        if not local_root or (isinstance(local_root, dict) and 'error' in local_root):
            alr = os.environ.get(consts.ALR, None)
            if alr:
                logger.warning('Unable to get local storage root. Using env var instead: "{}"'.format(consts.ALR))
                local_root = alr
            else:
                logger.error('Unable to get local storage root.')
                logger.info(
                    'Check that the local Artella Drive service is running and you have a working internet connection.')
                logger.info(
                    'To work offline set the "{}" environment variable to the proper local project directory'.format(
                        consts.ALR))
        else:
            local_root = utils.clean_path(local_root)
            os.environ[consts.ALR] = local_root

        return local_root

    def resolve_path(self, path):
        """
        Converts a local path to a remote handle path representation and vice versa

        :param str path: local path or remote server path
        :return: Returns a dictionary containing resolved path or error message is the path cannot be resolve
        :rtype: dict
        :example:
        >>> os.environ['ART_LOCAL_ROOT'] = "C:/Users/artella/artella-files"
        >>> self.resolve_path("ART_LOCAL_ROOT/project/refs/ref.png")
        {
            'handle': 'project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png',
            'file_path': u'C:\\Users\\artella\\artella-files\\project\\refs\\ref.png'
        }
        >>> self.resolve_path("artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png")
        {
            'handle': 'project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png',
            'file_path': u'C:\\Users\\artella\\artella-files\\project\\refs\\ref.png'
        }
        >>> self.resolve_path("C:/Users/artella/artella-files/project/refs/ref.png")
        {
            'handle': 'project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png',
            'file_path': 'C:\\Users\\artella\\artella-files\\project\\refs\\ref.png'
        }
        >>> self.resolve_path("C:/Invalid/Path/ref.png")
        {
            'url': 'http://127.0.0.1:29282/v2/localserve/resolve',
            'error': 'Failed to reach the local ArtellaDrive: "Bad Request"'
        }
        """

        # We set request object depending whether given path is an URI one or not
        if is_uri_path(path):
            payload = {'handle': path}
        else:
            payload = {'file_path': path}

        req = Request('http://{}:{}/v2/localserve/resolve'.format(self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload).encode())
        if 'error' in rsp:
            logger.error('Attempting to resolve "{}" "{}"'.format(path, rsp.get('error')))

        return rsp

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
        >>> self.translate_path("$ART_LOCAL_ROOT/ProjectA/refs/ref.png")
        "C:/Users/Tomi/artella/data/ProjectA/refs/ref.png"
        """

        if is_uri_path(file_path):
            return self.resolve_path(file_path)

        path = file_path
        if not os.path.isabs(file_path):
            path = self.relative_path_to_absolute_path(file_path)
        path = utils.clean_path(os.path.expanduser(os.path.expandvars(path)))

        local_root = self.get_local_root()
        local_project_names = list((self.get_local_projects() or dict()).keys())

        for old_alr in consts.OLD_LOCAL_ROOTS:
            old_alr_str = '${}'.format(old_alr)
            if path.startswith(old_alr_str):
                path = utils.clean_path(path.replace(old_alr, local_root))
                path = path[1:] if path.startswith('$') else path

        path_split = path.split('/')
        total_chars = 0
        for split in path_split:
            if split in local_project_names:
                break
            total_chars += len(split) + 1

        common_path = path[total_chars:]
        translated_path = '{}/{}'.format(local_root, common_path)

        rsp = self.resolve_path(translated_path)
        if 'error' in rsp:
            logger.warning('Error while resolving translated file path: "{}"!'.format(path))
            return path

        if not translated_path.startswith(local_root):
            logger.warning('Was not possible to translate file path: "{}"!'.format(path))
            return path

        return translated_path

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

        if not file_path:
            return False

        return file_path.startswith('${}'.format(consts.ALR))

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

        local_root = self.get_local_root()

        path_to_convert = file_path
        if not os.path.isabs(file_path):
            path_to_convert = self.relative_path_to_absolute_path(file_path)
        translated_path = utils.clean_path(self.translate_path(path_to_convert))

        converted_path = translated_path
        if translated_path.startswith(local_root):
            converted_path = translated_path.replace(local_root, '${}'.format(consts.ALR))

        return converted_path
    
    def relative_path_to_absolute_path(self, relative_path, project_id=None):
        """
        Converts a relative path to an absolute local file path taking into account the given project id

        :param str relative_path: Relative path to a file
        :param str or None project_id: project id the relative path file belongs to
        :return: Absolute local file path of the relative path in the given project
        :rtype: str
        """

        if os.path.isabs(relative_path):
            return relative_path

        local_root = self.get_local_root()

        if not project_id:
            project_id = utils.split_path(relative_path)[0]

        local_project_names = self.get_local_projects() or dict()
        for project_name, project_data in local_project_names.items():
            if project_id == project_name:
                return utils.clean_path(os.path.join(local_root, relative_path))
            if project_id == project_data.get('remote', None):
                return utils.clean_path(os.path.join(local_root, project_name, relative_path))

        return relative_path

    def project_name_from_path(self, file_path):
        """
        Returns project name given file path belongs to. None if the path does not belongs to nay user local project.

        :param str file_path: path we want to retrieve project name of.
        :return: project name given path belongs to.
        :rtype: str
        """

        local_project_names = list((self.get_local_projects() or dict()).keys())

        project_name = None

        path_split = file_path.split('/')
        for split in path_split:
            if split in local_project_names:
                project_name = split
                break

        return project_name

    def project_id_from_path(self, file_path):
        """
        Returns project ID given file path belongs to. None if the path does not belongs to any user local project.

        :param str file_path: path we want to retrieve project ID of.
        :return: Project ID given path belongs to.
        :rtype: str
        """

        local_projects = self.get_local_projects() or dict()
        if not local_projects:
            logger.warning('No local projects available to retrieve project ID from path!')
            return None

        project_name = self.project_name_from_path(file_path)
        if not project_name:
            logger.warning('Was not possible to retrieve Project ID from path: {}!'.format(file_path))
            return None

        if project_name not in list(local_projects.keys()):
            logger.warning(
                'Was not possible to retrieve Project ID from path because project "{}" is not recognized!'.format(
                    project_name))
            return None

        project_data = local_projects[project_name]
        project_id = project_data.get('remote', None)

        return project_id

    # ==============================================================================================================
    # FILES/FOLDERS
    # ==============================================================================================================

    def exists_in_server(self, file_path):
        """
        Returns whether or not given file path exists in Artella remote server.

        :param str file_path: File path we want to check. It can be an absolute local file path or an URI path
        :return: True if the file exists in server; False otherwise.
        :rtype: bool
        """

        rsp = self.resolve_path(file_path)

        return False if 'error ' in rsp else True

    def status(self, file_paths, include_remote=False):
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

        if not self.get_remote_sessions(update=True):
            logger.warning(
                'No remote sessions available. Artella App Drive status call aborted.')
            return list()

        file_paths = utils.force_list(file_paths, remove_duplicates=True)
        result = list()

        # Make sure that paths are clean
        file_paths = [utils.clean_path(file_path) for file_path in file_paths]

        for file_path in file_paths:
            try:
                file_path = file_path.decode('utf-8')
            except UnicodeDecodeError:
                file_path = file_path.decode('latin-1')
            uri_path = path_to_uri(file_path) if not is_uri_path(file_path) else file_path
            uri_parts = urlparse(uri_path)
            params = urlencode({'handle': uri_parts.path, 'include-remote': str(bool(include_remote)).lower()})
            req = Request('http://{}:{}/v2/localserve/fileinfo?{}'.format(
                self._host, self._port, params))
            rsp = self._communicate(req)
            if 'error' in rsp:
                logger.error(
                    'Attempting to retrieve status "{}" "{}"'.format(
                        uri_path.encode(), rsp.get('error').encode('utf-8')))
                continue

            result.append(rsp)

        return result

    def download(self, paths, version=None, recursive=False, overwrite=True, folders_only=False):
        """
        Downloads files from remote server

        :param list(str) paths: List of file/folder paths (full or URI paths) to download from remote server
        :param int version: If given, specified version of the file/folder will be downloaded
        :param bool recursive: If True and we download a folder, all folder contents will be downloaded also
        :param bool overwrite: If True, already downloaded files will be overwritten with the contents in remote server
        :param bool folders_only: If True, only folder structure will be downloaded
        :return: Dictionary containing batch ID of the operation
        :rtype: dict
        :example:
        >>> self.download('artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png')
        >>> self.download('C:/Users/artella/artella-files/project/refs/', recursive=True)
        >>> self.download('C:/Users/artella/artella-files/project/refs/', recursive=True, version=1)
        >>> self.download('C:/Users/artella/artella-files/project/refs/ref.png')
        {
            'batch_id': '1584199877-4'
        }
        >>> self.download('Non/Valid/Path')
        {}
        """

        path_handle_map = paths_to_handles(paths, as_dict=True)
        handles = list(path_handle_map.values())
        if not path_handle_map or not handles:
            return dict()
        logger.debug('Handles: "{}"'.format(handles))

        payload = {
            'handles': handles,
            'recursive': recursive,
            'replace_locals': overwrite,
            'folders_only': folders_only
        }
        if version is not None:
            payload['version'] = int(version)
        try:
            req = Request('http://{}:{}/v2/localserve/transfer/download'.format(self._host, self._port))
            rsp = self._communicate(req, json.dumps(payload).encode())
        except Exception:
            rsp = {'error': traceback.format_exc()}
        if 'error' in rsp:
            logger.warning(
                'Unable to download file paths "{}" "{}"'.format(list(path_handle_map.keys()), rsp.get('error')))
            return rsp

        return self._track_response(rsp)

    def pause_downloads(self):
        """
        Pauses current active downloads from Artella server

        :return: Response from Artella server after downloads are stopped
        :rtype: dict
        """

        req = Request('http://{}:{}/v2/localserve/pause/pause/downloads'.format(self._host, self._port))
        rsp = self._communicate(req)

        return rsp

    def pause_uploads(self):
        """
        Pauses current active uploads to Artella server

        :return: Response from Artella server after downloads are stopped
        :rtype: dict
        """

        req = Request('http://{}:{}/v2/localserve/pause/pause/uploads'.format(self._host, self._port))
        rsp = self._communicate(req)

        return rsp

    def resume_downloads(self):
        """
        Resume current paused downloads from Artella server

        :return: Response from Artella server after downloads are resumed
        :rtype: dict
        """

        req = Request('http://{}:{}/v2/localserve/pause/resume/downloads'.format(self._host, self._port))
        rsp = self._communicate(req)

        return rsp

    def resume_uploads(self):
        """
        Resume current paused uploads to Artella server

        :return: Response from Artella server after uploads are resumed
        :rtype: dict
        """

        req = Request('http://{}:{}/v2/localserve/pause/resume/uploads'.format(self._host, self._port))
        rsp = self._communicate(req)

        return rsp

    def upload(self, paths, folders_only=False, comment=''):
        """
        Uploads a new file/folder or a new version of an existing file/folder to the remote server

        :param list(str) paths: List of file/folder paths (full or URI paths) to upload to the remote server
        :param bool folders_only: If True, only folder structure will be uploaded
        :param str comment: Comment that will be linked to the uploaded files/folders
        :return: Response from Artella server after the upload operation is done.
        :rtype: dict
        >>> self.upload('artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png')
        >>> self.upload('C:/Users/artella/artella-files/project/refs/', folders_only=True, comment='new folder')
        >>> self.upload('C:/Users/artella/artella-files/project/refs/ref.png', comment='new file version')
        {
            'batch_id': '1584199877-4'
        }
        >>> self.upload('Non/Valid/Path')
        {}
        """

        paths = utils.force_list(paths, remove_duplicates=True)

        path_handle_map = paths_to_handles(paths, as_dict=True)
        handles = list(path_handle_map.values())
        if not path_handle_map or not handles:
            return dict()
        logger.debug('Handles: "{}"'.format(handles))

        payload = {
            'handles': handles,
            'recursive': False,
            'commit_message': comment or '',
            'folders_only': folders_only
        }
        req = Request('http://{}:{}/v2/localserve/transfer/upload'.format(self._host, self._port))

        rsp = self._communicate(req, json.dumps(payload).encode())
        if 'error' in rsp:
            logger.warning(
                'Unable to upload file paths "{}" "{}"'.format(list(path_handle_map.keys()), rsp.get('error')))
            return rsp

        return self._track_response(rsp)

    def lock_file(self, file_paths, note=consts.DEFAULT_LOCK_NOTE):
        """
        Lock given file path in the web platform so that other users know it is in use

        :param str or list(str) file_paths: Absolute local file path(s) to lock
        :param str or None note: Optional note to add to the lock operation
        :return: Returns True if the lock file was successfully locked or if the if the file was already locked
            by the same user; False otherwise
        :rtype: bool
        :example:
        >>> self.lock_file('C:/Users/artella/artella-files/project/refs/ref.png')
        True
        """

        file_paths = utils.force_list(file_paths, remove_duplicates=True)
        result = OrderedDict()

        for file_path in file_paths:
            payload = {
                'handle': file_path,
                'note': note or consts.DEFAULT_LOCK_NOTE
            }
            req = Request('http://{}:{}/v2/localserve/lock'.format(self._host, self._port))
            req.add_header('Content-Type', 'application/json')
            rsp = self._communicate(req, json.dumps(payload), method='POST')
            if isinstance(rsp, dict):
                if 'error' in rsp:
                    logger.error('Unable to lock file path "{}" "{}"'.format(file_path, rsp.get('error')))
                    return False
            else:
                logger.error('Unable to lock file path "{}" "{}"'.format(file_path, rsp))
                return False

            result[file_path] = rsp.get('response', False) and rsp.get('status_code', 0) == 200

        return result

    def unlock_file(self, file_paths):
        """
        Unlocks given file paths in the web platform so that other users can use it

        :param str or list(str) file_paths: Absolute local file path(s) to unlock
        :return: Returns True if the file was successfully unlocked; False otherwise
        :rtype: bool
        """

        file_paths = utils.force_list(file_paths, remove_duplicates=True)
        result = OrderedDict()

        for file_path in file_paths:
            payload = {
                'handle': file_path
            }
            req = Request('http://{}:{}/v2/localserve/lock'.format(self._host, self._port))
            req.add_header('Content-Type', 'application/json')
            rsp = self._communicate(req, json.dumps(payload).encode(), method='DELETE')
            if 'error' in rsp:
                logger.error('Unable to unlock file path "{}" "{}"'.format(file_path, rsp.get('error')))
                return result

            if isinstance(rsp, dict):
                result[file_path] = rsp.get('response', False) and rsp.get('status_code', 0) == 200
            else:
                # If we try to unlock files that are not remote yet the response will be an string telling us that
                # information. We consider that as a valid lock.
                result[file_path] = True

        return result

    def file_current_version(self, file_path, _status=None):
        """
        Returns current version of the given file

        :param str file_path: Absolute local file path to retrieve current local version of
        :param str _status: new file status
        :return: Current local version of the given file path
        :rtype: int
        """

        status = _status or self.status(file_path, include_remote=True)
        if not status:
            return None

        current_version = -1
        for file_status in status:
            for file_uri_path, file_status_data in file_status.items():
                if 'local_info' not in file_status_data or not file_status_data['local_info'] or \
                        'remote_info' not in file_status_data:
                    continue
                else:
                    current_version = file_status_data['remote_info'].get('version', 0)
                    break

        return current_version

    def file_latest_version(self, file_path, _status=None):
        """
        Returns latest version of the given file
        :param str file_path: Absolute local file path to retrieve latest server version of
        :return: int
        """

        status = _status or self.status(file_path, include_remote=True)

        latest_version = 0
        for file_status in status:
            for file_uri_path, file_status_data in file_status.items():
                if 'local_info' not in file_status_data or not file_status_data['local_info'] or \
                        'remote_info' not in file_status_data:
                    continue
                else:
                    latest_version = file_status_data['remote_info'].get('raw', dict()).get('highest_version', 0)
                    break

        return latest_version

    def file_is_latest_version(self, file_path):
        """
        Returns whether or not given local file path is updated to the latest version available in Artella server.

        :param str file_path: Absolute local file path or URI path we want to check version of
        :return: True if the file is updated to the latest version available; False otherwise.
        :rtype: bool
        """

        status = self.status(file_path, include_remote=True)

        local_version = self.file_current_version(file_path, _status=status)
        latest_version = self.file_latest_version(file_path, _status=status)

        return local_version == latest_version

    def can_lock_file(self, file_path):
        """
        Returns whether or not current opened DCC file (or given file path) can be locked or not
        A file only can be locked if it is not already locked by other user.

        :param str or None file_path: Absolute local file path we want to check if can be locked or not.
        :return: True if the file can be locked by current user; False otherwise.
        :rtype: bool
        """

        is_locked, is_locked_by_me, is_locked_by_name, remote_record_found = self.check_lock(file_path)
        if not remote_record_found:
            logger.info('File "{}" is not versioned yet. No need to lock'.format(file_path))
            return True

        if not is_locked or (is_locked and is_locked_by_me):
            return True

        return False

    def check_lock(self, file_path):
        """
        Returns whether or not the given file is locked and whether or not current user is the one that has the file
        locked.

        :param str file_path: Absolute local file path to check lock status of
        :return: Returns a tuple with the following fields:
            - is_locked: True if the given file is locked; False otherwise
            - is_locked_by_me: True if the given file is locked by current user; False otherwise
            - locked_by_name: Name of the user that currently has the file locked
            - remote_record_found: Indicates whether the request relates to an existing remote file record or not
        :rtype: tuple(bool, bool, str, bool)
        """

        payload = {
            'handle': file_path
        }
        req = Request('http://{}:{}/v2/localserve/lock'.format(self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload).encode(), method='GET')
        if 'error' in rsp:
            logger.error('Unable to check lock status for file path "{}" "{}"'.format(file_path, rsp.get('error')))
            return False, False, '', False

        is_locked = rsp.get('is_locked', False)
        is_locked_by_me = rsp.get('is_locked_by_me', False)
        locked_by_name = rsp.get('locked_by_name', '')
        remote_record_found = rsp.get('remote_record_found', False)

        return is_locked, is_locked_by_me, locked_by_name, remote_record_found

    def get_progress(self):
        """
        Returns the download progress information of the current download operation from Artella server

        :return: A tuple containing the following information:
            - amount of done download operations
            - amount of total download operations in progress
            - amount of total download operations that are going to be done
            - amount of total bytes downloaded
            - amount of total bytes to download
        :rtype: int, int, int, int, int
        """

        tx_count_done = 0
        tx_count_total = 0
        tx_bytes_done = 0
        tx_bytes_total = 0
        batches_complete = set()

        batch_ids = list(self._batch_ids)[:]

        for batch_id in batch_ids:
            params = urlencode({'batch-id': batch_id, 'details': True})
            req = Request('http://{}:{}/v2/localserve/progress/summary?{}'.format(self._host, self._port, params))
            rsp = self._communicate(req)
            tcd = int(rsp.get('transfer_count_done', 0))
            tct = int(rsp.get('transfer_count_total', 0))
            tbd = int(rsp.get('transfer_bytes_download_done', 0))
            tbt = int(rsp.get('transfer_bytes_download_total', 0))
            if tcd == tct or tbd == tbt:
                batches_complete.add(batch_id)
                continue
            tx_count_done += tcd
            tx_count_total += tct
            tx_bytes_done += tbd
            tx_bytes_total += tbt

        self._batch_ids -= batches_complete

        progress_value = 1
        if tx_bytes_total > 0:
            progress_value = float(tx_bytes_done) / float(tx_bytes_total)
        elif tx_count_total > 0:
            progress_value = float(tx_count_done) / float(tx_count_total)

        return int(progress_value * 100), tx_count_done, tx_count_total, tx_bytes_done, tx_bytes_total

    # ==============================================================================================================
    # TEST
    # ==============================================================================================================

    def ping(self):
        """
        Test call that returns whether the Artella Drive is valid or not

        :return: Returns a success response or auth failure message
        :rtype: dict
        """

        req = Request('http://{}:{}/v2/localserve/ping'.format(self._host, self._port))
        rsp = self._communicate(req, skip_auth=True)

        return rsp

    # ==============================================================================================================
    # ARTELLA DRIVE APP
    # ==============================================================================================================

    def artella_drive_connect(self):
        """
        Connects to the local user Artella Drive App via web socket so we can listen for realtime events
        :return:
        """

        server_address = (self._host, self._port)
        logger.info('Connecting to Artella Drive App web socket: {}'.format(server_address))
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(server_address)
        except Exception as exc:
            logger.error('Artella Plugin failed to connect to the Artella Drive App web socket: {}'.format(exc))
            return

        self.artella_drive_send_request(sock)
        self._socket_buffer = SocketBuffer(sock)
        rsp = self.artella_drive_read_response()
        self._running = True

        return rsp

    def artella_drive_disconnect(self):
        logger.debug('Disconnecting Artella Drive Client ...')
        self._running = False

        self._disconnect()

        return True

    def artella_drive_listen(self):
        self.artella_drive_connect()
        if not self._socket_buffer:
            logger.error('Socket to Artella Drive not connected.')
            return
        self._client_thread = threading.Thread(target=self._pull_messages,).start()

    def artella_drive_send_request(self, sock):

        if not self.update_auth_challenge():
            logger.error('Unable to authenticate to Artella Drive App.')
            return

        extensions_str = ''
        for extension in self._extensions:
            if extension != '':
                extension = '{}&'.format(extension)
            if extension.startswith('*'):
                extension = extension[1:]
            if extension.startswith('.'):
                extension = '%2A{}'.format(extension)
            extensions_str += 'file-handler={}'.format(extension)
        if extensions_str:
            extensions_str = extensions_str[:-1]

        key, expected_key_response = make_ws_key()
        path = '/v2/localserve/ws' if not extensions_str else '/v2/localserve/ws?{}'.format(extensions_str)
        r = [
            'GET {} HTTP/1.1'.format(path),
            'Upgrade: websocket',
            'Connection: Upgrade',
            'Host: {}:{}'.format(self._host, self._port),
            'Sec-WebSocket-Key: {}'.format(key),
            'Sec-WebSocket-Version: 13',
            'Authorization: {}'.format(self._auth_header),
        ]
        rr = consts.CRLF.join(r) + consts.CRLF + consts.CRLF
        logger.debug(
            'Artella Plugin sending websocket access request to the local Artella Drive App: {}'.format(r))

        try:
            sock.sendall(rr.encode())
        except Exception as exc:
            logger.warning('Was not possible to send request to Artella Drive App: {}'.format(exc))
            return False

        return True

    def artella_drive_read_response(self):
        logger.debug('Reading socket response ...')
        line = ''
        while line != consts.CRLF:
            line = self._socket_buffer.read_line()

        return line

    # ==============================================================================================================
    # INTERNAL
    # ==============================================================================================================

    def _communicate(self, req, data=None, skip_auth=False, method=None):
        """
        Internal function that sends a request to ArtellaDriver server

        :param Request req: URL request object
        :param str data: additional encoded data to send to the server
        :param bool skip_auth: whether authorization check should be skip or not
        :param str or None method: Method that should be used bu urrllib to send the request
        :return: dict, dictionary containing the answer from the server.
            If the call is not valid, a dictionary containing the url and error message is returned.
        """

        logger.debug('Making request to Artella Drive "{}"'.format(req.get_full_url()))
        if data:
            logger.debug('Request payload dump: "{}" | {}'.format(json.loads(data), type(data)))

        if not self._auth_header and not skip_auth:
            rsp = self.update_auth_challenge()
            if not rsp:
                msg = 'Unable to authenticate'
                logger.error(msg)
                return {'error': msg, 'url': req.get_full_url()}

        req.add_header('Authorization', self._auth_header)
        if method is not None:
            req.get_method = lambda: method
        try:
            rsp = urlopen(req, data)
        except URLError as exc:
            if hasattr(exc, 'reason'):
                msg = 'Failed to reach the local ArtellaDrive: "{}"'.format(exc.reason)
            elif hasattr(exc, 'code'):
                msg = 'ArtellaDrive is unable to fulfill the request "{}"'.format(exc.code)
            else:
                msg = exc
            logger.debug(exc)
            logger.error(msg)
            return {'error': msg, 'url': req.get_full_url()}
        else:
            raw_data = rsp.read()
            if not raw_data:
                return {'error': 'No Artella data response.', 'url': req.get_full_url()}
            else:
                try:
                    raw_data = "".join(chr(x) for x in bytearray(raw_data))
                    json_data = json.loads(raw_data)
                except ValueError:
                    logger.debug('ArtellaDrive data response: "{}"'.format(raw_data))
                    return raw_data
                except Exception as exc:
                    logger.error(exc)
                    return raw_data
                else:
                    logger.debug('ArtellaDriver JSON response: "{}"'.format(json_data))
                    return json_data

    def _disconnect(self):
        """
        Internal function that closes current Artella Drive client web socket

        :return: True if the web socket was successfully disconnected; False otherwise.
        :rtype: bool
        """

        try:
            if self._socket_buffer:
                self._socket_buffer.close()
                self._socket_buffer = None
                self._running = False
        except Exception as exc:
            logger.error(
                'Error while disconnect Artella Plugin from Artella Drive App web socket ... {}'.format(exc))
            return False

        return True

    def _track_response(self, rsp):
        """
        Internal function that extracts batch_id and transfer_data from response so that we can continue the
        tracking process

        :param dict rsp: Dictionary returned by a call to remote server
        :return: String containing ID of the operation
        :rtype: str
        """

        batch_id = rsp.get('batch_id')
        self._batch_ids.add(batch_id)

        return rsp

    def _pull_messages(self):
        logger.debug('Listening for commands on websocket')
        while self._running:
            try:
                msg = self._get_message()
            except Exception as exc:
                self._available = False
                try:
                    if exc.errno == 10054:
                        self._disconnect()
                except Exception as exc:
                    try:
                        logger.debug(str(exc))
                    except Exception as exc:
                        pass
                continue

            self._available = True
            logger.debug('Message received: {}'.format(msg))
            dccplugin.DccPlugin().pass_message(msg)

        # If Artella Drive Client is nor running we force disconnection
        # self._disconnect()

    def _get_message(self):
        op_code = ord(self._socket_buffer.get_char())
        v = ord(self._socket_buffer.get_char())
        if op_code != 129:
            raise exceptions.ArtellaException('Not a final text frame: {}'.format(op_code))
        if v < 126:
            length = v
        elif v == 126:
            a = ord(self._socket_buffer.get_char()) << 8
            b = ord(self._socket_buffer.get_char())
            length = a + b
        elif v == 127:
            # 8 byte payload length - we do not have any of these
            raise exceptions.ArtellaException('Unsupported payload length')
        else:
            raise exceptions.ArtellaException('Bad payload length: {}'.format(v))

        payload = self._socket_buffer.get_chars(length)

        return json.loads(payload)


class SocketBuffer(object):
    def __init__(self, sock):
        super(SocketBuffer, self).__init__()

        self._sock = sock
        self._buffer = ''

    def read_line(self):
        line = ''
        while True:
            c = self.get_char()
            line += c
            if c == '\n':
                return line

    def get_char(self):
        if len(self._buffer) == 0:
            self._buffer = self._sock.recv(consts.DEFAULT_BUFFER_SIZE)
        r = self._buffer[0]
        self._buffer = self._buffer[1:]

        return chr(r) if type(r) == int else r

    def get_chars(self, count):
        cc = ''
        for x in range(count):
            cc += self.get_char()

        return cc

    def close(self):
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()


def make_ws_key():
    """
     https://tools.ietf.org/html/rfc6455
    :return:
    """

    key = base64.b64encode(str(int(random.random() * 9999999)).encode()).decode()
    h = hashlib.sha1()
    h.update((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode())
    expected_key_response = base64.b64encode(h.digest()).decode()

    return key, expected_key_response


def is_uri_path(file_path):
    """
    Returns whether or not given file path is using Artella URI schema or not

    :param str file_path: File path to check.
    :return: True if given path is using Artella URI schema; False otherwise.
    :rtype: bool
    :example:
    >>> is_uri_path("artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png")
    True
    >>> is_uri_path("C:/Users/artella/artella-files/project/refs/ref.png")
    False
    """

    if not file_path:
        return False

    uri = urlparse(file_path)

    return uri.scheme == consts.ARTELLA_URI_SCHEME


def path_to_uri(path):
    """
    Converts a path to a path that uses Artella API scheme

    :param str path: File to convert to Artella URI scheme format
    :return: Returns a path converted into Artella URI scheme format. If the conversion cannot be done, the path
        without any change will be returned.
    :rtype: str
    :example:
    >>> path_to_uri("artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png")
    "artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png"
    >>> path_to_uri("C:/Users/artella/artella-files/project/refs/ref.png")
    "artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png"
    >>> path_to_uri("Invalid/Path")
    "Invalid/Path"
    """

    path_uri = paths_to_uri(path)

    return path_uri[0]


def paths_to_uri(paths):
    """
    Converts a list of paths to paths that use Artella URI scheme

    :param str or list(str) paths: List of paths to convert to Artella URI scheme
    :return: List of paths converted into Artella URI scheme. If a path cannot be converted, it will be returned
        without any changes.
    :rtype: list(str)
    """

    paths = utils.force_list(paths)

    fixed_paths = list()

    for pth in paths:
        full_path = os.path.abspath(os.path.expandvars(os.path.expanduser(pth)))
        rsp = ArtellaDriveClient.get().resolve_path(full_path)
        if 'error' in rsp:
            logger.warning('Unable to translate path "{}" "{}"'.format(pth, rsp.get('error')))
            fixed_paths.append(pth)
            continue

        url_parts = (consts.ARTELLA_URI_SCHEME, '', rsp.get('handle'), '', '', '')
        fixed_path = urlunparse(url_parts)
        if not is_uri_path(fixed_path):
            logger.error('Failed to translate "{}" to URI: "{}"'.format(pth, fixed_path))
            fixed_paths.append(pth)
            continue

        fixed_paths.append(fixed_path)

    return fixed_paths


def path_to_handle(path):
    """
    Converts a path to an Artella handle path

    :param path: str, Path to convert to handle path, it can be an URI path or an absolute local file path
    :return: Returns an Artella handle path
    :rtype: str
    :example:
    >>> path_to_handle("artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png")
    "file__12345"
    >>> path_to_handle("C:/Users/artella/artella-files/project/refs/ref.png")
    "file__12345"
    """

    handles = paths_to_handles(path, as_dict=False)

    return handles[0] if handles else path


def paths_to_handles(paths, as_dict=False):
    """
    Converts a list of paths (full paths or URI paths) to Artella handle paths

    :param str or list(str) paths:
    :param bool as_dict: If True, a dictionary mapping file paths with their handle will be returned.
    :return: List of handles associated to given file paths
    :rtype: list(str) or dict(str, str)
    """

    paths = utils.force_list(paths)

    handles = set()
    path_handle_map = dict()

    for pth in paths:
        if not is_uri_path(pth):
            uri_path = path_to_uri(pth)
            # If converted URI path is the same as the original path means that path is not valid, so we skip it
            if uri_path == pth:
                continue
        else:
            uri_path = pth
        uri_parts = urlparse(uri_path)
        handle = uri_parts.path
        handles.add(handle)
        path_handle_map[pth] = handle

    if as_dict:
        return path_handle_map

    return list(handles)


if __name__ == '__main__':

    from artella import loader
    loader.init()

    artella_cli = ArtellaDriveClient.get()
    print(artella_cli.ping())
