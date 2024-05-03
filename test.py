import cv2 as cv
import numpy as np 
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    print('Connected with result code ' + str(rc))
    client.subscribe('emgym/security/camera')
    
def on_message(client, userdata, msg):
    print(msg.topic + ' ' + str(msg.payload))
    
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

client.connect('test.mosquitto.org', 1883, 30)

client.publish('emgym/security/camera', 'Hello from Python!')

client.loop_forever()