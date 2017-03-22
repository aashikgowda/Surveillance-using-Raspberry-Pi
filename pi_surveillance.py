'''
Reference
http://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
'''

# Import all necessary libraries
import cv2
import numpy as np
import os
import time
from datetime import datetime
from picamera.array import PiRGBArray
from picamera import PiCamera
from twilio.rest import TwilioRestClient
from twilio.rest.resources import Connection
from twilio.rest.resources.connection import  PROXY_TYPE_HTTP
import subprocess

# Frame count
i = 0
# Motion count
motion_count = 0
motion_flag = False
# Start timer
st_time = time.time()
# Initialize the average frame
avg_frame = None
# Initialize the PiCamera module
cam = PiCamera()
# Initialize the paramters of the PiCamera
cam.resolution = (640,480)                # Resolution of camera
cam.framerate = 24                        # Frame rate of camera
# Initialize raw capture stream of PiCamera
raw_Data = PiRGBArray(cam,size=(640,480))
# Warm up time for camera
time.sleep(5)

'''
Loop over the frames from the continuous stream of video feed
This is much faster than looping capturing an image each time
by looping through it each time
'''
for frame in cam.capture_continuous(raw_Data,format='bgr',use_video_port=True):
    # Get the timestamp
    i += 1
    t_stamp = datetime.now().strftime("%A %d %B %Y %I:%M:%S%p")
    # Store the raw captured frame in numpy array
    img = frame.array
    text = 'No Motion'
    # Convert RGB image to Grayscale image
    gscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    '''
    Apply Gaussian Blur to the grayscale image
    This reduces the overall noise in the image
    '''
    gscale = cv2.GaussianBlur(gscale,(21,21),0)

    # Execute following lines if this is the first frame
    if i == 1:
        print("Createing a model of the backgorund")
        avg_frame = gscale.copy().astype('float')
        # Clear the current stream data
        raw_Data.truncate(0)
        continue
    '''
    Update the average frame with the new grayscale image
    Less weightage is given to the new grayscale image
    '''
    cv2.accumulateWeighted(gscale,avg_frame,0.5)
    # Pixel intensity differnece between average and current frame
    frame_diff = cv2.absdiff(cv2.convertScaleAbs(avg_frame),gscale)
    # Convert image with pixel intensities above threshold to binary 1
    bin_img = cv2.threshold(frame_diff, 10, 255, cv2.THRESH_BINARY)[1]
    # Close the holes in the binary image
    bin_img = cv2.dilate(bin_img, None, iterations=2)

    # Function which finds all the contours in the image
    all_conts  = cv2.findContours(bin_img.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[1]
    # Loop over all the contours detected
    for cont in all_conts:
    	# Ignore the contour if it is small
    	if cv2.contourArea(cont) < 6000:
    	    continue
    	(x, y, w, h) = cv2.boundingRect(cont)
    	# Draw a rectagle around the contour
    	cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
    	text = "Motion Detected"
    	# Increase the motion count
    	motion_count += 1

    # Text message alert to user
    if motion_count > 3 and motion_flag is False:
        print("Alerting user")
		# Get these values at https://twilio.com/user/account
		account_sid = "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		auth_token = "93603XXXXXXXXXXXXXXXXXXXXXXXXXX"
		client = TwilioRestClient(account_sid, auth_token)
		# One time Text Message Alert
		message = client.messages.create(to="+1XXXXX9726", from_="+1XXXXX8071",
                                     body="Motion Detected - Please check dropbox!")
        motion_flag = True

    # Add the timestamp and required text onto the frame
    cv2.putText(img, "Room Status: {}".format(text), (10, 20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.putText(img, "Timestamp : " + t_stamp,(20, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    cv2.putText(img, "Frame : " + str(i),(20, img.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    # Display the resulting frame
    cv2.imshow("Live Feed", img)
    # Save the resulting image to synchronized dropbox folder   
	if text == 'Motion Detected':
		cv2.imwrite("Dropbox/"+ t_stamp + ".jpg",img)
    
    # Break loop if 'e' is pressed
    key = cv2.waitKey(1) & 0xFF
    if key == ord('e'):
        break
    # Clear the current stream data
    raw_Data.truncate(0)

cv2.destroyAllWindows()
print("Frames Captured : " + str(i))
print("-----%s seconds------" %(time.time() - st_time))

