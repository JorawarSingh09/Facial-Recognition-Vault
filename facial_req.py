#! /usr/bin/python

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import imutils
import pickle
import time
import cv2
import pyfirmata
import RPi.GPIO as GPIO
from time import sleep
import os
import glob
import picamera
import smtplib

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN) #input from motions sensor

#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "unknown"
#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())

# initialize the video stream and allow the camera sensor to warm up
# Set the ser to the followng
# src = 0 : for the build in single web cam, could be your laptop webcam
# src = 2 : I had to set it to 2 inorder to use the USB webcam attached to my laptop
#vs = VideoStream(src=2,framerate=10).start()
vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()

#arduino setup
board = pyfirmata.Arduino("/dev/ttyACM0")
it = pyfirmata.util.Iterator(board)
it.start()

pin9 = board.get_pin('d:9:s')
pin9.write(180)
sleep(0.015)

sender = 'jorarpi6411@gmail.com'
password = 'COMP6441somethingAwesome!'
receiver = 'jora090901@gmail.com'

DIR = './capture/'
FILE_PREFIX = 'motion_image'



def send_mail():
	print 'Sending E-Mail'
	#check if path to capture folder exists
	#if not make it
	if not os.path.exists(DIR):
		os.makedirs(DIR)
    # Find the largest ID of existing images.
    # Start new images after this ID value.
	files = sorted(glob.glob(os.path.join(DIR, FILE_PREFIX + '[0-9][0-9][0-9].jpg')))
	count = 0
    #if there are already files in folder,
	# start filename count from last filename + 1
	if len(files) > 0:
        # Grab the count from the last filename.
		count = int(files[-1][-7:-4])+1

    # Save image to file
	filepath = os.path.join(FILE_PREFIX + '%03d.jpg' % count)
	filename = FILE_PREFIX + '%03d.jpg' % count
	#open directory
	os.chdir(DIR)
	# Capture the face and save to DIR
	cv2.imwrite(filename, frame)
    # Sending mail
	msg = MIMEMultipart()
	msg['From'] = sender
	msg['To'] = receiver
	msg['Subject'] = 'Movement Detected'

	#email contents
	body = 'Motion detected near vault. Frame at time of event attached below.'
	msg.attach(MIMEText(body, 'plain'))
	attachment = open(filepath, 'rb')
	part = MIMEBase('application', 'octet-stream')
	part.set_payload((attachment).read())
	#configure attachment
	encoders.encode_base64(part)
	part.add_header('Content-Disposition', 'attachment; filename= %s' % filename)
	msg.attach(part)
	#send email throuhg smtp server
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(sender, password)
	text = msg.as_string()
	server.sendmail(sender, receiver, text)
	server.quit()

# loop over frames from the video file stream
while True:

	# grab the frame from the threaded video stream and resize it
	# to 500px (to speedup processing)
	frame = vs.read()
	frame = imutils.resize(frame, width=500)
	# Detect the fce boxes
	boxes = face_recognition.face_locations(frame)
	# compute the facial embeddings for each face bounding box
	encodings = face_recognition.face_encodings(frame, boxes)
	names = []

	if GPIO.input(10) != GPIO.HIGH:
			print("HI")
			pin9.write(180)
			sleep(30)

	i = GPIO.input(11)
	if i == 1:  # When output from motion sensor is HIGH
		print("Motion detected")
		send_mail()

	# loop over the facial embeddings
	for encoding in encodings:

		# attempt to match each face in the input image to our known
		# encodings
		matches = face_recognition.compare_faces(data["encodings"],
			encoding)
		name = "Unknown" #if face is not recognized, then print Unknown


		# check to see if we have found a match
		if True in matches:
			# find the indexes of all matched faces then initialize a
			# dictionary to count the total number of times each face
			# was matched
			matchedIdxs = [i for (i, b) in enumerate(matches) if b]
			counts = {}

			# loop over the matched indexes and maintain a count for
			# each recognized face face
			for i in matchedIdxs:
				name = data["names"][i]
				counts[name] = counts.get(name, 0) + 1

			# determine the recognized face with the largest number
			# of votes (note: in the event of an unlikely tie Python
			# will select first entry in the dictionary)
			name = max(counts, key=counts.get)
			#If someone in your dataset is identified, print their name on the screen
			currentname = name
			if currentname != "unknown":
				print(currentname)
				#open lock
				pin9.write(20)
				sleep(0.015)
				#if the button is pressed lock the device again
				if GPIO.input(10) != GPIO.HIGH:
					print("HI")
					pin9.write(180)
					sleep(30)



		# update the list of names
		names.append(name)

	# loop over the recognized faces
	for ((top, right, bottom, left), name) in zip(boxes, names):
		# draw the predicted face name on the image - color is in BGR
		cv2.rectangle(frame, (left, top), (right, bottom),
			(0, 255, 225), 2)
		y = top - 15 if top - 15 > 15 else top + 15
		cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
			.8, (0, 255, 255), 2)

	# display the image to our screen
	cv2.imshow("Facial Recognition is Running", frame)
	key = cv2.waitKey(1) & 0xFF

	# quit when 'q' key is pressed
	if key == ord("q"):
		break

	# update the FPS counter
	fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
