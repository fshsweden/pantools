import socket
import struct
import pickle

def send_size(sock: socket, data: bytes):
    # data is bytes()
    print(f"send_size sends {len(data)} followed by the data")
    sock.sendall(struct.pack(">i", len(data)) + data)

# an alias since json was really a dict!
def send_json(connection: socket, json: dict):
    send_dict(dict)

def send_dict(connection: socket, d: dict):
    #convert dictionary to bytes
    message = pickle.dumps(d)
    # print(f"sending: {message}")
    send_size(connection, message)

def recv_dict(sock: socket) -> dict:
    b = recv_size(sock)
    return pickle.loads(b)

def recv_size(sock: socket) -> str:
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
    
    #print("size of message is: {}".format(size_of_message))

    total_bytes_read = 0
    while total_bytes_read < size_of_message:
        # receives bytes!
        chunk = sock.recv(size_of_message - len(buffer))
        # print("read chunk: {}".format(len(chunk)))
        total_bytes_read += len(chunk)
        buffer += chunk

    return buffer
    
