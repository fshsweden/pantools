import struct
import socket
import pickle

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
