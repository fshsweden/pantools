import imutils
from imutils.video import VideoStream
import time
from _thread import *
import pickle 
import socket
import sys

from .TCPClient import TCPClient
from .logger import logger
from .send_recv import send_size, recv_size

# ================================================================
#
# ================================================================
class CameraClient(TCPClient):

    def __init__(self, magic, port, picam=False) -> None:
        """Constructor 
        
        magic is the keystring that we look for when receiving advertisements on port "port"

        Normally I use 6868. You Choose a unique keyword to listen for.

        Syntax of advertisement is assumed to be KEYWORD#SERVICE-IP#SERVICE-PORT
        """

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
        self.send_message({
            "message": "announce",
            "msgtype": "admin",
            "hostname": socket.gethostname()
        })
        start_new_thread(self.write_thread, ())

    def handle_message(self, msg):
        super().handle_message(msg)
        logger.debug("CameraClient handle_message")

    def send_message(self, msg) -> None:
        m = pickle.dumps(msg)
        send_size(self.sock, m)

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
        self.send_message(msg)

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

                    logger.debug(f"Sending frame {self.frame_number}")
                    self.send_image(
                        self.frame_number,
                        self.currentFrame,
                    )

                    time.sleep(0.01)
        except Exception as e:
            logger.error("Exception in write thread")
            logger.error(str(e))
        finally:
            logger.info("Closing socket from write_thread...")
            self.sock.close()

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
