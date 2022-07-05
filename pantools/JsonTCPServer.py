import threading
import time
import sys
import socket
from _thread import *
from pantools.net import announce_service
from pantools.logger import logger
from pantools.send_recv import send_dict_json, send_dict_pickle
from .JsonTCPClientConnection import JsonTCPClientConnection

# ================================================================
#
# ================================================================
class JsonTCPServer:

    def __init__(self, host, port) -> None:
        """JsonTCPServer constructor. Needs no arguments since port etc is set in setup_server()"""
        self.clients = []
        self.lock = threading.Lock()
        self.conn_handler = None
        self.msg_handler = None
        self.err_handler = None

        """Creates a socket and starts listening. Also optionally starts an Anouncement thread"""
        self.ServerSocket = socket.socket()
        self.ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            # logger.info("Binding to {}:{}".format(host, port))
            self.ServerSocket.bind((host, port))
        except socket.error as e:
            logger.info(str(e))
            sys.exit(1)

        # logger.info("Listening for a Connection..")
        self.ServerSocket.listen(5)


    def setupMessageHandler(self, conn_handler, message_handler, error_handler):
        self.conn_handler = conn_handler
        self.msg_handler = message_handler
        self.err_handler = error_handler

    def get_clients(self):
        return self.clients


    def accept_clients(self):
        while True:
            # logger.debug("accept_clients() thread waiting for JSON clients...")
            client_socket, address = self.ServerSocket.accept()
            # logger.info("Client connected: " + address[0] + ":" + str(address[1]))
            client = JsonTCPClientConnection(client_socket, self)
            self.add_client(client)
            if self.conn_handler != None:
                self.conn_handler(client, True)
            client.start_reader()


    # Relay these two from JsonTCPClientConnection
    def read_exception(self, client, e):
        if self.err_handler != None:
            self.err_handler(client, e)
        self.remove_client(client)

    def handle_message(self, client, obj) -> None:
        if self.msg_handler is not None:
            self.msg_handler(client, obj)


    def add_client(self, client: JsonTCPClientConnection) -> None:
        # logger.info("Adding connection {}".format(client))
        self.lock.acquire()
        self.clients.append(client)
        self.lock.release()
        if self.conn_handler != None:
            self.conn_handler(client, True)

    def remove_client(self, client: JsonTCPClientConnection) -> None:
        # logger.info("Removing connection {}".format(client))

        try:
            self.lock.acquire()
            self.clients.remove(client)
        except Exception as e:
            logger.error(f"Internal exception: {e} removing client")
        finally:
            self.lock.release()

        # if self.msg_handler is not None:
        #     self.msg_handler(client, {
        #         "message": "lost_client",
        #         "hostname": "???",
        #         "client": client
        #     })

        if self.conn_handler != None:
            self.conn_handler(client, False)


    def broadcast_dict(self, msg) -> None:
        self.lock.acquire()
        for client in self.clients:
            # logger.info(f"Sending message {msg} to {client}")
            try:
                send_dict_json(client.getSocket(), msg)
            except Exception as e:
                # logger.error(f"Exception: {e} when broadcasting message")
                self.remove_client(client)

        self.lock.release()

    def stop_server(self):
        self.ServerSocket.close()

