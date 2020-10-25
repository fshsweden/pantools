import struct
import imutils
from imutils.video import VideoStream
import time
from _thread import *
import pickle 
import socket
import sys
import struct

from .TCPClient import TCPClient
from .logger import logger
from .send_recv import send_size, recv_size

# ================================================================
#
# ================================================================
class CameraClient():

    def __init__(self, magic, port, picam=False) -> None:

        self.frame_number = 1
        self.picam = picam
        self.magic = magic
        self.port = port
        self.tcp_client = TCPClient(magic, port)

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
        self.tcp_client.start_client()
        self.tcp_client.send_msg({
            "message": "announce",
            "msgtype": "admin",
            "hostname": socket.gethostname()
        })
        start_new_thread(self.camera_thread, ())

    def send_image(self, frame_number, frame) -> None:
        msg = {
            "message": "image",
            "msgtype": "image",
            "type": "json-object",
            "threadname": "none",
            "hostname": socket.gethostname(),
            "frameno": frame_number,
            "image": frame,
        }
        print(f"Sending message size: {get_size(msg)} where image {frame_number} of type {type(frame)} takes up {frame.size} bytes")
        self.tcp_client.send_msg(msg)

    def camera_thread(self):
        logger.info("************ camera thread started **************")
        try:
            while True:
                logger.info("Reading video frame")
                fr = self.vs.read()

                if fr is None:
                    logger.error("No current frame!")
                else:
                    fr = fr.copy()
                    fr = imutils.resize(fr, width=512)
                    self.frame_number = self.frame_number + 1
                    frnum = self.frame_number

                    msg = {
                        "message": "image",
                        "msgtype": "image",
                        "type": "json-object",
                        "threadname": "none",
                        "hostname": socket.gethostname(),
                        "frameno": frnum,
                        "image": fr
                    }
                    
                    self.tcp_client.send_msg(msg)

                    time.sleep(0.01)

        except Exception as e:
            logger.error("Exception in camera thread")
            logger.error(str(e))
        finally:
            logger.info("Exiting camera_thread...")

    def send_msg(self, msg):
        self.tcp_client.send_msg(msg)

    # blocking read!
    def read_msg(self):
        msg = self.tcp_client.read_msg()
        return msg
            

def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size
