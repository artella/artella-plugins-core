#!/usr/bin/env python
import base64
import hashlib
import json
import logging
import os
import random
import socket
import threading
import urllib
import urllib2
import urlparse

# local environment variable for root folder location
# when the ArtellaApp is not accessible this is used as a fallback
#
ALR = "ARTELLA_FOLDER_ROOT"
ARTELLA_URI_SCHEME = "artella"
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 29282
CRLF = "\r\n"


logging.basicConfig(level=logging.INFO)


def get_client():
    cli = ArtellaAppClient()
    # challenge value gets updated when the Artella App restarts
    # need to check this each time in case the local server got restarted
    cli.auth_challenge_update()
    return cli


class SocketBuffer(object):
    """ often when working with 3rd-party applications we are limited
        to using an embeded python instance which is lacking helpful
        packages. in an effort to keep our plugin "light weight" and
        and easy-to-install single file, we do some of the heavy lifting
        here instead of importing another package and/or manipulate the
        PYTHON_PATH.
    """

    def __init__(self, sock):
        super(SocketBuffer, self).__init__()
        self.sock = sock
        self.buf = ""

    def read_line(self):
        line = ""
        while True:
            c = self.get_char()
            line += c
            if c == "\n":
                return line

    def get_char(self):
        if len(self.buf) == 0:
            self.buf = self.sock.recv(2000)
        r = self.buf[0]
        self.buf = self.buf[1:]
        return r

    def get_chars(self, count):
        cc = ""
        for x in xrange(0, count):
            cc += self.get_char()
        return cc


def make_ws_key():
    # https://tools.ietf.org/html/rfc6455
    key = base64.b64encode(str(int(random.random() * 9999999)))
    h = hashlib.sha1()
    h.update(key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    expected_key_response = base64.b64encode(h.digest())
    return key, expected_key_response


_auth_header = "artella-file-challenge artella-challenge {}"
_challenge_path = None


class ArtellaAppClient():

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self._host = host
        self._port = port
        self._auth_header = None
        self._batch_ids = set()
        self._socket_buffer = None

    def auth_challenge_update(self):
        """ collect some data from a local file to confirm we are running
            on the same machine that the Artella app is running.
        """
        global _challenge_path
        if not _challenge_path:
            rsp = self.get_challenge_file_path()
            if not rsp:
                logging.error("unable to get challenge file path %s" % rsp)
                self._auth_header = None
                return self._auth_header
            _challenge_path = rsp.get("challenge_file_path")
        if not os.path.exists(_challenge_path):
            logging.error("challenge file not found %s" % _challenge_path)
            self._auth_header = None
            return self._auth_header
        with open(os.path.expanduser(_challenge_path)) as fp:
            b = fp.read()
        self._auth_header = _auth_header.format(b[:64].encode("hex"))
        return self._auth_header

    def ws_connect(self):
        """ conncect to the local ArtellaApp via websocket
            so that we can listen for realtime events
        """
        server_address = (self._host, self._port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.info("connecting to ArtellaApp websocket: %s:%s"
                     % server_address)
        try:
            sock.connect(server_address)
        except Exception as e:
            logging.error("plugin failed to connect to the "
                          "ArtellaApp websocket: %s" % e)
            return

        self.ws_send_request(sock)
        self._socket_buffer = SocketBuffer(sock)
        rsp = self.ws_read_response()
        return rsp

    def ws_send_request(self, sock):
        key, expected_key_response = make_ws_key()
        if not self.auth_challenge_update():
            logging.error("unable to authenticate")
            return
        path = "/v2/localserve/ws"
        r = [
            "GET {} HTTP/1.1".format(path),
            "Upgrade: websocket",
            "Connection: Upgrade",
            "Host: {}:{}".format(self._host, self._port),
            "Sec-WebSocket-Key: {}".format(key),
            "Sec-WebSocket-Version: 13",
            "Authorization: {}".format(self._auth_header),
        ]
        rr = CRLF.join(r) + CRLF + CRLF
        logging.debug("plugin sending websocket access request to "
                      " the local ArtellaApp: %s" % rr)
        sock.sendall(rr)
        return

    def ws_read_response(self):
        logging.debug("reading socket response...")
        line = ""
        while line != CRLF:
            line = self._socket_buffer.read_line()
        return line

    def ws_listen(self):
        self.ws_connect()
        if not self._socket_buffer:
            logging.error("socket not connected")
            return
        threading.Thread(
            target=self._pull_messages,
        ).start()
        return

    def _pull_messages(self):
        logging.info("listening for commands on websocket")
        while True:
            msg = self._get_message()
            # do something useful with the message here
            logging.info("message recieved: %s" % msg)
        return

    def _get_message(self):
        opcode = ord(self._socket_buffer.get_char())
        v = ord(self._socket_buffer.get_char())
        if opcode != 129:
            raise Exception("not a final text frame :" + str(opcode))
        if v < 126:
            length = v
        elif v == 126:
            a = ord(self._socket_buffer.get_char()) << 8
            b = ord(self._socket_buffer.get_char())
            length = a + b
        elif v == 127:
            # 8 byte payload length - we won't have any of these
            raise Exception("unsuported payload length")
        else:
            raise Exception("bad payload length: " + str(v))

        payload = self._socket_buffer.get_chars(length)
        return json.loads(payload)

    def ping(self):
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/ping" %
            (self._host, self._port))
        rsp = self._communicate(req)
        return rsp

    def get_challenge_file_path(self):
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/auth/challenge-file-path" %
            (self._host, self._port))
        rsp = self._communicate(req, skip_auth=True)
        return rsp

    def get_local_root(self):
        """ ask the remote server for the local storage root for this machine
        """
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/kv/settings/workspace" %
            (self._host, self._port))
        ws = self._communicate(req)
        if not ws:
            alr = os.environ.get(ALR, None)
            if alr:
                logging.warning("unable to get local storage root "
                                "using env var: %s" % ALR)
                ws = alr
            else:
                logging.error("unable to get local storage root")
                logging.info("check that the local Artella Studio "
                             "service is running and you have a "
                             "working internet connection")
                logging.info("to work offline set the %s environment variable "
                             "to the appropriate local project directory."
                             % ALR)
        return ws

    def get_storage_id(self):
        """ ask for the storage id of the machine this code is running on
        """
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/kv/settings/machine-id" %
            (self._host, self._port))
        rsp = self._communicate(req)
        return rsp

    def get_metadata(self):
        """ ask the remote server for general data related to current session
        """
        params = urllib.urlencode({'dump': 'true'})
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/kv/settings?%s" %
            (self._host, self._port, params))
        rsp = self._communicate(req)
        return rsp

    def resolve(self, path):
        if is_already_uri_path(path):
            payload = {'handle': path}
        else:
            payload = {'file_path': path}
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/resolve" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            logging.error("attempting to resolve %s %s"
                          % (path, rsp.get('error')))
        return rsp

    def download(self, artella_uri_list):
        """ pull the file from the remote server
        """
        handles = set()
        for uri in artella_uri_list:
            if not is_already_uri_path(uri):
                uri = path_to_uri(uri)
            uri_parts = urlparse.urlparse(uri)
            handle = uri_parts.path
            handles.add(handle)

        if not handles:
            return {}
        logging.debug("  handles %s" % handles)
        payload = {
            'handles': list(handles),
            'recursive': False,
            'replace_local': True
        }
        logging.debug("   request payload orig: %s" % payload)
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/transfer/download" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            return rsp
        return self.track_response(rsp)

    def upload(self, artella_uri, comment=""):
        """ upload an updated file to the remote server
        """
        uri_parts = urlparse.urlparse(artella_uri)
        handle = uri_parts.path
        payload = {
            'handles': [handle],
            'recursive': False,
            'commit_message': comment
        }
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/transfer/upload" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            return rsp
        return self.track_response(rsp)

    def lock_file(self, artella_uri):
        """ lock the file in the web platform so that other
            users know it is in use.
        """
        payload = {
            'handle': artella_uri,
            'note': 'locked for use by plugin'
        }
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/lock" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            logging.error(rsp.get('error'))
            return False

        return rsp.get('response', False) and rsp.get('status_code', 0) == 200

    def unlock_file(self, artella_uri):
        """ unlock it
        """
        payload = {
            'handle': artella_uri
        }
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/unlock" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            logging.error(rsp.get('error'))
            return False

        return rsp.get('response', False) and rsp.get('status_code', 0) == 200

    def status(self, artella_uri):
        """ get the status of a file from the remote server
        """
        uri_parts = urlparse.urlparse(artella_uri)
        params = urllib.urlencode({'handle': uri_parts.path})
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/fileinfo?%s" %
            (self._host, self._port, params))
        rsp = self._communicate(req)
        if 'error' in rsp:
            return rsp
        # TODO: once we have a reliable way to resolve the record handle
        # back into the abs path, iterate and match on the file name
        for k, v in rsp.iteritems():
            if os.path.basename(k) == os.path.basename(artella_uri):
                return v.get('remote_info', {})
        return rsp

    def get_progress(self):
        """ check for progess of long running transfers
        """
        tx_count_done = 0
        tx_count_total = 0
        tx_bytes_done = 0
        tx_bytes_total = 0
        batches_complete = set()
        for batch_id in self._batch_ids:
            params = urllib.urlencode({
                'batch-id': batch_id,
                'details': True})
            req = urllib2.Request(
                "http://%s:%s/v2/localserve/progress/summary?%s" %
                (self._host, self._port, params))
            v = self._communicate(req)
            tcd = int(v.get('transfer_count_done', 0))
            tct = int(v.get('transfer_count_total', 0))
            tbd = int(v.get('transfer_bytes_download_done', 0))
            tbt = int(v.get('transfer_bytes_download_total', 0))
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

        return (
            int(progress_value * 100),
            tx_count_done,
            tx_count_total,
            tx_bytes_done,
            tx_bytes_total)

    def pause_downloads(self):
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/pause/pause/downloads" %
            (self._host, self._port))
        rsp = self._communicate(req, {"noop": ""})
        return rsp

    def track_response(self, rsp):
        """ extrack batch_id and transfer data from response
            so that we can continue to track progress
        """
        batch_id = rsp.get('batch_id')
        self._batch_ids.add(batch_id)
        return rsp

    def _communicate(self, req, data=None, skip_auth=False):
        logging.debug(">>> making request to ArtellaApp %s"
                      % req.get_full_url())
        if data:
            logging.debug("  request payload dump: %s"
                          % json.loads(data))
        if not self._auth_header and not skip_auth:
            rsp = self.auth_challenge_update()
            if not rsp:
                msg = "unable to authenticate"
                logging.error(msg)
                return {'error': msg,
                        'url': req.get_full_url()}

        req.add_header('Authorization', self._auth_header)

        try:
            rsp = urllib2.urlopen(req, data)
        except urllib2.URLError as e:
            if hasattr(e, 'reason'):
                msg = "failed to reach the local ArtellaApp: %s" \
                    % e.reason
            elif hasattr(e, 'code'):
                msg = "ArtellaApp is unable to fulfill the request: %s" \
                    % e.code
            logging.debug(e)
            logging.error(msg)
            return {'error': msg,
                    'url': req.get_full_url()}
        else:
            raw_data = rsp.read()
            try:
                json_data = json.loads(raw_data)
            except Exception as e:
                logging.debug("  ArtellaApp data response: %s" % raw_data)
                return raw_data
            else:
                logging.debug("  ArtellaApp JSON response: %s" % json_data)
                return json_data


def is_already_uri_path(file_path):
    if not file_path:
        return False
    uri = urlparse.urlparse(file_path)
    return uri.scheme == ARTELLA_URI_SCHEME


def path_to_uri(file_path):
    elp = os.path.abspath(os.path.expandvars(os.path.expanduser(file_path)))
    rsp = get_client().resolve(elp)
    if 'error' in rsp:
        logging.warning("unable to translate path %s %s"
                        % (file_path, rsp.get('error')))
        return file_path

    url_parts = (
        ARTELLA_URI_SCHEME,
        '',
        rsp.get('handle'),
        '',
        '',
        '')
    # 'artella:path/to/file.ext'
    fixed_path = urlparse.urlunparse(url_parts)
    if not is_already_uri_path(fixed_path):
        logging.error("failed to translate %s to uri: %s"
                      % (file_path, fixed_path))
        return file_path
    return fixed_path


if __name__ == "__main__":
    print "testing harness....\n"

    print "connect to the running ArtellaApp"
    print get_client().ping()

    print "\nget location of the challenge file"
    print get_client().get_challenge_file_path()

    print "\nget local storage root"
    print get_client().get_local_root()

    print "\nget machine id"
    print get_client().get_storage_id()
