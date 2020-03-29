#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive Python client implementation
"""

from __future__ import print_function, division, absolute_import

import os
import json
import codecs
import socket
import base64
import random
import hashlib
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

import artella
from artella.core import consts, utils


class ArtellaDriveClient(object):
    """
    Class used to interact with ArtellaDrive application on client side
    """

    _challenge_path = None

    def __init__(self, host=consts.DEFAULT_HOST, port=consts.DEFAULT_PORT):
        self._host = host               # Contains default IP host used by the client.
        self._port = port               # Contains default port used by the client.
        self._auth_header = ''          # Contains authentication header read from challenge file.
        self._remote_sessions = list()  # Contains list of available remote sessions.
        self._batch_ids = set()         # Contains a list that tracks all calls made to the client during a session.
        self._socket_buffer = None      # Contains instance of the socket buffer used to communicate with Artella App
        self._running = False           # Flag that is True while Artella Drive thread is running
        self._exception = None          # Contains exception caused while Artella Drive is running

    # ==============================================================================================================
    # PROPERTIES
    # ==============================================================================================================

    @property
    def running(self):
        """
        Returns whether or not current Artella Drive thread is running.
        While Artella Drive thread is running, it listens responses from Artella Drive

        :return: True if the Artella Drive thread is running; False otherwise
        :rtype: bool
        """

        return self._running

    # ==============================================================================================================
    # CLASS FUNCTIONS
    # ==============================================================================================================

    @classmethod
    def get(cls):
        """
        Returns a new instance of ArtellaDriveClient making sure that authorization is valid

        :return: New instance of Artella Drive object
        :rtype: ArtellaDriveClient
        """

        artella_client = cls()

        # Challenge value gets updated when the Artella drive restarts.
        # We need to check this each time in case the local server got restarted
        auth_header = artella_client.update_auth_challenge()
        if not auth_header:
            raise Exception('Local ArtellaDriver not available. Please launch Artella Drive App.')

        # Updates the list of available remotes
        artella_client.update_remotes_sessions()

        return artella_client

    # ==============================================================================================================
    # CHALLENGE FILE
    # ==============================================================================================================

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
                artella.log_error('Unable to get challenge file path "{}"'.format(rsp))
                self._auth_header = None
                return self._auth_header
            ArtellaDriveClient._challenge_path = rsp.get('challenge_file_path')

        if not os.path.exists(ArtellaDriveClient._challenge_path):
            artella.log_error('Challenge file not found: "{}"'.format(ArtellaDriveClient._challenge_path))
            self._auth_header = None
            return self._auth_header

        with open(os.path.expanduser(ArtellaDriveClient._challenge_path), 'rb') as fp:
            base_auth_header = fp.read()

        self._auth_header = consts.AUTH_HEADER.format(codecs.encode(base_auth_header[:64], 'hex').decode('ascii'))

        return self._auth_header

    def get_remote_sessions(self):
        """
        Returns a list with all available remote sessions
        :return: List of cached remote sessions in current Artella Drive Client
        :rtype: list(str)
        """

        return self._remote_sessions

    def update_remotes_sessions(self):
        """
        Collects all available remote servers available.

        :return: List of available remote sessions received from Artella Drive App.
        :rtype: list(str)
        """

        if not self.update_auth_challenge():
            artella.log_error('Unable to authenticate to Artella Drive App.')
            utils.clear_list(self._remote_sessions)
            return

        rsp = self.ping()
        if 'error' in rsp:
            artella.log_error('Attempting to retrieve remote sessions: "{}" '.format(rsp.get('error')))
            utils.clear_list(self._remote_sessions)
            return

        self._remote_sessions = rsp.get('remote_sessions', list())
        if not self._remote_sessions:
            artella.log_warning(
                'No remote sessions available. Please visit your Project Drive in Artella Web App and try again!')

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
    # PATHS
    # ==============================================================================================================

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
                artella.log_warning('Unable to get local storage root. Using env var instead: "{}"'.format(consts.ALR))
                local_root = alr
            else:
                artella.log_error('Unable to get local storage root.')
                artella.log_info(
                    'Check that the local Artella Drive service is running and you have a working internet connection.')
                artella.log_info(
                    'To work offline set the "{}" environment variable to the proper local project directory'.format(
                        consts.ALR))

        return local_root

    def resolve(self, path):
        """
        Converts a local path to a remote handle path representation and vice versa

        :param str path: local path or remote server path
        :return: Returns a dictionary containing resolved path or error message is the path cannot be resolve
        :rtype: dict
        :example:
        >>> os.environ['ARTELLA_FOLDER_ROOT'] = "C:/Users/artella/artella-files/project"
        >>> self.resolve("$ARTELLA_FOLDER_ROOT/refs/ref.png")
        {
            'handle': 'project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png',
            'file_path': u'C:\\Users\\artella\\artella-files\\project\\refs\\ref.png'
        }
        >>> self.resolve("artella:project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png")
        {
            'handle': 'project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png',
            'file_path': u'C:\\Users\\artella\\artella-files\\project\\refs\\ref.png'
        }
        >>> self.resolve("C:/Users/artella/artella-files/project/refs/ref.png")
        {
            'handle': 'project__fo0pohsa2sea4wyr5zmzcwnzse/refs/ref.png',
            'file_path': 'C:\\Users\\artella\\artella-files\\project\\refs\\ref.png'
        }
        >>> self.resolve("C:/Invalid/Path/ref.png")
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
            artella.log_error('Attempting to resolve "{}" "{}"'.format(path, rsp.get('error')))

        return rsp

    # ==============================================================================================================
    # FILES/FOLDERS
    # ==============================================================================================================

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

        if not self.get_remote_sessions():
            artella.log_warning(
                'No remote sessions available. Artella App Drive status call aborted.')
            return dict()

        file_paths = utils.force_list(file_paths, remove_duplicates=True)
        result = list()

        for file_path in file_paths:
            uri_path = path_to_uri(file_path) if not is_uri_path(file_path) else file_path
            uri_parts = urlparse(uri_path)
            params = urlencode({'handle': uri_parts.path, 'include-remote': str(bool(include_remote)).lower()})
            req = Request('http://{}:{}/v2/localserve/fileinfo?{}'.format(
                self._host, self._port, params))
            rsp = self._communicate(req)
            if 'error' in rsp:
                artella.log_error('Attempting to retrieve status "{}" "{}"'.format(uri_path, rsp.get('error')))
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
        handles = path_handle_map.values()
        if not path_handle_map or not handles:
            return dict()
        artella.log_debug('Handles: "{}"'.format(handles))

        payload = {
            'handles': handles,
            'recursive': recursive,
            'replace_locals': overwrite,
            'folders_only': folders_only
        }
        if version is not None:
            payload['version'] = int(version)
        req = Request('http://{}:{}/v2/localserve/transfer/download'.format(self._host, self._port))
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            artella.log_warning(
                'Unable to download file paths "{}" "{}"'.format(path_handle_map.keys(), rsp.get('error')))
            return rsp

        return self._track_response(rsp)

    def upload(self, paths, folders_only=False, comment=''):
        """
        Uploads a new file/folder or a new version of an existing file/folder to the remote server

        :param list(str) paths: List of file/folder paths (full or URI paths) to upload to the remote server
        :param bool folders_only: If True, only folder structure will be uploaded
        :param str comment: Comment that will be linked to the uploaded files/folders
        :return:
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
        artella.log_debug('Handles: "{}"'.format(handles))

        payload = {
            'handles': handles,
            'recursive': False,
            'commit_message': comment or '',
            'folders_only': folders_only
        }
        req = Request('http://{}:{}/v2/localserve/transfer/upload'.format(self._host, self._port))

        rsp = self._communicate(req, json.dumps(payload).encode())
        if 'error' in rsp:
            artella.log_warning(
                'Unable to upload file paths "{}" "{}"'.format(path_handle_map.keys(), rsp.get('error')))
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
            rsp = self._communicate(req, json.dumps(payload))
            if isinstance(rsp, dict):
                if 'error' in rsp:
                    artella.log_error('Unable to lock file path "{}" "{}"'.format(file_path, rsp.get('error')))
                    return False
            else:
                artella.log_error('Unable to lock file path "{}" "{}"'.format(file_path, rsp))
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
            req = Request('http://{}:{}/v2/localserve/unlock'.format(self._host, self._port))
            req.add_header('Content-Type', 'application/json')
            rsp = self._communicate(req, json.dumps(payload).encode())
            if 'error' in rsp:
                artella.log_error('Unable to unlock file path "{}" "{}"'.format(file_path, rsp.get('error')))
                return False

            if isinstance(rsp, dict):
                result[file_path] = rsp.get('response', False) and rsp.get('status_code', 0) == 200
            else:
                # If we try to unlock files that are not remote yet the response will be an string telling us that
                # information. We consider that as a valid lock.
                result[file_path] = True

        return file_paths

    def file_current_version(self, file_paths):
        """
        Returns current version of the given file
        :param str or list(str) file_paths: Absolute local file path(s) to retrieve version of
        :return:
        """

        status = self.status(file_paths, include_remote=True)

        result = list()

        for file_status in status:
            for file_uri_path, file_status_data in file_status.items():
                if 'remote_info' not in file_status_data:
                    result.append(0)
                else:
                    current_version = file_status_data['remote_info'].get('version', 0)
                    result.append(current_version)

        return result

    def file_is_locked(self, file_path):
        """
        Returns whether or not the given file is locked and whether or not current user is the one that has the file
        locked.
        :param str file_path: Absolute local file path to check lock status of
        :return: Returns a tuple with the following fields:
            - is_locked: True if the given file is locked; False otherwise
            - is_locked_by_me: True if the given file is locked by current user; False otherwise
            - locked_by_name: Name of the user that currently has the file locked
        :rtype: tuple(bool, bool, str)
        """

        payload = {
            'handle': file_path
        }
        req = Request('http://{}:{}/v2/localserve/check-lock'.format(self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload).encode())
        if 'error' in rsp:
            artella.log_error('Unable to check lock status for file path "{}" "{}"'.format(file_path, rsp.get('error')))
            return False, False

        is_locked = rsp.get('is_locked', False)
        is_locked_by_me = rsp.get('is_locked_by_me', False)
        locked_by_name = rsp.get('locked_by_name', '')

        return is_locked, is_locked_by_me, locked_by_name

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

        # TODO: Using this we completely stop Artella client thread if an exception is arised
        # if self._running:
        #     self.artella_drive_disconnect()

        server_address = (self._host, self._port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        artella.log_info('Connecting to Artella Drive App web socket: {}'.format(server_address))
        try:
            sock.connect(server_address)
        except Exception as exc:
            artella.log_error('Artella Plugin failed to connect to the Artella Drive App web socket: {}'.format(exc))
            return

        self.artella_drive_send_request(sock)
        self._socket_buffer = SocketBuffer(sock)
        rsp = self.artella_drive_read_response()
        self._running = True

        return rsp

    def artella_drive_disconnect(self):
        self._running = False

    def artella_drive_listen(self):
        try:
            self.artella_drive_connect()
            if not self._socket_buffer:
                artella.log_error('Socket to Artella Drive not connected.')
                return
            threading.Thread(target=self._pull_messages,).start()
        except Exception as exc:
            artella.log_exception('{} | {}'.format(exc, traceback.format_exc()))

    def artella_drive_send_request(self, sock):

        if not self.update_auth_challenge():
            artella.log_error('Unable to authenticate to Artella Drive App.')
            return

        key, expected_key_response = make_ws_key()
        path = '/v2/localserve/ws'
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
        artella.log_debug(
            'Artella Plugin sending websocket access request to the local Artella Drive App: {}'.format(r))
        sock.sendall(rr.encode())

    def artella_drive_read_response(self):
        artella.log_debug('Reading socket response ...')
        line = ''
        while line != consts.CRLF:
            line = self._socket_buffer.read_line()

        return line

    # ==============================================================================================================
    # INTERNAL
    # ==============================================================================================================

    def _communicate(self, req, data=None, skip_auth=False):
        """
        Internal function that sends a request to ArtellaDriver server

        :param Request req: URL request object
        :param str data: additional encoded data to send to the server
        :param bool skip_auth: whether authorization check should be skip or not
        :return: dict, dictionary containing the answer from the server.
            If the call is not valid, a dictionary containing the url and error message is returned.
        """

        artella.log_debug('Making request to Artella Drive "{}"'.format(req.get_full_url()))
        if data:
            artella.log_info('Request payload dump: "{}" | {}'.format(json.loads(data), type(data)))
            # if data:
            #     data = data.encode()

        if not self._auth_header and not skip_auth:
            rsp = self.update_auth_challenge()
            if not rsp:
                msg = 'Unable to authenticate'
                artella.log_error(msg)
                return {'error': msg, 'url': req.get_full_url()}

        req.add_header('Authorization', self._auth_header)
        try:
            rsp = urlopen(req, data)
        except URLError as exc:
            if hasattr(exc, 'reason'):
                msg = 'Failed to reach the local ArtellaDrive: "{}"'.format(exc.reason)
            elif hasattr(exc, 'code'):
                msg = 'ArtellaDrive is unable to fulfill the request "{}"'.format(exc.code)
            else:
                msg = exc
            artella.log_debug(exc)
            artella.log_error(msg)
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
                    artella.log_debug('ArtellaDrive data response: "{}"'.format(raw_data))
                    return raw_data
                except Exception as exc:
                    artella.log_error(exc)
                    return raw_data
                else:
                    artella.log_debug('ArtellaDriver JSON response: "{}"'.format(json_data))
                    return json_data

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
        artella.log_info('Listening for commands on websocket')
        while self._running:
            try:
                if self._exception:
                    self.artella_drive_connect()
                    self._exception = None
                msg = self._get_message()
                artella.log_info('Message received: {}'.format(msg))
                artella.Plugin().pass_message(msg)
            except Exception as exc:
                artella.log_exception('{} | {}'.format(exc, traceback.format_exc()))
                self._exception = exc

    def _get_message(self):
        op_code = ord(self._socket_buffer.get_char())
        v = ord( self._socket_buffer.get_char())
        if op_code != 129:
            raise Exception('Not a final text frame: {}'.format(op_code))
        if v < 126:
            length = v
        elif v == 126:
            a = ord(self._socket_buffer.get_char()) << 8
            b = ord(self._socket_buffer.get_char())
            length = a + b
        elif v == 127:
            # 8 byte payload length - we do not have any of these
            raise Exception('Unsupported payload length')
        else:
            raise Exception('Bad payload length: {}'.format(v))

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
            self._buffer = self._sock.recv(2000)
        r = self._buffer[0]
        self._buffer = self._buffer[1:]

        return chr(r) if type(r) == int else r

    def get_chars(self, count):
        cc = ''
        for x in range(count):
            cc += self.get_char()

        return cc


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
        rsp = ArtellaDriveClient.get().resolve(full_path)
        if 'error' in rsp:
            artella.log_warning('Unable to translate path "{}" "{}"'.format(pth, rsp.get('error')))
            fixed_paths.append(pth)
            continue

        url_parts = (consts.ARTELLA_URI_SCHEME, '', rsp.get('handle'), '', '', '')
        fixed_path = urlunparse(url_parts)
        if not is_uri_path(fixed_path):
            artella.log_error('Failed to translate "{}" to URI: "{}"'.format(pth, fixed_path))
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
    artella_cli = ArtellaDriveClient.get()
    print(artella_cli.ping())
    print(artella_cli.get_challenge_file_path())
    print(artella_cli.get_local_root())
    print(artella_cli.get_storage_id())
    print(artella_cli.get_metadata())
