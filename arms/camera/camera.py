from picamera import PiCamera
from picamera.array import PiRGBArray
from time import sleep
import math
import numpy as np
import cv2
from collections import Counter
import datetime
import arms.utils.log as log

class Camera:
	"""
	Initializes the Camera object with a specified resolution,
	rotation and zoom. Also creates a raw variable that is used to
	handle the captured picture (so you don't need to save a file and
	open it). Then a short sleep to make sure everything is initialized.
	"""
	def __init__(self):
		self.camera = PiCamera()
		self.camera.resolution = (3280, 2464)
		self.camera.rotation = 180
		self.camera.zoom = (0.4, 0.4, 0.2, 0.2)
		self.raw = PiRGBArray(self.camera)
		log.camera.info("Camera initialized!")
		sleep(1)
		
	"""
	The Cable Insertion method. 
	Extracts both lines and points from the image. 
	"""

	def cableInsertion(self, debugPrint = False, points = True):
		self.camera.capture(self.raw, format="bgr") #Takes the picture and saves it on raw
		print("Click!")
		#Use this to use the captured picture and the other one for a specific file
		img = self.raw.array
		
		#img = cv2.imread('2018-10-01 15:13:49.347220.jpg')
		if img is None:  
			log.camera.warning('Failed to load image file.')
			return
		filename = str(datetime.datetime.now()) + ".jpg"
		cv2.imwrite(filename,img)	#Saves the image for potential later use
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
		verMax = Counter(thetaVer).most_common(2)[1][0]
		horMax = Counter(thetaHor).most_common(2)[1][0]
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
		for i in range(0,4):
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
				cv2.line(img,(x1,y1),(x2,y2),(0,0,255),2)
				
		p1 = self.line_intersection(finalLines[0], finalLines[2])
		p2 = self.line_intersection(finalLines[0], finalLines[3])
		p3 = self.line_intersection(finalLines[1], finalLines[2])
		p4 = self.line_intersection(finalLines[1], finalLines[3])
		if debugPrint:
			cv2.circle(img,p1,10,(0,255,0),2)
			cv2.circle(img,p2,10,(0,255,0),2)
			cv2.circle(img,p3,10,(0,255,0),2)
			cv2.circle(img,p4,10,(0,255,0),2)
			cv2.imwrite('hough.jpg',img)
			cv2.imwrite('test.jpg',edged)
		#cv2.waitKey(0)
			cv2.destroyAllWindows()
		if points:
			return p1, p2, p3, p4
		else:
			return finalLines
		
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



