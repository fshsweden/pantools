import cv2

class Motion:
    def __init__(self, ceil) -> None:
        self.ceil = ceil

    def processImage(self, frame):

        if self.frame1gray == None:
            self.frame1gray = frame.copy()
            self.frame1gray = cv2.cvtColor(self.frame1gray, cv2.COLOR_RGB2GRAY)

        self.frame2gray = frame.copy()
        self.frame2gray = cv2.cvtColor(self.frame2gray, cv2.COLOR_RGB2GRAY)

        self.height, self.width, channels = frame.shape
        self.nb_pixels = self.width * self.height

        self.trigger_time = 0 #Hold timestamp of the last detection

        self.frame2gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        # Absdiff to get the difference between to the frames
        self.res = cv2.absdiff(self.frame1gray, self.frame2gray)
        # Remove the noise and do the threshold
        self.res = cv2.blur(self.res, (5, 5))
        # ## element = cv2.createStructuringElementEx(5*2+1, 5*2+1, 5, 5,  cv2.CV_SHAPE_RECT)
        # ## cv2.MorphologyEx(self.res, self.res, None, None, cv2.CV_MOP_OPEN)
        # ## cv2.MorphologyEx(self.res, self.res, None, None, cv2.CV_MOP_CLOSE)
        # ## cv2.Threshold(self.res, self.res, 10, 255, cv2.CV_THRESH_BINARY_INV)

    def somethingHasMoved(self):
        nb = 0 # Will hold the number of black pixels
        for y in range(self.height-1):  # Iterate the hole image
            for x in range(self.width-1):
                if self.res[y, x] == 0.0:  # If the pixel is black keep it
                    nb += 1
        avg = (nb*100.0)/self.nb_pixels  # Calculate the average of black pixel in the image
        # print "Average: ",avg, "%\r",
        if avg > self.ceil:  # If over the ceil trigger the alarm
            return True
        else:
            return False
