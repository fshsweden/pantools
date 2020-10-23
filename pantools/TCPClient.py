import struct
import socket
import pickle
import threading
from _thread import *
import queue
from pantools.net import announce_service, wait_for_announcement
import time

from .logger import logger
from .send_recv import send_json, send_size, recv_size

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
        self.msg_handler = None
        self.exception_handler = None
        self.connection_status_handler = None
        
        self.inq = queue.Queue(10000)
        self.outq = queue.Queue(10000)

        self.quit_write_thread = False
        self.quit_read_thread = False


    # ------------------------------------------------------------
    # TCPClient:add_connection_status_handler
    # ------------------------------------------------------------
    def add_connection_status_handler(self, status_handler):
        self.connection_status_handler = status_handler

    # ------------------------------------------------------------
    # TCPClient:add_msg_handler
    # ------------------------------------------------------------
    def add_msg_handler(self, msg_handler):
        self.msg_handler = msg_handler

    # ------------------------------------------------------------
    # TCPClient:add_exception_handler
    # ------------------------------------------------------------
    def add_exception_handler(self, exception_handler):
        self.exception_handler = exception_handler

    # ------------------------------------------------------------
    # If you dont know the service ip/port, use the advertisement!
    # ------------------------------------------------------------
    def start_client(self):
        logger.info("start_client. waiting for announcement before connecting...")
        (service_host, service_port) = wait_for_announcement(self.adv_port, self.adv_magic)
        logger.info("start_client. got announcement: {} {}".format(service_host, service_port))
        self.connect_to_service(service_host, service_port)

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

    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def write_thread(self):
        logger.debug("+++ ENTR +++ write_thread()")
        while (not self.quit_write_thread):
            if self.outq.empty():
                time.sleep(0.5)
            else:
                out_msg = self.outq.get()

                try:
                    send_size(self.sock, out_msg)
                except Exception as e:
                    self.handle_exception(e)
                    logger.error(f"Exception: {e} - exiting write thread")
                    return


    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def handle_message(self, msg):
        #self.inq.put(msg)
        
        if self.msg_handler is not None:
            self.msg_handler(msg)


    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def handle_exception(self, e):
        if self.exception_handler is not None:
            self.exception_handler(e)

    # ------------------------------------------------------------
    #
    # ------------------------------------------------------------
    def handle_connection_status(self, status):
        if self.connection_status_handler is not None:
            self.connection_status_handler(status)

    #
    #
    #
    def subscribe(self, msgtype):

        # send a subscription message
        self.send_msg({
                "message": "subscribe",
                "msgtype": msgtype,
                "type": "json-object",
                "threadname": "none",
                "hostname": socket.gethostname()
            })


    #   BUG: DONT USE BOTH THIS AND THE QUEUE VERSION AT THE SAME TIME!
    #
    #
    def send_msg_direct(self, msg_json):
        msg_encoded = pickle.dumps(msg_json)
        send_size(self.sock, msg_encoded)

    #   BUG: DONT USE BOTH THIS AND THE DIRECT VERSION AT THE SAME TIME!
    #
    #
    def send_msg(self, msg_json):
        msg_encoded = pickle.dumps(msg_json)
        self.outq.put(msg_encoded)
