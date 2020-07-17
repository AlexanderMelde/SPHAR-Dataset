"""
View a Video using OpenCV to see if its encoding will be
 read correctly during further processing / training.

This Method is independent from installed Video-Viewers
 like VLC or the Ubuntu Default Video Player.

Author: Alexander Melde (alexander@melde.net)

Using code from
https://www.learnopencv.com/read-write-and-display-a-video-using-opencv-cpp-python/
"""

import cv2

VIDEO_PATH = "../CutUcaerial/out/Running/ucaerial_actions1_Running_16_0.mp4"

# Create a VideoCapture object and read from input file
cap = cv2.VideoCapture(VIDEO_PATH)

# Check if camera opened successfully
if not cap.isOpened():
    print("Error opening video stream or file")

# Read until video is completed
while cap.isOpened():
    # Capture frame-by-frame
    ret, frame = cap.read()

    if not ret:
        # Break the loop if no more frames in file
        break
    else:
        # Display the resulting frame
        cv2.imshow('Frame', frame)

        # Press Q on keyboard to  exit
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break


# When everything done, release the video capture object
cap.release()

# Closes all the frames
cv2.destroyAllWindows()
