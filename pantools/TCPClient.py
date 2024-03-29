import struct
import socket
import pickle
import threading
from _thread import *
import queue
from pantools.net import announce_service, wait_for_announcement
import time
import uuid

from pantools import logger
from pantools.send_recv import send_json, send_size, recv_size

# ================================================================
#
# ================================================================
class TCPClient:

    # ------------------------------------------------------------
    # listen for advertisements on port XYZ, listen for ABC keyword
    # ------------------------------------------------------------
    def __init__(self, magic, port) -> None:
        self.sock = None
        self.adv_magic = magic
        self.adv_port = port
        
        self.inq = queue.Queue(10000)
        self.outq = queue.Queue(10000)

        self.quit_write_thread = False
        self.quit_read_thread = False

        self.clientid = str(uuid.uuid1())

    # ------------------------------------------------------------
    # If you dont know the service ip/port, use the advertisement!
    # ------------------------------------------------------------
    def start_client(self):
        logger.info("start_client. waiting for announcement before connecting...")
        (service_host, service_port) = wait_for_announcement(self.adv_port, self.adv_magic)
        logger.info("start_client. got announcement: {} {}".format(service_host, service_port))
        self.connect_to_service(service_host, service_port)

    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def send_announce(self, clienttype):

        msg = self.msg_template("announce")
        msg["clientid"] = self.clientid
        msg["clienttype"] = clienttype
        self.send_msg(msg)

    def msg_template(self, message):
        return {
            "message": message,
            "clientid": self.clientid,
            "hostname": socket.gethostname(),
        }

    def send_get_clients(self):
        msg = self.msg_template("getclients")
        self.send_msg(msg)

    #
    #
    #
    def send_subscribe(self, message, message_source):

        msg = self.msg_template("subscribe")
        msg["message-arg"] = message
        msg["message-source"] =  message_source

        self.send_msg(msg)


    # ------------------------------------------------------------
    # Connect and start a reader loop.
    # ------------------------------------------------------------
    def connect_to_service(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            logger.info("Connecting to: {}:{}".format(ip, port))
            self.sock.connect((ip, port))
            logger.info("Connected! - Starting worker threads")
            self.handle_connection_status("connected")
            
            start_new_thread(self.write_thread, ())
            start_new_thread(self.read_thread, ())

        except Exception as e:
            logger.error("Got an exception {} trying to connect".format(str(e)))
            self.handle_connection_status("disconnected")

        logger.debug("Exiting connect_to_service()")

    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def inq_size(self):
        return self.inq.qsize()

    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def outq_size(self):
        return self.outq.qsize()
            
    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def read_thread(self):
        logger.debug("+++ ENTR +++ read_thread()")
        try:
            cont = True
            while cont:
                try:
                    msg_encoded = recv_size(self.sock)
                    msg = pickle.loads(msg_encoded)
                    self.handle_message(msg)
                except Exception as e:
                    logger.error("Exception in read_thread...")
                    logger.error(str(e))
                    self.handle_exception(e)
                    cont = False
        finally:
            logger.debug("Closing socket from read_thread...")
            self.sock.close()
            logger.debug("+++ EXIT +++ read_thread()")
            self.handle_connection_status("disconnected")

        logger.error(f"Exiting read-thread!!")

    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def write_thread(self):
        logger.debug("+++ ENTR +++ write_thread()")
        while not self.quit_write_thread:

            out_msg = self.outq.get(block=True)

            try:
                send_size(self.sock, out_msg)
            except Exception as e:
                self.handle_exception(e)
                logger.error(f"Exception: {e} - exiting write thread")

                self.quit_write_thread = True
                self.quit_read_thread = True
                return

        logger.error(f"Exiting write-thread since quit:_thread flag was set!!")

    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def handle_message(self, msg):
        self.inq.put(msg)


    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def handle_exception(self, e):
        msg = {
            "message": "exception",
            "exception": e
        }
        self.inq.put(msg)

    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def handle_connection_status(self, status):
        msg = {
            "message": "connection_status",
            "status": status
        }
        self.inq.put(msg)

    def send_msg(self, msg_json):
        msg_encoded = pickle.dumps(msg_json)
        self.outq.put(msg_encoded)

    def read_msg(self):
        m = self.inq.get(block=True)
        return m
        
