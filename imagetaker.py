import time
import picamera
import json
import numpy as np
import cv2
import base64
import paho.mqtt.client as mqtt

# Setup MQTT client
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

try:
    # Connect to MQTT server
    mqtt_client.connect('172.20.10.13', 1883, 30)

    # Enable camera
    with picamera.PiCamera() as camera:
        # Define camera parameters
        camera.resolution = (320, 320)
        camera.framerate = 5
        camera.start_preview()

        # Give the camera some warm-up time
        time.sleep(2)

        # count = 0 -> for debugging
        while True:
            # start = time.time() -> for debugging
            # count += 1 -> for debugging

            # Capture image
            img_output = np.empty((320, 320, 3), dtype=np.uint8)
            camera.capture(img_output, 'rgb', use_video_port=True)

            # finish = time.time() -> for debugging

            # Encode image to JPEG
            retval, buffer = cv2.imencode('.jpg', img_output)
            b64buffer = base64.b64encode(buffer)

            # Prepare message for MQTT
            message = {"message": b64buffer.decode("utf-8")}
            output = json.dumps(message)

            # Publish image over MQTT
            mqtt_client.publish('emgym/security/camera', output)

            # print(count) -> for debugging
            # print(finish - start) -> for debugging

except Exception as e:
    print("An error occurred:", e)
