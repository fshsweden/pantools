from time import sleep
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST, SO_REUSEADDR, gethostbyname, gethostbyname_ex, gethostname
from .logger import logger
import numpy as np

def get_local_ip():
    addr = [l for l in ([ip for ip in gethostbyname_ex(gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket(AF_INET, SOCK_DGRAM)]][0][1]]) if l][0][0]
    return addr

def announce_service(adv_magic, adv_port, service_host, service_port):

    s = socket(AF_INET, SOCK_DGRAM)  # create UDP socket
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)  # this is a broadcast socket
    s.bind(('', 0))
    # format id <magicstring>#<ip>#<port> !
    data = adv_magic+'#' + service_host + '#'+str(service_port)
    data = data.encode('utf-8')
    s.sendto(data, ('<broadcast>', adv_port))
    s.close()


def wait_for_announcement(port, magic):
    s = socket(AF_INET, SOCK_DGRAM)  # create UDP socket
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(('', port))

    found = False
    str = ""
    ip = ""
    port = 0

    while not found:
        data, addr = s.recvfrom(1024)  # wait for a packet
        str = data.decode('utf-8')
        if str.startswith(magic):
            found = True
            (m, ip, port) = str.split('#')
            logger.debug("got service announcement from {}, with ip {} and port {}".format(str[len(magic):], ip, port))

    s.close()
    return (ip, int(port))


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great circle distance between two points on the 
    earth (specified in decimal degrees), returns the distance in
    meters.
    All arguments must be of equal length.
    :param lon1: longitude of first place
    :param lat1: latitude of first place
    :param lon2: longitude of second place
    :param lat2: latitude of second place
    :return: distance in meters between the two sets of coordinates
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km * 1000
