#!/usr/bin/env python
# Inspired by from https://github.com/mattwilliamson/Motion-Tracker/blob/master/track.py
from imutils.video import VideoStream
import numpy as np
import cv2

class MotionDetectorContour:
    def __init__(self,ceil=15):
        self.ceil = ceil
        cv2.namedWindow("Target", 1)
        self.vs = VideoStream(usePiCamera=False)
        self.backSub = cv2.createBackgroundSubtractorMOG2()
        if not self.vs.stream.stream.isOpened():
            print("Can't open USB camera 0!")
            exit()
        self.vs.start()

    def run(self):
        # Capture first frame to get size
        image = self.vs.read()
        # frame_size = np.shape(frame)
        width = image.width
        height = image.height
        surface = width * height #Surface area of the image
        cursurface = 0 #Hold the current surface that have changed

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        #grey_image = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U, 1)
        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        #moving_average = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_32F, 3)
        moving_average = np.zeros((height,width,3), np.uint8)
        difference = None

        while True:
            color_image = self.vs.read()
            
            color_image = cv2.GaussianBlur(color_image,(5,5),0)

            mask = self.backSub.apply(color_image)

            #Convert the image so that it can be thresholded
            grey_image = cv2.cvtColor(difference, cv2.CV_RGB2GRAY)
            grey_image = cv2.threshold(grey_image, 70, 255, cv2.CV_THRESH_BINARY)

            grey_image = cv2.dilate(grey_image, None, 18) #to get object blobs
            grey_image = cv2.erode(grey_image, None, 10)

            # Find contours
            storage = cv2.CreateMemStorage(0)
            contours = cv2.findContours(grey_image, cv2.CV_RETR_EXTERNAL, cv2.CV_CHAIN_APPROX_SIMPLE)

            backcontours = contours #Save contours

            while contours: #For all contours compute the area
                cursurface += cv2.contourArea(contours)
                contours = contours.h_next()

            avg = (cursurface*100)/surface #Calculate the average of contour area on the total size
            if avg > self.ceil:
                print("Something is moving !")
            #print avg,"%"
            cursurface = 0 #Put back the current surface to 0

            #Draw the contours on the image
            _red =  (0, 0, 255); #Red for external contours
            _green =  (0, 255, 0);# Gren internal contours
            levels=1 #1 contours drawn, 2 internal contours as well, 3 ...
            
            color_image = cv2.drawContours (backcontours,  _red, _green, levels, 2, cv2.CV_FILLED)

            cv2.ShowImage("Target", color_image)

            # Listen for ESC or ENTER key
            c = cv2.WaitKey(7) % 0x100
            if c == 27 or c == 10:
                break

if __name__=="__main__":
    t = MotionDetectorContour()
    t.run()

