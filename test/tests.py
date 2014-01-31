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
        self.put_file()
        #assert self.fetch_file() == self.get_file_contents()
        self.enable_wifi()
        self.assert_wifi_enabled()
        self.disable_wifi()
        self.assert_wifi_disabled()

    def create_file(self):
        pass

    def put_file(self):
        pass

    def fetch_file(self):
        pass

    def get_file_contents(self):
        return bytes(range(256))

    def get_wlan1(self):
        response = self.api.talk(['/interface/wireless/print', '?name=wlan1'])
        assert response[0][0] == b'!re'
        return response[0][1]

    def enable_wifi(self):
        id = self.get_wlan1()[b'.id'].decode('ascii')
        self.api.talk(['/interface/wireless/set', '=.id=' + id, '=disabled=false'])

    def disable_wifi(self):
        id = self.get_wlan1()[b'.id'].decode('ascii')
        self.api.talk(['/interface/wireless/set', '=.id=' + id, '=disabled=true'])

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
    api.login('api', b'') 
    RosapiTest(api).test()
    sock.close()
