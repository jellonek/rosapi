#!/usr/bin/python

import select
import socket
import sys

import rosapi


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((sys.argv[1], 8728))  
    apiros = rosapi.ApiRos(s);             
    apiros.login(sys.argv[2], sys.argv[3]);

    inputsentence = []

    while 1:
        r = select.select([s, sys.stdin], [], [], None)
        if s in r[0]:
            # something to read in socket, read sentence
            apiros.readSentence()

        if sys.stdin in r[0]:
            # read line from input and strip off newline
            l = sys.stdin.readline()
            l = l[:-1]

            # if empty line, send sentence and start with new
            # otherwise append to input sentence
            if l == '':
                apiros.writeSentence(inputsentence)
                inputsentence = []
            else:
                inputsentence.append(l)

if __name__ == '__main__':
    main()
