import numpy as np
from time import sleep
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST, gethostbyname, gethostbyname_ex, gethostname
#import socket


def get_local_ip():
    addr = [l for l in ([ip for ip in gethostbyname_ex(gethostname())[2] if not ip.startswith("127.")][:1], [
                        [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket(AF_INET, SOCK_DGRAM)]][0][1]]) if l][0][0]
    return addr


def announce_service(port, magic):

    s = socket(AF_INET, SOCK_DGRAM)  # create UDP socket
    s.bind(('', 0))
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)  # this is a broadcast socket

    # print("hostname=", gethostname())
    # print("gethostname=", gethostbyname_ex(gethostname()))
    # my_ip=gethostbyname(gethostname()) #get our IP. Be careful if you have multiple network interfaces or IPs
    my_ip = get_local_ip()

    data = MAGIC+my_ip
    data = data.encode('utf-8')
    # print("data:[", data, "]")
    s.sendto(data, ('<broadcast>', PORT))
    print("sent service announcement:", data)

    s.close()


def wait_for_announcement(port, magic):
    s = socket(AF_INET, SOCK_DGRAM)  # create UDP socket
    s.bind(('', port))

    found = False
    str = ""

    while not found:
        data, addr = s.recvfrom(1024)  # wait for a packet
        str = data.decode('utf-8')
        if str.startswith(magic):
            found = True
            print("got service announcement from", str[len(magic):])

    s.close()
    return str


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


if __name__ == "__main__":
    PORT = 50000
    MAGIC = "0xBOOBBOOB"  # to make sure we don't confuse or get confused by other programs
    while 1:
        announce_service(PORT, MAGIC)
        sleep(5)
