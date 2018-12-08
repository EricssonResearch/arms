
from time import sleep
import math
import numpy as np
import cv2
from collections import Counter
import datetime
import arms.utils.log as log
import RPi.GPIO as GPIO

class Camera:
    """
    Initializes the Camera object with a specified resolution,
    rotation and zoom. Also creates a raw variable that is used to
    handle the captured picture (so you don't need to save a file and
    open it). Then a short sleep to make sure everything is initialized.
    """
    def __init__(self, noCam = False):
        self.width = 2000
        self.height = 1700
        self.edgeX = (3280 - self.width)/2
        self.edgeY = (2464 - self.width)/2
        self.threshold = 15
        self.correct_pos = False
        if not noCam:
            from picamera import PiCamera
            from picamera.array import PiRGBArray
            self.camera = PiCamera()
            self.camera.resolution = (3280, 2464)
            #self.camera.rotation = 90
            self.camera.zoom = (0.4, 0.4, 0.2, 0.2)
            self.raw = PiRGBArray(self.camera)
            log.camera.info("Camera initialized!")

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(17, GPIO.OUT)
        sleep(1)

    def __del__(self):
        GPIO.cleanup()
                
    """
    The Cable Insertion method. 
    Extracts both lines and points from the image. 
    """

    def evaluate(self, debugPrint = False, specificPic = None):
        self.correct_pos = False
		#Use this to use the captured picture and the other one for a specific file
        if specificPic is None:
            GPIO.output(17, GPIO.HIGH)
            self.camera.capture(self.raw, format="bgr") #Takes the picture and saves it on raw
            GPIO.output(17, GPIO.LOW)
            print("Click!")
            img = self.raw.array
            filename = str(datetime.datetime.now()) + ".jpg"
            cv2.imwrite(filename,img)	#Saves the image for potential later use
        else:
            img = cv2.imread(specificPic + '.jpg')
        if img is None:  
            log.camera.warning('Failed to load image file.')
            return

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)	#converts to grayscale
        gray = cv2.blur(gray, (5,5))
        cv2.imwrite("blur.jpg",gray)
        edged = cv2.Canny(gray, 50, 100, None, apertureSize = 3)	#Canny edge detection to find the edges of the picture
        lines = cv2.HoughLines(edged,1,np.pi/360,180)	#Uses Hough line detection to find the most concurrent
        #edges (i.e. the longest lines). The third value is the resolution for the measurements and the fourth value is the
        #threshold. The threshold determines how many times a line must be detected to qualify, lower it if no lines can be found.
        """
        The following code filters out lines that are not horizontal or vertical.
        It also saves the line values in lists depending on if they're horizontal or vertical.
        """
        rhoHor = []
        rhoVer = []
        thetaHor = []
        thetaVer = []
        cv2.imwrite('test.jpg',edged)
        if lines is not None:
            for i in range(len(lines)):
                rho = lines[i][0][0]
                theta = lines[i][0][1]
                if (theta % (math.pi/2)) < 0.05:
                    if theta%(math.pi) < 0.05:
                        thetaVer.append(theta)
                        rhoVer.append(rho)
                    else:
                        thetaHor.append(theta)
                        rhoHor.append(rho)
        else:
            log.camera.warning("No lines found")
            return None
        """
    The following code take the second most common angle to make sure that
    the angles are aligned with the object. If not used the most common angle
    is 0 and the left and rightmost lines will have bad angles because of how
    the algorithm works.
    The rest of the code iterates over all vertical and horizontal lines to 
    find the outermost lines by continously updating a Final value if the 
    rho is smaller/larger than the smallest/largest value found yet. 
    So you end up with the outermost lines.
        """
        #verMax = Counter(thetaVer).most_common(2)[1][0]
        #horMax = Counter(thetaHor).most_common(2)[1][0]
        rhoFinal = [0, 3000, 0, 3000]
        thetaFinal = [0, 0, 0, 0]
        for i in range(len(rhoVer)):
            if rhoVer[i] < rhoFinal[1] and thetaHor[i] != 0:
                rhoFinal[1] = rhoVer[i]
                thetaFinal[1] = thetaVer[i]
            elif rhoVer[i] > rhoFinal[0]:
                rhoFinal[0] = rhoVer[i]
                thetaFinal[0] = thetaVer[i]
        for i in range(len(rhoHor)):
            if rhoHor[i] < rhoFinal[3]:
                rhoFinal[3] = rhoHor[i]
                thetaFinal[3] = thetaHor[i]
            elif rhoHor[i] > rhoFinal[2]:
                rhoFinal[2] = rhoHor[i]
                thetaFinal[2] = thetaHor[i]
        """
        Takes the outermost lines and saves them (and prints them on the original
        image if debugPrint is set to True). Then the lines are used to find the
        intersections of the lines (which can also be printed).
        TODO: translate the intersection points to robotstudio movements.
        Could be done both inside and outside this function.		
        """
        finalLines = []
        thetaSum = 0
        thetas = 0
        for i in range(4):
            rho = rhoFinal[i]
            theta = thetaFinal[i]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 3000*(-b))
            y1 = int(y0 + 3000*(a))
            x2 = int(x0 - 3000*(-b))
            y2 = int(y0 - 3000*(a))
            line = [[x1,y1],[x2,y2]]
            finalLines.append(line)
            if debugPrint:
                print(rho)
                print(theta)
                print()
                cv2.line(img,(x1,y1),(x2,y2),(255,255,0),10)
            if theta % (math.pi/2) > 0.001:
                if theta % (math.pi/2)>(math.pi/4):
                    theta = (math.pi/2) - theta
                else:
                    theta = theta % (math.pi/2)
                thetaSum += theta
                thetas += 1
        if thetas > 0:
            thetaZ = thetaSum/thetas
        else:
            thetaZ = 0
        p1 = self.line_intersection(finalLines[1], finalLines[3])
        p2 = self.line_intersection(finalLines[0], finalLines[3])
        p3 = self.line_intersection(finalLines[1], finalLines[2])
        p4 = self.line_intersection(finalLines[0], finalLines[2])
        mid = self.line_intersection((p1,p4), (p2,p3))
        #dist1 = self.point_distance(p1, (self.edgeX, self.edgeY))
        #dist2 = self.point_distance(p2, (3280 - self.edgeX, self.edgeY))
        #dist3 = self.point_distance(p3, (self.edgeX, 2464 - self.edgeY))
        #dist4 = self.point_distance(p4, (3280 - self.edgeX, 2464 - self.edgeY))

        p1new = self.rotate(mid, p1, thetaZ)
        p2new = self.rotate(mid, p2, thetaZ)
        p3new = self.rotate(mid, p3, thetaZ)
        p4new = self.rotate(mid, p4, thetaZ)

        dist1 = self.point_distance(p1new, (self.edgeX, self.edgeY))
        dist2 = self.point_distance(p2new, (3280 - self.edgeX, self.edgeY))
        dist3 = self.point_distance(p3new, (self.edgeX, 2464 - self.edgeY))
        dist4 = self.point_distance(p4new, (3280 - self.edgeX, 2464 - self.edgeY))

        dx = (dist1[0] + dist2[0] + dist3[0] + dist4[0])/4
        dy = (dist1[1] + dist2[1] + dist3[1] + dist4[1])/4
        if debugPrint:
            cv2.circle(img,p1,30,(0,0,255),10)
            cv2.circle(img,p2,30,(0,0,255),10)
            cv2.circle(img,p3,30,(0,0,255),10)
            cv2.circle(img,p4,30,(0,0,255),10)
            cv2.circle(img,(640, 382),30,(0,255,0),10)
            cv2.circle(img,(2640, 2082),30,(0,255,0),10)
            cv2.circle(img,(2640, 382),30,(0,255,0),10)
            cv2.circle(img,(640, 2082),30,(0,255,0),10)
            """
            cv2.circle(img,p1new,10,(255,0,255),10)
            cv2.circle(img,p2new,10,(255,0,255),10)
            cv2.circle(img,p3new,10,(255,0,255),10)
            cv2.circle(img,p4new,10,(255,0,255),10)
            """
            cv2.line(img,mid,(int(mid[0] - dx), int(mid[1] - dy)),(0,255,0),15)
            if specificPic:
                picSplit = specificPic.split('.')
                printString = 'hough' + picSplit[1] + '.jpg'
                cv2.imwrite(printString,img)
            else:
                cv2.imwrite("hough.jpg",img)
        if dx <= self.threshold and dy <= self.threshold:
            dx = 0
            dy = 0
            self.correct_pos = True
        
        return thetaZ, -(dx/self.width*13.7), -(dy/self.width*13.7)

    def line_intersection(self, line1, line2):
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1]) #Typo was here

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if div == 0:
            log.camera.warning("lines (" + str(xdiff[0]) + ", " + str(ydiff[0]) + " and (" + str(xdiff[1]) + ", " + str(ydiff[1]) + ") do not intersect")
            raise Exception('lines do not intersect')

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return int(x), int(y)

    def point_distance(self, p1, p2, hypot = False):
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        if hypot:
            return math.hypot(dx, dy)
        else:
            return (dx, dy)
    def rotate(self, origin, point, angle):
        """
        Rotate a point counterclockwise by a given angle around a given origin.

        The angle should be given in radians.
        """
        ox, oy = origin
        px, py = point
        angle = - angle

        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return int(qx), int(qy)
    
		
		
#test
#cam = Camera()
#print(cam.cableInsertion(True))


##sleep(5)
#imgblur = cv2.imread('max.jpg', 0)
#img = cv2.GaussianBlur(img, (7,7), 0)
#img = cv2.blur(imgblur, (7,7))

##hls = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
##lower = np.array([0,205,0])
##upper = np.array([255,255,255])

##mask = cv2.inRange(hls, lower, upper)
#edged = cv2.dilate(edged, None, iterations = 1)
#edged = cv2.erode(edged, None, iterations = 1)



