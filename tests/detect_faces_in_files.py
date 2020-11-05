import cv2
import os
from imutils import paths
import face

files = list(paths.list_images("."))

for p in files:
    p = os.path.abspath(p)
    # load the image from disk
    image = cv2.imread(p)
    if (image is not None):
        rects = face.get_face_rect(image)
        if len(rects) > 0:
            print(f"{p} has {len(rects)} faces")
