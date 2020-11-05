import cv2
from datetime import datetime
import time

# codec = cv2.CV_FOURCC('D', 'I', 'V', 'X')
# filename = datetime.now().strftime("%b-%d_%H:%M:%S")+".avi"

class VideoRecorder:
    #height, width, channels = frame.shape

    def __init__(self, filename, codec, fps=15, size_tuple=(640, 480) ) -> None:
        self.writer=cv2.CreateVideoWriter(filename, codec, fps, size_tuple, 1)

    def addframe(self, frame):
        self.writer.write(frame)

    def close(self):
        self.writer.release()
