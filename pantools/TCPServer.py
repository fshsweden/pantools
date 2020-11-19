import threading
import time
import logging
import sys
import os
import socket
import pickle
from _thread import *
from pantools.net import announce_service, wait_for_announcement

from .logger import logger
from .send_recv import send_json, send_size, recv_size
from .ClientConnection import ClientConnection

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
        self.msg_counter = 0
        self.lock = threading.Lock()

    def print_clients(self, header) -> None:
        """Prints a table of active connections, followed by a table of active subscriptions"""

        print(f"-- Clients (header):")
        for c in self.clients:
            logger.info(f"Connected client:{c.getPeerName()}")
        for msgtype in self.msg_subscribers:
            for c in self.msg_subscribers[msgtype]:
                logger.info(f"Subscriber of msgtype:{msgtype} is {c.getPeerName()}")

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
        self.remove_client(client)

    def add_client(self, client: ClientConnection) -> None:
        logger.info("Adding connection {}".format(client))
        self.lock.acquire()
        self.clients.append(client)
        self.lock.release()

        self.print_clients("After ADD")

    def remove_client(self, client: ClientConnection) -> None:
        logger.info("Removing connection {}".format(client))

        self.lock.acquire()
        try:
            self.clients.remove(client)
            for msgtype in self.msg_subscribers:
                if client in self.msg_subscribers[msgtype]:
                    print("Removing subscriber {}".format(client))
                    self.msg_subscribers[msgtype].remove(client)
        except Exception as e:
            logger.error(f"Exception: {e}")
        finally:
            self.lock.release()

        self.print_clients("After REMOVE")


    def add_subscriber(self, msgtype, client) -> None:
        logger.info("Adding subscriber {} {}".format(msgtype, client))
        self.lock.acquire()
        if msgtype not in self.msg_subscribers:
            self.msg_subscribers[msgtype] = []
        self.msg_subscribers[msgtype].append(client)
        self.lock.release()
        self.print_clients("After ADD SUB")

    def remove_subscriber(self, msgtype, client) -> None:
        logger.info("Removing subscriber {} {}".format(msgtype, client))
        self.lock.acquire()
        if msgtype not in self.msg_subscribers:
            self.lock.release()
            return
        try:
            self.msg_subscribers[msgtype].remove(client)
        except Exception as e:
            logger.error(f"Exception : {e}")
        finally:
            self.lock.release()
        self.print_clients("After REMOVE SUB")

    def send_message_to_all_clients(self, msg) -> None:
        pass

    def send_message_to_all_subscribers(self, msg) -> None:
        self.lock.acquire()
        if msg["msgtype"] in self.msg_subscribers:
            for c in self.msg_subscribers[msg["msgtype"]]:
                logger.debug("Sending message to {}".format(c))
                try:
                    send_json(c.getSocket(), msg)
                except Exception as e:
                    logger.error(f"Exception: {e} when sending message to all clients")

        self.lock.release()

    def accept_clients(self):
        while True:
            logger.debug("accept_clients() thread waiting...")
            client_socket, address = self.ServerSocket.accept()
            logger.info("Client connected: " + address[0] + ":" + str(address[1]))

            client = ClientConnection(client_socket, self)
            self.add_client(client)
            client.start_reader()

    def stop_server(self):
        self.ServerSocket.close()

    def handle_message(self, client, obj) -> None:
        """Handles incoming messages to the server. Most important are announce and subscribe"""
        message = obj["message"]
        msgtype = obj["msgtype"]

        self.msg_counter = self.msg_counter + 1
        if self.msg_counter % 100 == 0:
            logger.debug(f"{self.msg_counter} messages received!")

        # filter out the ones we dont want printed out
        if message not in ["image"]:
            logger.debug(f"Received message {message}")

        if message == "subscribe":
            # self.lookup_client(connection)
            self.add_subscriber(msgtype, client)
            self.print_clients("After SUBSCRIBE")

        if message == "unsubscribe":
            self.remove_subscriber(msgtype, client)
            self.print_clients("After UNSUBSCRIBE")

        if message == "image":
            self.send_message_to_all_subscribers(obj)

        if message == "announce":
            logger.debug("Received announce {}".format(obj["hostname"]))
            client.set_hostname(obj["hostname"])

        # Query Reply!
        if message == "gethosts":
            logger.debug("Received gethosts")
            


