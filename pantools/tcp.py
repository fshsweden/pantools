import struct
import socket
import pickle
import threading
import sys
import time
import struct
import imutils
from imutils.video import VideoStream

from _thread import *
from sys import int_info
from threading import main_thread
from pantools.net import announce_service, wait_for_announcement

import logging, sys, os
logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d in function %(funcName)s] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ================================================================
#
# ================================================================
class TCPServer:

    def __init__(self) -> None:
        self.connections = []
        self.subscribers = [] # deprecated
        self.msg_subscribers = {}
        self.ThreadCount = 0
        self.lock = threading.Lock()

    def print_connections(self, header):
        logger.info("--- connection list {} ---".format(header))
        for c in self.connections:
            logger.info(c.getpeername())
        logger.info("--- end         ---")
        logger.info("--- subscriber list ---")
        for msgtype in self.msg_subscribers:
            logger.info("msgtype:{}".format(msgtype))
            for c in self.msg_subscribers[msgtype]:
                logger.info(c.getpeername())
        logger.info("--- end         ---")

    def setup_server(self, host, port, adv_magic=None, adv_port=None):
        self.ServerSocket = socket.socket()
        self.ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ThreadCount = 0
        try:
            logger.info("Binding to {}:{}".format(host, port))
            self.ServerSocket.bind((host, port))
        except socket.error as e:
            logger.info(str(e))
            sys.exit(1)

        logger.info("Listening for a Connection..")
        self.ServerSocket.listen(5)

        if adv_magic is not None and adv_port is not None:
            start_new_thread(self.advertise_service,(adv_magic, adv_port, host, port))

    def advertise_service(self, adv_magic, adv_port, service_host, service_port):
        logger.info("Starting an advertising thread {} on port {}. Service on {} {}".format(adv_magic, adv_port, service_host, service_port))
        while True:
            announce_service(adv_magic, adv_port, service_host, service_port)
            time.sleep(5)

    def add_connection(self, connection):
        logger.info("Adding connection {}".format(connection))
        self.lock.acquire()
        self.connections.append(connection)
        self.lock.release()

        self.print_connections("After ADD")

    def remove_connection(self, connection):
        logger.info("Removing connection {}".format(connection))

        self.lock.acquire()
        self.connections.remove(connection)
        for msgtype in self.msg_subscribers:
            if connection in self.msg_subscribers[msgtype]:
                print("Removing connection {}".format(connection))
                self.msg_subscribers[msgtype].remove(connection)
        self.lock.release()

        self.print_connections("After REMOVE")


    def add_subscriber(self, msgtype, connection):
        logger.info("Adding subscriber {} {}".format(msgtype, connection))
        self.lock.acquire()
        if msgtype not in self.msg_subscribers:
            self.msg_subscribers[msgtype] = []
        self.msg_subscribers[msgtype].append(connection)
        self.lock.release()
        self.print_connections("After ADD SUB")

    def remove_subscriber(self, msgtype, connection):
        logger.info("Removing subscriber {} {}".format(msgtype, connection))
        self.lock.acquire()
        if msgtype not in self.msg_subscribers:
            self.lock.release()
            return
        self.msg_subscribers[msgtype].remove(connection)
        self.lock.release()
        self.print_connections("After REMOVE SUB")

    #
    # Thread started for each connection!
    #
    def read_thread(self, connection):

        # print("Starting thread for socket {}".format(connection))
        srcaddr, srcport = connection.getpeername()

        # print("Startar recv_size() loop")
        while True:
            try:
                data = recv_size(connection)
                obj = pickle.loads(data)

                message = obj["message"]
                msgtype = obj["msgtype"]

                if message == "subscribe":
                    logger.info("Received SUBSCRIBE...")
                    self.add_subscriber(msgtype, connection)
                    self.print_connections("After SUBSCRIBE")

                if message == "unsubscribe":
                    logger.info("Received UNSUBSCRIBE...")
                    self.remove_subscriber(msgtype, connection)
                    self.print_connections("After UNSUBSCRIBE")

                if message == "image":
                    logger.debug("Received image {}".format(obj["frameno"]))
                    self.lock.acquire()
                    logger.debug("finding subscribers of msgtype {}".format(msgtype))

                    if msgtype in self.msg_subscribers:
                        for c in self.msg_subscribers[msgtype]:
                            # Avoid sending message to ourselves
                            # if c is not connection:
                            logger.debug("Sending message to {}".format(c))
                            send_json(c, obj)
                            # else:
                            #     logger.info("Skipping sending image to camera client!")

                    self.lock.release()

            except Exception as e:
                logger.error(str(e))
                logger.info("Apparently the client hung up! Closing connection!")
                self.remove_connection(connection)
                connection.close()
                return # close thread!


    def accept_clients(self):
        while True:
            logger.debug("accept_clients() thread waiting...")
            client_socket, address = self.ServerSocket.accept()
            logger.info("Client connected: " + address[0] + ":" + str(address[1]))
            self.add_connection(client_socket)
            self.print_connections("After CLIENT ACCEPTED")
            start_new_thread(self.read_thread, (client_socket,))
            self.ThreadCount += 1
            logger.info("Started thread Number: " + str(self.ThreadCount))

    def stop_server(self):
        self.ServerSocket.close()

# ****************************************************************
# Generic socket utilities
# ****************************************************************
def send_size(sock, data):
    # data is bytes()
    sock.sendall(struct.pack(">i", len(data)) + data)


def send_json(connection, json):
    message = pickle.dumps(json)
    send_size(connection, message)


def recv_size(sock):
    # data length is packed into 4 bytes
    total_bytes_read = 0
    size_of_message = 300000
    chunk = bytes("", "utf-8")

    length_field = bytes("", "utf-8")
    buffer = bytes("", "utf-8")

    #
    # Read Message Length Field (size 4)
    #
    while total_bytes_read < 4:
        sz_to_recv = 4 - len(length_field)
        chunk = sock.recv(sz_to_recv)
        if (len(chunk) < sz_to_recv):
            raise Exception("Was reading {} bytes but got only {}".format(sz_to_recv, len(chunk)))
        else:
            total_bytes_read += len(chunk)
            length_field += chunk

    size_of_message = struct.unpack(">i", length_field)[0]
    # print("size of message is: {}".format(size_of_message))

    total_bytes_read = 0
    while total_bytes_read < size_of_message:
        # receives bytes!
        chunk = sock.recv(size_of_message - len(buffer))
        # print("read chunk: {}".format(len(chunk)))
        total_bytes_read += len(chunk)
        buffer += chunk

    return buffer


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
            logger.info("Connected!")
            self.handle_connection_status("connected")
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
    def handle_message(self, msg):
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

    #
    #
    #
    def send_msg(self, msg_json):
        msg_encoded = pickle.dumps(msg_json)
        send_size(self.sock, msg_encoded)


# ================================================================
#
# ================================================================
class CameraClient(TCPClient):

    def __init__(self, magic, port, picam=False) -> None:
        super().__init__(magic, port)
        self.frame_number = 1
        self.picam = picam
        self.magic = magic
        self.port = port
        if self.picam == True:
            logger.debug("Using PI Camera!")
            self.vs = VideoStream(usePiCamera=True).start()
        else:
            logger.debug("Using USB Camera!")
            self.vs = VideoStream(usePiCamera=False).start()
        time.sleep(2)
        logger.debug("Camera varmed up!")

    def start_client(self):
        logger.debug("Camera Client start_client...")
        super().start_client()
        start_new_thread(self.write_thread, ())

    def handle_message(self, msg):
        super().handle_message(msg)
        logger.debug("CameraClient handle_message")

    def write_thread(self):
        logger.debug("write thread...")
        try:
            while True:
                self.frame_number = self.frame_number + 1
                self.currentFrame = self.vs.read()

                if self.currentFrame is None:
                    logger.debug("No current frame!")
                else:
                    self.currentFrame = imutils.resize(
                        self.currentFrame, width=512)
                    # currentFrame = cv2.cvtColor(currentFrame, cv2.COLOR_BGR2GRAY)

                    if self.frame_number % 100 == 0:
                        logger.debug("{} frames sent to server!".format(
                            self.frame_number))

                    m = pickle.dumps(
                        {
                            "message": "image",
                            "msgtype": "image",
                            "type": "json-object",
                            "threadname": "none",
                            "hostname": socket.gethostname(),
                            "frameno": self.frame_number,
                            "image": self.currentFrame,
                        }
                    )

                    # print("Client Sends: {} {}".format(m, type(m)))
                    send_size(self.sock, m)

                    time.sleep(0.01)
        except Exception as e:
            logger.error("Exception in write thread")
            logger.error(str(e))
        finally:
            logger.info("Closing socket from write_thread...")
            self.sock.close()
