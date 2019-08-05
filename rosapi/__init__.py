from __future__ import unicode_literals

import binascii
import logging
import socket
import ssl
import sys

from hashlib import md5

from .retryloop import RetryError
from .retryloop import retryloop
from .socket_utils import set_keepalive

PY2 = sys.version_info[0] < 3
logger = logging.getLogger(__name__)


class RosAPIError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        if isinstance(self.value, dict) and self.value.get('message'):
            return self.value['message']
        elif isinstance(self.value, list):
            elements = (
                '%s: %s' %
                (element.__class__, str(element)) for element in self.value
            )
            return '[%s]' % (', '.join(element for element in elements))
        else:
            return str(self.value)


class RosAPIConnectionError(RosAPIError):
    pass


class RosAPIFatalError(RosAPIError):
    pass


class RosApiLengthUtils(object):
    def __init__(self, api):
        self.api = api

    def write_lenght(self, length):
        self.api.write_bytes(self.length_to_bytes(length))

    def length_to_bytes(self, length):
        if length < 0x80:
            return self.to_bytes(length)
        elif length < 0x4000:
            length |= 0x8000
            return self.to_bytes(length, 2)
        elif length < 0x200000:
            length |= 0xC00000
            return self.to_bytes(length, 3)
        elif length < 0x10000000:
            length |= 0xE0000000
            return self.to_bytes(length, 4)
        else:
            return self.to_bytes(0xF0) + self.to_bytes(length, 4)

    def read_length(self):
        b = self.api.read_bytes(1)
        i = self.from_bytes(b)
        if (i & 0x80) == 0x00:
            return i
        elif (i & 0xC0) == 0x80:
            return self._unpack(1, i & ~0xC0)
        elif (i & 0xE0) == 0xC0:
            return self._unpack(2, i & ~0xE0)
        elif (i & 0xF0) == 0xE0:
            return self._unpack(3, i & ~0xF0)
        elif (i & 0xF8) == 0xF0:
            return self.from_bytes(self.api.read_bytes(4))
        else:
            raise RosAPIFatalError('Unknown value: %x' % i)

    def _unpack(self, times, i):
        res = self.to_bytes(i) + self.api.read_bytes(times)
        return self.from_bytes(res)

    if PY2:
        def from_bytes(self, data):
            data_values = [ord(char) for char in data]
            value = 0
            for byte_value in data_values:
                value <<= 8
                value += byte_value
            return value

        def to_bytes(self, i, size=1):
            data = []
            for _ in xrange(size):
                data.append(chr(i & 0xff))
                i >>= 8
            return ''.join(reversed(data))
    else:
        def from_bytes(self, data):
            return int.from_bytes(data, 'big')

        def to_bytes(self, i, size=1):
            return i.to_bytes(size, 'big')


class RosAPI(object):
    """Routeros api"""

    def __init__(self, socket):
        self.socket = socket
        self.length_utils = RosApiLengthUtils(self)

    def login(self, username, password, legacy=False):
        if legacy:
            for _, attrs in self.talk([b'/login']):
                token = binascii.unhexlify(attrs[b'ret'])
            md5_hash = md5(b'\x00' + password + token).hexdigest().encode('ascii')
            self.talk([b'/login', b'=name=' + username,
                    b'=response=00' + md5_hash])
        else:
            self.talk([b'/login', b'=name=' + username, b'=password=' + password])

    def talk(self, words):
        if self.write_sentence(words) == 0:
            return
        output = []
        while True:
            input_sentence = self.read_sentence()
            if not len(input_sentence):
                continue
            attrs = {}
            reply = input_sentence.pop(0)
            for line in input_sentence:
                try:
                    second_eq_pos = line.index(b'=', 1)
                except IndexError:
                    attrs[line[1:]] = b''
                else:
                    attrs[line[1:second_eq_pos]] = line[second_eq_pos + 1:]
            output.append((reply, attrs))
            if reply == b'!done':
                if output[0][0] == b'!trap':
                    raise RosAPIError(output[0][1])
                if output[0][0] == b'!fatal':
                    self.socket.close()
                    raise RosAPIFatalError(output[0][1])
                return output

    def write_sentence(self, words):
        words_written = 0
        for word in words:
            self.write_word(word)
            words_written += 1
        self.write_word(b'')
        return words_written

    def read_sentence(self):
        sentence = []
        while True:
            word = self.read_word()
            if not len(word):
                return sentence
            sentence.append(word)

    def write_word(self, word):
        logger.debug('>>> %s' % word)
        self.length_utils.write_lenght(len(word))
        self.write_bytes(word)

    def read_word(self):
        word = self.read_bytes(self.length_utils.read_length())
        logger.debug('<<< %s' % word)
        return word

    def write_bytes(self, data):
        sent_overal = 0
        while sent_overal < len(data):
            try:
                sent = self.socket.send(data[sent_overal:])
            except socket.error as e:
                raise RosAPIConnectionError(str(e))
            if sent == 0:
                raise RosAPIConnectionError('Connection closed by remote end.')
            sent_overal += sent

    def read_bytes(self, length):
        received_overal = b''
        while len(received_overal) < length:
            try:
                received = self.socket.recv(
                    length - len(received_overal))
            except socket.error as e:
                raise RosAPIConnectionError(str(e))
            if len(received) == 0:
                raise RosAPIConnectionError('Connection closed by remote end.')
            received_overal += received
        return received_overal


class BaseRouterboardResource(object):
    def __init__(self, api, namespace):
        self.api = api
        self.namespace = namespace

    def call(self, command, set_kwargs, query_kwargs=None):
        query_kwargs = query_kwargs or {}
        query_arguments = self._prepare_arguments(True, **query_kwargs)
        set_arguments = self._prepare_arguments(False, **set_kwargs)
        query = ([('%s/%s' % (self.namespace, command)).encode('ascii')] +
                 query_arguments + set_arguments)
        response = self.api.api_client.talk(query)

        output = []
        for response_type, attributes in response:
            if response_type == b'!re':
                output.append(self._remove_first_char_from_keys(attributes))

        return output

    @staticmethod
    def _prepare_arguments(is_query, **kwargs):
        command_arguments = []
        for key, value in kwargs.items():
            if key in ['id', 'proplist']:
                key = '.%s' % key
            key = key.replace('_', '-')
            selector_char = '?' if is_query else '='
            command_arguments.append(
                ('%s%s=' % (selector_char, key)).encode('ascii') + value)

        return command_arguments

    @staticmethod
    def _remove_first_char_from_keys(dictionary):
        elements = []
        for key, value in dictionary.items():
            key = key.decode('ascii')
            if key in ['.id', '.proplist']:
                key = key[1:]
            elements.append((key, value))
        return dict(elements)

    def get(self, **kwargs):
        return self.call('print', {}, kwargs)

    def detailed_get(self, **kwargs):
        return self.call('print', {'detail': b''}, kwargs)

    def set(self, **kwargs):
        return self.call('set', kwargs)

    def add(self, **kwargs):
        return self.call('add', kwargs)

    def remove(self, **kwargs):
        return self.call('remove', kwargs)


class RouterboardResource(BaseRouterboardResource):
    def detailed_get(self, **kwargs):
        return self.call('print', {'detail': ''}, kwargs)

    def call(self, command, set_kwargs, query_kwargs=None):
        query_kwargs = query_kwargs or {}
        result = super(RouterboardResource, self).call(
            command, self._encode_kwargs(set_kwargs),
            self._encode_kwargs(query_kwargs))
        for item in result:
            for k in item:
                item[k] = item[k].decode('ascii')
        return result

    def _encode_kwargs(self, kwargs):
        return dict((k, v.encode('ascii')) for k, v in kwargs.items())


class RouterboardAPI(object):
    def __init__(self, host, username='api', password='', port=8728, ssl=False, legacy_login=False):
        self.host = host
        self.username = username
        self.password = password
        self.socket = None
        self.port = port
        self.ssl = ssl
        self.legacy_login = legacy_login
        self.reconnect()

    def __enter__(self):
        return self

    def __exit__(self, _, __, ___):
        self.close_connection()

    def reconnect(self):
        if self.socket:
            self.close_connection()
        try:
            for retry in retryloop(10, delay=0.1, timeout=30):
                try:
                    self.connect()
                    self.login()
                except socket.error:
                    retry()
        except (socket.error, RetryError) as e:
            raise RosAPIConnectionError(str(e))

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15.0)
        sock.connect((self.host, self.port))
        set_keepalive(sock, after_idle_sec=10)
        if self.ssl:
            try:
                self.socket = ssl.wrap_socket(sock)
            except ssl.SSLError as e:
                raise RosAPIConnectionError(str(e))
        else:
            self.socket = sock
        self.api_client = RosAPI(self.socket)

    def login(self):
        self.api_client.login(self.username.encode('ascii'),
                              self.password.encode('ascii'),
                              self.legacy_login)

    def get_resource(self, namespace):
        return RouterboardResource(self, namespace)

    def get_base_resource(self, namespace):
        return BaseRouterboardResource(self, namespace)

    def close_connection(self):
        self.socket.close()
