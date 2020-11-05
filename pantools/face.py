import cv2

SCALEFACTOR=1.1
MINNEIGHBOURS=5
MINSIZEX=40
MINSIZEY=40

def get_face_rect(image, _scale=SCALEFACTOR, _minNeighbours=MINNEIGHBOURS, _minsizex=MINSIZEX, _minsizey=MINSIZEY):
    cascadepath = "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascadepath)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=_scale,
        minNeighbors=_minNeighbours,
        minSize=(_minsizex, _minsizey)
    )

    return faces
