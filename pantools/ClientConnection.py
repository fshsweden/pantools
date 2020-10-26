import threading
import time,logging, sys, os
import socket
import pickle
from _thread import *
from pantools.net import announce_service, wait_for_announcement

from .logger import logger
from .send_recv import recv_dict, recv_size
#from .TCPServer import TCPServer

class ClientConnection:
    """ server is a TCPServer """
    def __init__(self, sock: socket, server) -> None:
        self.sock = sock
        self.server = server
        self.hostname = "unknown"
        self.hosttype = "unknown"

        self.filenum = 0

    def start_reader(self):    
        start_new_thread(self.read_thread, ())

    def getPeerName(self):
        return self.sock.getpeername()

    def getSocket(self) -> socket:
        return self.sock

    def set_hostname(self, hostname) -> None:
        self.hostname = hostname

    def get_hostname(self) -> str:
        return self.hostname

    def set_type(self, hosttype) -> None:
        self.hosttype = hosttype

    def get_type(self) -> str:
        return self.hosttype

    def get_id(self) -> str:
        return f"{self.hostname} : {self.hosttype}"

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
                buf = recv_size(self.sock)
                #self.save_buffer(buf)

                logger.debug(f"Size of raw data:{len(buf)}")
                obj = pickle.loads(buf)
                logger.debug(f"Size of unpickled data:{len(obj)}")

                self.server.handle_message(self, obj)

            except Exception as e:
                logger.error(str(e))
                logger.info("Exception when reading incoming message! Closing connection!")

                self.save_buffer(buf)
                #TEMPORARILY DISABLED
                self.server.read_exception(self, e)
                self.sock.close()
                return # close thread!

