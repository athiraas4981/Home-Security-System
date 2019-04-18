import cv2
import os
import numpy as np

from tinydb import TinyDB, Query

import time
from picamera.array import PiRGBArray
from picamera import PiCamera

import json, ast
from pusher_push_notifications import PushNotifications



def faceDetection(test_img):
    gray_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
    face_haar_cascade = cv2.CascadeClassifier('HaarCascade/haarcascade_frontalface_default.xml')
    #face_haar_cascade = cv2.CascadeClassifier('HaarCascade/haarcascade_frontalface_alt2.xml')
    faces = face_haar_cascade.detectMultiScale(gray_img,scaleFactor=1.32,minNeighbors=5)

    return faces,gray_img

def labels_for_training_data(directory):
	faces = []
	faceID = []
	img_path = ""
	i = 0
	users = {}
	for path, subdirnames, filenames in os.walk(directory):
		for filename in filenames:
			if filename.startswith("."):
				continue

			id = os.path.basename(path)
			img_path = os.path.join(path, filename)
			print("img_path: ", img_path)
			print("id: ", i)
			test_img = cv2.imread(img_path)
			if test_img is None:
				continue

			faces_rect, gray_img = faceDetection(test_img)
			
			if len(faces_rect) !=1:
				continue

			(x,y,w,h) = faces_rect[0]
			roi_gray = gray_img[y:y+w, x:x+h]

			faces.append(roi_gray)
			faceID.append(int(i))
			
		if path != "trainingImages":
			local_name = os.path.basename(path)
			users[i] = str(local_name)
			i = i + 1
	
	print users
	
	db = TinyDB('users.json')
	db.purge()
	db.insert(users)
	
	return faces, faceID

def train_classifier(faces, faceID):
	face_recognizer = cv2.createLBPHFaceRecognizer()
	face_recognizer.train(faces, np.array(faceID))

	return face_recognizer

def draw_rect(test_img, face):
	(x,y,w,h) = face
	cv2.rectangle(test_img, (x,y), (x+w, y+h),(255,0,0), thickness=5)

def put_text(test_img, text, x, y):
	cv2.putText(test_img, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, 5, (255,0,0), 6)


def detect_face(camera, rawCapture):
	 
	# allow the camera to warmup
	# capture frames from the camera
	for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		# grab the raw NumPy array representing the image, then initialize the timestamp
		# and occupied/unoccupied text
		image = frame.array
		faces_detected, gray_img = faceDetection(image)
	
		if len(faces_detected) != 0:
			for (x,y,w,h) in faces_detected:
				cv2.rectangle(image, (x,y), (x+w, y+h),(255,0,0), thickness=5)
				cv2.imwrite('images/c1.png', image)
				return faces_detected, gray_img
 			#break
 		
		return faces_detected, gray_img
		# show the frame
		#cv2.imshow("Frame", image)
		#key = cv2.waitKey(1) & 0xFF
	
		# clear the stream in preparation for the next frame
		rawCapture.truncate(0)
 
		# if the `q` key was pressed, break from the loop
		#if key == ord("q"):
		#	break


def identify_face(faces_detected, gray_img):
		
	test_img = cv2.imread('images/c1.png')
	face_recognizer = cv2.createLBPHFaceRecognizer()
	face_recognizer.load('trainingData.yml')

	#name = {0: "Arunjith", 1: "Athira", 2: "Rahul", 3: "Muneert", 4: "Nadiya"}

	db = TinyDB('users.json')
	users = db.all()
	name = {}

	for user in users:
		for i in user:
			name[int(i)] = user[i]
		
	users = ast.literal_eval(json.dumps(name))
	new_list = {}

	for user in users:
		new_list[int(user)] = users[user]
	name = new_list	
	print name

	for face in faces_detected:
	    (x,y,w,h) = face
	    roi_gray = gray_img[y:y+h, x:x+h]
	
	    label, confidence = face_recognizer.predict(roi_gray)
	
	    print("confidence: ", confidence)
	    print("label: ", label)
	
	    draw_rect(test_img, face)
	    predicted_name = name[label]
	    
	    isPredicted = False
	    if confidence > 500:
	        continue
	    else:
	    	isPredicted = True
	
	    #put_text(test_img, predicted_name, x, y)
	    return isPredicted, label, predicted_name, test_img
	
	
def send_push(name, time):
	
	beams_client = PushNotifications(
	    instance_id='97bc1b7f-aa2a-4760-af68-3052371c6dbd',
	    secret_key='17482EE2588EE046FBA7E20949EBB4CE00AA2325E6FCDDCD3E34202E0A79A5CB',
	)
	
	response = beams_client.publish_to_interests(
	    interests=['hello'],
	    publish_body={
	        'apns': {
	            'aps': {
	                'alert': 'Hello!'
	            }
	        },
	        'fcm': {
	            'notification': {
	                'title': 'New access request',
	                'body': name + " has been requested to open at " + time
	            }
	        }
	    }
	)

	print(response['publishId'])



