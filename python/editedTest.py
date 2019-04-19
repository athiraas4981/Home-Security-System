import cv2
import faceRecognition as fr

import time
import datetime
from picamera.array import PiRGBArray
from picamera import PiCamera
from tinydb import TinyDB, Query

# ------------- THIS IS THE ACTUAL TRAINING PART ------- 

#faces, faceID = fr.labels_for_training_data('trainingImages')

#face_recognizer = fr.train_classifier(faces, faceID)
#face_recognizer.save('trainingData.yml')
#exit()
	
	
if __name__ == '__main__':
	
 
	# initialize the camera and grab a reference to the raw camera capture
	
	camera = PiCamera()
	camera.resolution = (640, 480)
	camera.framerate = 32
	count = 0
	while True:
		rawCapture = PiRGBArray(camera, size=(640, 480))
		
		faces_detected, gray_img = fr.detect_face(camera, rawCapture)
		print faces_detected
		if not len(faces_detected):
			print("empty")
			count = 0
			continue
		else:
			print("Found")
			
		is_predicted, label, predicted_name, image = fr.identify_face(faces_detected, gray_img)
		
		if is_predicted == True:
			count = count + 1
		else:
			count = 0
			
		print count, is_predicted
			
		if count > 5:
			count = 0
			print("Found some one => ", label, "=> ", predicted_name)
			
			ts = time.time()
			url = str(ts) + '.png'
			dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
			st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
			
			cv2.imwrite('visitors/' + url, image)
			
			db = TinyDB('visitors.json')
			db.insert({'name': predicted_name, 'url': url, 'date': dt, 'time': st})
			print("Inserted")
			
			fr.send_push(predicted_name, st)
			
		time.sleep(0.1)
