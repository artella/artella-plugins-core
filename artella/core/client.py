#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaApp Python client implementation
"""

from __future__ import print_function, division, absolute_import

import json
import logging
import urllib2

from artella.core import consts

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

        req = urllib2.Request('http://{}:{}/v2/localserve/auth/challenge-file-path'.format(self._host, self._port))
        rsp = self._communicate(req, skip_auth=True)

        return rsp

    def update_auth_challenge(self):
        """
        Collects some data from a local file to confirm we are running on the same that
        Artella drive is running.

        :return:
        """

        if not self._challenge_path:
            pass

        return False

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

        req = urllib2.Request('http://{}:{}/v2/localserve/ping'.format(self._host, self._port))
        rsp = self._communicate(req, skip_auth=True)

        return rsp

    # ==============================================================================================================
    # INTERNAL
    # ==============================================================================================================

    def _communicate(self, req, data=None, skip_auth=False):
        """
        Internal function that sends a request to ArtellaDriver server
        :param req: urllib2.Request, URL request object
        :param data: str, additional encoded data to send to the server
        :param skip_auth: bool, Whether authorization check should be skip or not
        :return: dict, dictionary containing the answer from the server.
            If the call is not valid a dictionary containing the url and error message is returned.
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
            rsp = urllib2.urlopen(req, data)
        except urllib2.URLError as exc:
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
            try:
                json_data = json.loads(raw_data)
            except Exception as exc:
                logging.debug('Artella data response: "{}"'.format(raw_data))
                logging.error(exc)
                return raw_data
            else:
                logging.debug('ArtellaDrive JSON response: "{}"'.format(json_data))


if __name__ == '__main__':
    artella_cli = ArtellaDriveClient.get()
    print(artella_cli.ping())
