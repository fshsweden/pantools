import threading
import time,logging, sys, os
import socket
import pickle
from _thread import *
from pantools.net import announce_service, wait_for_announcement
import json

from pantools import logger
from pantools import recv_dict, recv_size, recv_line

class JsonClientConnection:
    """ server is a TCPServer """
    def __init__(self, sock: socket, server) -> None:
        self.sock = sock
        self.server = server
        self.clientname = "clientname_not_set"
        self.clienttype = "clienttype_not_set"
        self.clientid = "clientid_not_set"
        self.filenum = 0

    def start_reader(self):    
        start_new_thread(self.read_thread, ())

    def getPeerName(self):
        return self.sock.getpeername()

    def getSocket(self) -> socket:
        return self.sock

    def set_clientname(self, clientname) -> None:
        self.clientname = clientname

    def get_clientname(self) -> str:
        return self.clientname

    def set_clienttype(self, clienttype) -> None:
        self.clienttype = clienttype

    def get_clienttype(self) -> str:
        return self.clienttype

    def set_clientid(self, clientid) -> None:
        self.clientid = clientid

    def get_clientid(self) -> str:
        return self.clientid

    def save_buffer(self, buf: bytes):
        self.filenum=self.filenum+1
        filename = f"image-file-{self.filenum}.pkl"
        with open(filename, "wb") as mypicklefile:
            pickle.dump(buf, mypicklefile)

    #
    # Thread started for each connection!
    #
    def read_thread(self):

        logger.debug("Starting thread for socket {}".format(self.sock))
        srcaddr, srcport = self.sock.getpeername()
        logger.debug("Startar recv_size() loop")
        while True:
            buf = bytes()
            try:
                line = recv_line(self.sock)
                print(f"Read line-terminated string: {line}")
                try:
                    j = json.loads(line)
                    self.server.handle_message(self, j)
                except:
                    pass

            except Exception as e:
                logger.error(str(e))
                logger.info("Exception when reading incoming message! Closing connection!")

                self.save_buffer(buf)
                self.server.read_exception(self, e)
                self.sock.close()
                return # close thread!

