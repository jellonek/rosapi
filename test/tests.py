import socket
import sys
import time

import rosapi
from rosapi import socket_utils

class RosapiTest(object):
    def __init__(self, api):
        self.api = api

    def test(self):
        self.create_file()
        self.assert_file_exists()
        self.put_file(80)
        assert self.get_file_contents(80) == self.fetch_file()
        self.enable_wifi()
        self.assert_wifi_enabled()
        self.disable_wifi()
        self.assert_wifi_disabled()

    def create_file(self):
        self.api.talk([b'/interface/wireless/export', b'=file=testfile'])

    def assert_file_exists(self):
        response = self.api.talk([b'/file/print', b'?name=testfile.rsc'])
        assert len(response) == 2

    def put_file(self, length):
        response = self.api.talk([b'/file/print', b'?name=testfile.rsc', b'=detail='])
        id = response[0][1][b'.id']
        self.api.talk([b'/file/set', b'=.id=' + id, b'=contents=' + self.get_file_contents(length)])

    def fetch_file(self):
        response = self.api.talk([b'/file/print', b'?name=testfile.rsc', b'=detail='])
        assert response[0][0] == b'!re'
        return response[0][1][b'contents']

    def get_file_contents(self, length):
        return bytes(b % 256 for b in range(length))

    def get_wlan1(self):
        response = self.api.talk([b'/interface/wireless/print', b'?name=wlan1'])
        assert response[0][0] == b'!re'
        return response[0][1]

    def enable_wifi(self):
        id = self.get_wlan1()[b'.id']
        self.api.talk([b'/interface/wireless/set', b'=.id=' + id, b'=disabled=false'])

    def disable_wifi(self):
        id = self.get_wlan1()[b'.id']
        self.api.talk([b'/interface/wireless/set', b'=.id=' + id, b'=disabled=true'])

    def assert_wifi_enabled(self):
        assert self.get_wlan1()[b'disabled'] == b'false'
        

    def assert_wifi_disabled(self):
        assert self.get_wlan1()[b'disabled'] == b'true'

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15.0)
    sock.connect(('10.9.0.14', 8728))
    socket_utils.set_keepalive(sock, after_idle_sec=10)

    api = rosapi.RosAPI(sock)
    api.login(b'api', b'') 
    RosapiTest(api).test()
    sock.close()
