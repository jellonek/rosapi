import rosapi
from rosapi import socket_utils


class RosapiTest(object):
    def __init__(self, api):
        self.api = api

    def test(self):
        self.create_file()
        self.assert_file_exists()
        self.put_file(0x40)
        assert get_test_file_contents(0x40) == self.fetch_file()
        self.put_file(0x1ff)
        assert get_test_file_contents(0x1ff) == self.fetch_file()
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
        response = self.api.talk([b'/file/print',
                                  b'?name=testfile.rsc', b'=detail='])
        file_id = response[0][1][b'.id']
        self.api.talk([b'/file/set', b'=.id=' + file_id,
                       b'=contents=' + get_test_file_contents(length)])

    def fetch_file(self):
        response = self.api.talk([b'/file/print', b'?name=testfile.rsc',
                                  b'=detail='])
        assert response[0][0] == b'!re'
        return response[0][1][b'contents']

    def get_wlan1(self):
        response = self.api.talk([b'/interface/wireless/print',
                                  b'?name=wlan1'])
        assert response[0][0] == b'!re'
        return response[0][1]

    def enable_wifi(self):
        file_id = self.get_wlan1()[b'.id']
        self.api.talk([b'/interface/wireless/set', b'=.id=' + file_id,
                       b'=disabled=false'])

    def disable_wifi(self):
        file_id = self.get_wlan1()[b'.id']
        self.api.talk([b'/interface/wireless/set', b'=.id=' + file_id,
                       b'=disabled=true'])

    def assert_wifi_enabled(self):
        assert self.get_wlan1()[b'disabled'] == b'false'

    def assert_wifi_disabled(self):
        assert self.get_wlan1()[b'disabled'] == b'true'


class RouterboardAPITest(object):
    def __init__(self, api):
        self.api = api

    def test(self):
        self.get_wlan1()
        self.enable_wifi()
        self.assert_wifi_enabled()
        self.disable_wifi()
        self.assert_wifi_disabled()

    def get_wlan1(self):
        resource = self.api.get_resource('/interface/wireless')
        response = resource.get(name='wlan1')
        assert 1 == len(response)
        return response[0]

    def enable_wifi(self):
        resource = self.api.get_resource('/interface/wireless')
        resource.set(disabled='false', id=self.get_wlan1()['id'])

    def disable_wifi(self):
        resource = self.api.get_resource('/interface/wireless')
        resource.set(disabled='true', id=self.get_wlan1()['id'])

    def assert_wifi_enabled(self):
        assert self.get_wlan1()['disabled'] == 'false'

    def assert_wifi_disabled(self):
        assert self.get_wlan1()['disabled'] == 'true'


class RouterboardAPIBaseResourceTest(object):
    def __init__(self, api):
        self.api = api

    def test(self):
        self.assert_file_exists()
        self.put_file(0x40)
        assert get_test_file_contents(0x40) == self.fetch_file()
        self.put_file(0x1ff)
        assert get_test_file_contents(0x1ff) == self.fetch_file()
        self.get_wlan1()
        self.enable_wifi()
        self.assert_wifi_enabled()
        self.disable_wifi()
        self.assert_wifi_disabled()

    def get_wlan1(self):
        resource = self.api.get_base_resource('/interface/wireless')
        response = resource.get(name=b'wlan1')
        assert 1 == len(response)
        return response[0]

    def enable_wifi(self):
        resource = self.api.get_base_resource('/interface/wireless')
        resource.set(disabled=b'false', id=self.get_wlan1()['id'])

    def disable_wifi(self):
        resource = self.api.get_base_resource('/interface/wireless')
        resource.set(disabled=b'true', id=self.get_wlan1()['id'])

    def assert_wifi_enabled(self):
        assert self.get_wlan1()['disabled'] == b'false'

    def assert_wifi_disabled(self):
        assert self.get_wlan1()['disabled'] == b'true'

    def assert_file_exists(self):
        response = self.api.get_base_resource('/file').get(
            name=b'testfile.rsc')
        assert len(response) == 1

    def put_file(self, length):
        response = self.api.get_base_resource('/file').get(
            name=b'testfile.rsc')
        file_id = response[0]['id']
        self.api.get_base_resource('/file').set(
            id=file_id, contents=get_test_file_contents(length))

    def fetch_file(self):
        response = self.api.get_base_resource('/file').get(
            name=b'testfile.rsc')
        file_id = response[0]['id']
        response = self.api.get_base_resource('/file').detailed_get(id=file_id)
        return response[0]['contents']


def get_test_file_contents(length):
    return bytes(b % 256 for b in range(length))


if __name__ == '__main__':
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15.0)
    sock.connect(('10.9.0.14', 8728))
    socket_utils.set_keepalive(sock, after_idle_sec=10)

    api = rosapi.RosAPI(sock)
    api.login(b'api', b'')
    RosapiTest(api).test()
    sock.close()
    with rosapi.RouterboardAPI('10.9.0.14') as api:
        RouterboardAPITest(api).test()
        RouterboardAPIBaseResourceTest(api).test()
