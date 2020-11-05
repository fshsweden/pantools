import cv2
from datetime import datetime
import time


class MotionDetector():

    def onChange(self, val): # callback when the user change the ceil
        self.ceil = val

    def __init__(self, ceil=8, doRecord=True, showWindows=True):
        self.writer = None
        self.font = None
        self.doRecord = doRecord # Either or not record the moving object
        self.show = showWindows # Either or not show the 2 windows
        self.frame = None

        ###self.capture=cv2.CaptureFromCAM(0)
        self.capture = cv2.VideoCapture(0)
        ###self.frame = cv2.QueryFrame(self.capture) #Take a frame to init recorder
        _, self.frame = self.capture.read()
        if doRecord:
            self.initRecorder()

        ####self.frame1gray = cv2.CreateMat(self.frame.height, self.frame.width, cv2.CV_8U) #Gray frame at t-1
        ######cv2.CvtColor(self.frame, self.frame1gray, cv2.CV_RGB2GRAY)
        #self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        self.frame1gray = self.frame.copy()
        self.frame1gray = cv2.cvtColor(self.frame1gray, cv2.COLOR_RGB2GRAY)

        #Will hold the thresholded result
        ####self.res = cv2.CreateMat(self.frame.height, self.frame.width, cv2.CV_8U)
        ####self.frame2gray = cv2.CreateMat(self.frame.height, self.frame.width, cv2.CV_8U) #Gray frame at t
        self.frame2gray = self.frame.copy()
        self.frame2gray = cv2.cvtColor(self.frame2gray, cv2.COLOR_RGB2GRAY)

        (self.height, self.width, chan) = self.frame.shape
        #self.height = self.frame.height
        self.nb_pixels = self.width * self.height
        self.ceil = ceil
        self.isRecording = False
        self.trigger_time = 0 #Hold timestamp of the last detection

        if showWindows:
            cv2.namedWindow("Image")
            cv2.createTrackbar("Mytrack", "Image", self.ceil, 100, self.onChange)

    def initRecorder(self): #Create the recorder
        codec = cv2.CV_FOURCC('D', 'I', 'V', 'X')
        #codec = cv2.CV_FOURCC("D", "I", "B", " ")
        self.writer=cv2.CreateVideoWriter(datetime.now().strftime("%b-%d_%H:%M:%S")+".avi", codec, 15, cv2.GetSize(self.frame), 1)
        #FPS set at 15 because it seems to be the fps of my cam but should be ajusted to your needs
        self.font = cv2.InitFont(cv2.CV_FONT_HERSHEY_SIMPLEX, 1, 1, 0, 2, 8) #Creates a font

    def run(self):
        started = time.time()
        while True:

            ### curframe = cv2.QueryFrame(self.capture)
            _, curframe=self.capture.read()
            #curframe = cv2.cvtColor(curframe, cv2.COLOR_BGR2RGB)
            instant = time.time() #Get timestamp o the frame

            self.processImage(curframe) #Process the image

            if not self.isRecording:
                if self.somethingHasMoved():
                    self.trigger_time = instant #Update the trigger_time
                    if instant > started +5:#Wait 5 second after the webcam start for luminosity adjusting etc..
                        print("Something is moving !")
                        if self.doRecord: #set isRecording=True only if we record a video
                            self.isRecording = True
            else:
                if instant >= self.trigger_time +10: #Record during 10 seconds
                    print("Stop recording")
                    self.isRecording = False
                else:
                    cv2.PutText(curframe,datetime.now().strftime("%b %d, %H:%M:%S"), (25,30),self.font, 0) #Put date on the frame
                    cv2.WriteFrame(self.writer, curframe) #Write the frame

            if self.show:
                cv2.imshow("Image", curframe)
                cv2.imshow("Res", self.res)

            self.frame1gray = self.frame2gray.copy()
            c = cv2.waitKey(1)

            if c == 27 or c == 1048603:  # Break if user enters 'Esc'.
                break

    def processImage(self, frame):
        # cv2.cvtColor(frame, self.frame2gray, cv2.CV_RGB2GRAY)
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

if __name__=="__main__":
    detect = MotionDetector(doRecord=False)
    detect.run()

