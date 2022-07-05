import json
import socket
import struct
import pickle
from .logger import logger
import json

#
# String data without length (possibly terminated by \r\n?)
# JSON data is sent as strings
#
def send_string(sock: socket, data: str):
    # data is bytes()
    sock.sendall(data.encode("utf-8"))

#
# Receive string data, as byte by byte...
#
def recv_line(sock: socket) -> str:
    buffer = bytearray()
    chunk = sock.recv(1)
    # read chars until we hit a NL
    while chunk != b'\n':
        buffer += chunk
        chunk = sock.recv(1)
    s = buffer.decode('utf-8')
    return s

# an alias since json was really a dict!
def send_json(sock: socket, d: dict):
    send_dict_json(sock, d)

def send_dict_json(sock: socket, d: dict):
    #convert dictionary to bytes
    message = json.dumps(d) + "\r\n"
    send_string(sock, message)



#
# Pickle-serialized data with length byte!
#
def send_size(sock: socket, data: bytes):
    # data is bytes()
    b = bytearray()
    b += struct.pack(">i", len(data))
    logger.debug(f"send_size sends {len(b)} {len(data)} followed by the data")
    sock.sendall(b)
    sock.sendall(data)

def send_dict_pickle(sock: socket, d: dict):
    #convert dictionary to bytes
    message = pickle.dumps(d)
    send_size(sock, message)

def recv_dict(sock: socket) -> dict:
    b = recv_size(sock)
    return pickle.loads(b)

def recv_size(sock: socket) -> str:
    # data length is packed into 4 bytes
    total_bytes_read = 0
    size_of_message = 0
    length_field = bytearray()
    buffer = bytearray()

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
    
    logger.debug("size of message is: {}".format(size_of_message))

    total_bytes_read = 0
    while total_bytes_read < size_of_message:
        # receives bytes!
        want = size_of_message - len(buffer)
        chunk = sock.recv(want)
        logger.debug("wanted to read {} and read chunk: {}".format(want, len(chunk)))
        total_bytes_read += len(chunk)
        buffer += chunk

    logger.debug(f"  done reading chunks: total size is {len(buffer)}")
    if (total_bytes_read != len(buffer)):
        logger.error("XXXXXXXXXXX SERIOUS ERROR! XXXXXXXXXXXX")
    return buffer
    
