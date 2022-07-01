import threading
import time
import sys
import socket
from _thread import *
from pantools.net import announce_service
from pantools.logger import logger
from pantools.send_recv import send_dict_json, send_dict_pickle
from .ClientConnection import ClientConnection
from .JsonClientConnection import JsonClientConnection

# ================================================================
#
# ================================================================
class TCPServer:

    def __init__(self) -> None:
        """TCPServer constructor. Needs no arguments since port etc is set in setup_server()"""
        self.clients = []
        self.subscribers = []  # deprecated
        self.msg_subscribers = {}
        self.ThreadCount = 0
        self.lock = threading.Lock()
        self.msg_handler = None

    def setupMessageHandler(self, message_handler):
        self.msg_handler = message_handler

    def print_clients(self, header) -> None:
        """Prints a table of active connections, followed by a table of active subscriptions"""

        logger.info(f"-- Connected Clients {header}:")
        for c in self.clients:
            logger.info(f"{c.getPeerName()} {c.get_clientid()} {c.get_clienttype()}")

        logger.info(f"-- Subscriptions:")
        for message in self.msg_subscribers:
            for c in self.msg_subscribers[message]:
                client = c
                logger.info(f" {client.getPeerName()} subscribes to message:{message}")

    def setup_server(self, host, port, adv_magic=None, adv_port=None) -> None:
        """Creates a socket and starts listening. Also optionally starts an Anouncement thread"""
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
            start_new_thread(self.advertise_service,
                             (adv_magic, adv_port, host, port))

    def advertise_service(self, adv_magic, adv_port, service_host, service_port) -> None:
        """Will continuosly send out an advertisement message using announce_service"""

        logger.info("Starting an advertising thread {} on port {}. Service on {} {}".format(
            adv_magic, adv_port, service_host, service_port))
        while True:
            announce_service(adv_magic, adv_port, service_host, service_port)
            time.sleep(5)

    def read_exception(self, client, e):
        logger.error("Error occurred, removing client")
        logger.error(e)
        self.remove_client(client)

    def add_client(self, client: ClientConnection) -> None:
        logger.info("Adding connection {}".format(client))
        self.lock.acquire()
        self.clients.append(client)
        self.lock.release()

        self.print_clients("After ADD")

    def remove_client(self, client: ClientConnection) -> None:
        logger.info("Removing connection {}".format(client))

        try:
            self.lock.acquire()
            self.clients.remove(client)
        except Exception as e:
            logger.error(f"Exception: {e}")
        finally:
            self.lock.release()

        self.remove_subscriber("*", client)

        self.print_clients("After remove_client")

        if self.msg_handler is not None:
            self.msg_handler(client, {
                "message": "lost_client",
                "hostname": "???",
                "clientid": client.get_clientid(),
                "clienttype": client.get_clienttype(),
                "client": client
            })


    def add_subscriber(self, message, client) -> None:
        logger.info("Adding subscriber to {} from {}".format(message, client))
        self.lock.acquire()
        if message not in self.msg_subscribers:
            self.msg_subscribers[message] = []
        self.msg_subscribers[message].append(client)
        self.lock.release()
        self.print_clients("After add_subscriber")

    def remove_subscriber(self, message, client) -> None:
        logger.info("Removing subscriber to {} from {}".format(message, client))
        self.lock.acquire()
        if message != "*" and message not in self.msg_subscribers:
            self.lock.release()
            return
        try:
            if message == "*":
                logger.info(f"Removing all subscriptions for {client}")
                for m in self.msg_subscribers:
                    logger.info(f"Removing {m}")
                    self.msg_subscribers[m].remove(client)
            else:
                self.msg_subscribers[message].remove(client)
        except Exception as e:
            logger.error(f"Exception : {e}")
        finally:
            self.lock.release()
        self.print_clients("After remove_subscriber")

    def broadcast_json_message(self, msg) -> None:
        self.lock.acquire()
        for client in self.clients:
            logger.info(f"Sending message {msg} to {client}")
            try:
                send_dict_json(client.getSocket(), msg)
            except Exception as e:
                logger.error(f"Exception: {e} when broadcasting message")

        self.lock.release()

    def send_message_reply(self, client, msg):
        try:
            send_dict_json(client.getSocket(), msg)
        except Exception as e:
            logger.error(f"Exception: {e} when sending message to client {client}")

    def send_message_to_all_subscribers(self, msg) -> None:
        self.lock.acquire()
        if msg["message"] in self.msg_subscribers:
            for c in self.msg_subscribers[msg["message"]]:
                client = c
                # filter the actual image from output on screen
                output_msg = [value for key, value in msg.items() if key not in ["image"]]
                logger.info(f"Sending message {output_msg} to {c}")
                try:
                    send_dict_pickle(client.getSocket(), msg)
                except Exception as e:
                    logger.error(f"Exception: {e} when sending message to all clients")

        self.lock.release()

    def accept_clients(self, use_json=True):
        while True:
            logger.debug("accept_clients() thread waiting for JSON clients...")
            client_socket, address = self.ServerSocket.accept()
            logger.info("Client connected: " + address[0] + ":" + str(address[1]))

            # We *could* pass the connection class as a parameter
            if use_json:
                client = JsonClientConnection(client_socket, self)
            else:
                client = ClientConnection(client_socket, self)

            self.add_client(client)
            client.start_reader()

    def stop_server(self):
        self.ServerSocket.close()

    def handle_message(self, client, obj) -> None:

        if self.msg_handler is not None:
            self.msg_handler(client, obj)



