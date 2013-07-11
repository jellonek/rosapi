#!/usr/bin/python

import logging
import select
import socket
import sys

import rosapi


def main():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((sys.argv[1], 8728))  
    apiros = rosapi.RosAPI(s)
    apiros.login(sys.argv[2], sys.argv[3])

    inputsentence = []

    while True:
        try:
            r = select.select([s, sys.stdin], [], [], None)
        except KeyboardInterrupt:
            return

        if s in r[0]:
            # something to read in socket, read sentence
            apiros.read_sentence()

        if sys.stdin in r[0]:
            # read line from input and strip off newline
            line = sys.stdin.readline().strip()

            # if empty line, send sentence and start with new
            # otherwise append to input sentence
            if not line:
                if not inputsentence:
                    return
                apiros.write_sentence(inputsentence)
                inputsentence = []
            else:
                inputsentence.append(line)

if __name__ == '__main__':
    main()
