import socket
from _thread import *
import queue
import uuid
import json

from pantools import logger
from pantools.send_recv import send_dict_json, recv_line, send_string

# ================================================================
#
# ================================================================
class JsonTCPClient:

    # def msg_template(self, message):
    #     return {
    #         "message": message,
    #         "hostname": socket.gethostname(),
    #     }

    # def send_get_clients(self):
    #     msg = self.msg_template("getclients")
    #     self.send_msg(msg)



    # ------------------------------------------------------------
    # Connect and start a reader loop.
    # ------------------------------------------------------------
    def connect(self, host, port):

        self.host = host
        self.port = port
        self.sock = None
        
        self.inq = queue.Queue(10000)
        self.outq = queue.Queue(10000)

        self.quit_write_thread = False
        self.quit_read_thread = False

        self.clientid = str(uuid.uuid1())

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            logger.info("Connecting to: {}:{}".format(host, port))
            self.sock.connect((host, port))
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
                    line = recv_line(self.sock)
                    msg = json.loads(line)
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
                if type(out_msg) is dict:
                    send_dict_json(self.sock, out_msg)
                else:
                    send_string(self.sock, out_msg)
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
        self.outq.put(msg_json)

    def read_msg(self):
        m = self.inq.get(block=True)
        return m
        
