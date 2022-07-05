import threading
import time,logging, sys, os
import socket
import pickle
from _thread import *
from pantools.net import announce_service, wait_for_announcement
import json
from pantools import logger
from pantools import recv_dict, recv_size, recv_line, send_dict_json

class JsonTCPClientConnection:
    """ server is a JsonTCPServer """
    def __init__(self, sock: socket, server) -> None:
        self.sock = sock
        self.server = server
        self.filenum = 0

    def start_reader(self) -> None:    
        start_new_thread(self.read_thread, ())

    def getPeerName(self)  -> str:
        try:
            return self.sock.getpeername()
        except:
            return "<unknown/closed>"

    def getSocket(self) -> socket:
        return self.sock

    def send_msg(self, msg):
        send_dict_json(self.sock, msg)

    #
    # Thread started for each connection!
    #
    def read_thread(self):

        # logger.debug("Starting thread for socket {}".format(self.sock))
        srcaddr, srcport = self.sock.getpeername()
        while True:
            try:
                line = recv_line(self.sock)
                # convert the string to a json/dict
                j = json.loads(line)
                # ask owning server to handle message
                self.server.handle_message(self, j)

            except Exception as e:
                #logger.error(str(e))
                #logger.error("Exception when reading/converting/handling incoming message! Closing connection!")
                self.server.read_exception(self, e)
                self.sock.close()
                return # close thread!
