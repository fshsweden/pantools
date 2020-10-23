import threading
import time,logging, sys, os
import socket
import pickle
from _thread import *
from pantools.net import announce_service, wait_for_announcement

from .logger import logger
from .send_recv import send_json, send_size, recv_size
#from .TCPServer import TCPServer

class ClientConnection:
    """ server is a TCPServer """
    def __init__(self, sock: socket, server) -> None:
        self.sock = sock
        self.server = server
        self.hostname = "unknown"
        self.hosttype = "unknown"
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

    #
    # Thread started for each connection!
    #
    def read_thread(self):

        logger.debug("Starting thread for socket {}".format(self.sock))
        srcaddr, srcport = self.sock.getpeername()

        logger.debug("Startar recv_size() loop")
        while True:
            try:
                data = recv_size(self.sock)
                obj = pickle.loads(data)
                self.server.handle_message(self, obj)

            except Exception as e:
                logger.error(str(e))
                logger.info("Apparently the client hung up! Closing connection!")
                #self.server.remove_client(self.sock)
                self.server.read_exception(self, e)
                self.sock.close()
                return # close thread!

