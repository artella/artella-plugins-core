#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive Python client implementation
"""

from __future__ import print_function, division, absolute_import

import os
import json
import logging
try:
    from urllib.parse import urlparse, urlencode, urlunparse
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urlparse import urlparse, urlunparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError, URLError

from artella.core import consts, utils

logging.basicConfig(level=logging.INFO)


class ArtellaDriveClient(object):
    """
    Class used to interact with ArtellaDrive application on client side
    """

    _challenge_path = None

    def __init__(self, host=consts.DEFAULT_HOST, port=consts.DEFAULT_PORT):
        self._host = host
        self._port = port
        self._auth_header = None
        self._batch_ids = set()

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
        artella_client.update_auth_challenge()

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
        Collects some data from a local file to confirm we are running on the same that
        Artella drive is running.

        :return: string containing authentication header for current session or None if authentication was invalid
        :rtype: str or None
        """

        if not ArtellaDriveClient._challenge_path:
            rsp = self.get_challenge_file_path()
            if not rsp or 'error' in rsp:
                logging.error('Unable to get challenge file path "{}"'.format(rsp))
                self._auth_header = None
                return self._auth_header
            ArtellaDriveClient._challenge_path = rsp.get('challenge_file_path')

        if not os.path.exists(ArtellaDriveClient._challenge_path):
            logging.error('Challenge file not found: "{}"'.format(ArtellaDriveClient._challenge_path))
            self._auth_header = None
            return self._auth_header

        with open(os.path.expanduser(ArtellaDriveClient._challenge_path)) as fp:
            base_auth_header = fp.read()
        self._auth_header = consts.AUTH_HEADER.format(base_auth_header[:64].encode('hex'))

        return self._auth_header

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
            "workspace": "C:\Users\artella\artella-files",
            "openers.log": "C:\\Users\\artella\\AppData\\Roaming\\artella\\openers.log"
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
        "C:\Users\artella\artella-files"
        """

        req = Request('http://{}:{}/v2/localserve/kv/settings/workspace'.format(self._host, self._port))
        local_root = self._communicate(req)
        if not local_root or (isinstance(local_root, dict) and 'error' in local_root):
            alr = os.environ.get(consts.ALR, None)
            if alr:
                logging.warning('Unable to get local storage root. Using env var instead: "{}"'.format(consts.ALR))
                local_root = alr
            else:
                logging.error('Unable to get local storage root.')
                logging.info(
                    'Check that the local Artella Drive service is running and you have a working internet connection.')
                logging.info(
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
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            logging.error('Attempting to resolve "{}" "{}"'.format(path, rsp.get('error')))

        return rsp

    # ==============================================================================================================
    # FILES
    # ==============================================================================================================

    def status(self, path):
        """
        Returns the status of a file from the remote server
        :param str path: Local path or Resolved URI path of a folder/file or list of folders/files
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

        if not is_uri_path(path):
            path = path_to_uri(path)

        uri_parts = urlparse(path)
        params = urlencode({'handle': uri_parts.path})
        req = Request('http://{}:{}/v2/localserve/fileinfo?{}'.format(self._host, self._port, params))
        rsp = self._communicate(req)
        if 'error' in rsp:
            logging.error('Attempting to retrieve status "{}" "{}"'.format(path, rsp.get('error')))
            return rsp

        # TODO: [dave]: once we have a reliable way to resolve the record handle
        # back into the abs path, iterate and match on the file name
        for k, v in rsp.items():
            if os.path.basename(k) == os.path.basename(path):
                return v.get('remote_info', dict())

        return rsp

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

        handles = paths_to_handles(paths)
        if not handles:
            return dict()
        logging.debug('Handles: "{}"'.format(handles))

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
            logging.warning('Unable to download file paths "{}" "{}"'.format(handles, rsp.get('error')))
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

        handles = paths_to_handles(paths)
        if not handles:
            return dict()
        logging.debug('Handles: "{}"'.format(handles))

        payload = {
            'handles': handles,
            'recursive': False,
            'commit_message': comment or '',
            'folders_only': folders_only
        }
        req = Request('http://{}:{}/v2/localserve/transfer/upload'.format(self._host, self._port))
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            logging.warning('Unable to upload file paths "{}" "{}"'.format(handles, rsp.get('error')))
            return rsp

        return self._track_response(rsp)

    # ==============================================================================================================
    # TEST
    # ==============================================================================================================

    def ping(self):
        """
        Test call that returns whether the Artella Drive is valid or not
        :return: Returns a success response or auth failure message
        :rtype: dict
        :example:
        >>> self.ping()
        {
            message: 'OK';
            response: true;
            status_code: 200;
        }
        """

        req = Request('http://{}:{}/v2/localserve/ping'.format(self._host, self._port))
        rsp = self._communicate(req, skip_auth=True)

        return rsp

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

        logging.debug('Making request to Artella Drive "{}"'.format(req.get_full_url()))
        if data:
            logging.debug('Request payload dump: "{}"'.format(json.loads(data)))

        if not self._auth_header and not skip_auth:
            rsp = self.update_auth_challenge()
            if not rsp:
                msg = 'Unable to authenticate'
                logging.error(msg)
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
            logging.debug(exc)
            logging.error(msg)
            return {'error': msg, 'url': req.get_full_url()}
        else:
            raw_data = rsp.read()
            if not raw_data:
                return {'error': 'No Artella data response.', 'url': req.get_full_url()}
            else:
                try:
                    json_data = json.loads(raw_data)
                except ValueError:
                    logging.debug('ArtellaDrive data response: "{}"'.format(raw_data))
                    return raw_data
                except Exception as exc:
                    logging.error(exc)
                    return raw_data
                else:
                    logging.debug('ArtellaDriver JSON response: "{}"'.format(json_data))
                    return json_data

    def _track_response(self, rsp):
        """
        Internal function that extracts batch_id and transfer_data from response so that we can continue the
        tracking process
        :param rsp:
        :return:
        """

        batch_id = rsp.get('batch_id')
        self._batch_ids.add(batch_id)

        return rsp


def is_uri_path(file_path):
    """
    Returns whether or not given file path is using Artella URI schema or not
    :param str file_path:
    :return: True if given path is using Artella URI schema; False otherwise.
    :rtype: bool
    """

    if not file_path:
        return False

    uri = urlparse(file_path)

    return uri.scheme == consts.ARTELLA_URI_SCHEME


def path_to_uri(path):
    """
    Converts a path to a path that uses Artella API scheme
    :param str path:
    :return:
    :rtype: list
    """

    path_uri = paths_to_uri(path)

    return path_uri[0]


def paths_to_uri(paths):
    """
    Converts a list of paths to paths that uses Artella URI scheme
    :param str or list(str) paths:
    :return:
    :rtype: list
    """

    paths = utils.force_list(paths)

    fixed_paths = list()

    for pth in paths:
        full_path = os.path.abspath(os.path.expandvars(os.path.expanduser(pth)))
        rsp = ArtellaDriveClient.get().resolve(full_path)
        if 'error' in rsp:
            logging.warning('Unable to translate path "{}" "{}"'.format(pth, rsp.get('error')))
            fixed_paths.append(pth)
            continue

        url_parts = (consts.ARTELLA_URI_SCHEME, '', rsp.get('handle'), '', '', '')
        fixed_path = urlunparse(url_parts)
        if not is_uri_path(fixed_path):
            logging.error('Failed to translate "{}" to URI: "{}"'.format(pth, fixed_path))
            fixed_paths.append(pth)
            continue

        fixed_paths.append(fixed_path)

    return fixed_paths


def paths_to_handles(paths):
    """
    Converts a list of paths (full paths or URI paths) to Artella handle paths
    :param str or list(str) paths:
    :return:
    :rtype: list
    """

    paths = utils.force_list(paths)

    handles = set()

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

    return list(handles)


if __name__ == '__main__':
    artella_cli = ArtellaDriveClient.get()
    print(artella_cli.ping())
    print(artella_cli.get_challenge_file_path())
    print(artella_cli.get_local_root())
    print(artella_cli.get_storage_id())
    print(artella_cli.get_metadata())
    # print(artella_cli.resolve('artella:project__foppohsucse44wyrmzm6ewnzse/Plug-ins/Area.png'))
    # os.environ['ARTELLA_FOLDER_ROOT'] = "C:/Users/Tomi/artella-files/Rambutan"
    # print(path_to_uri("$ARTELLA_FOLDER_ROOT/Plug-ins/Area.png"))
