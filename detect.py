import cv2 as cv
import numpy as np 
import paho.mqtt.client as mqtt
import time
import base64
import json
import threading
import datetime

from flask import Flask, render_template, jsonify

app = Flask(__name__)

count = 0
person_detected = False
queue = []
image_to_send_to_web = None
web_posts_queue = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/data')
def post_to_web():
    
    if (len(web_posts_queue) == 0):
        return jsonify({})
    data = jsonify(web_posts_queue)
    # print (web_posts_queue)
    web_posts_queue.clear()
    return data

def on_connect(client, userdata, flags, rc):
    print('Connected with result code ' + str(rc))
    client.subscribe('emgym/security/camera')
    
def on_message(client, userdata, msg):
    # convert string to numpy array
    if len(msg.payload) < 30:
        print("Invalid message")
        return
    payload = json.loads(msg.payload)
    decoded = base64.b64decode(payload["message"])
    # print (decoded)
    nparr = np.frombuffer(decoded, np.uint8)
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    global count
    count += 1
    # print(count)
    queue.append((img, payload["message"]))
    # print (img)
    
    
if __name__ == '__main__':
    
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect('172.20.10.13', 1883, 30)
    client.loop_start()
    
    t = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False)).start()



    net = cv.dnn.readNet('yolov3.weights', 'yolov3.cfg')

    classes = []
    with open('coco.names', 'r') as f:
        classes = [line.strip() for line in f.readlines()]


    layer_name = net.getLayerNames()

    output_layer = [layer_name[i - 1] for i in net.getUnconnectedOutLayers()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))


    # print ("test")

    while cv.waitKey(1) < 0:
        person = False
        if len(queue) == 0:
            continue
        img, encoded = queue.pop(0)
        height, width, channels = img.shape
        blob = cv.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        
        net.setInput(blob)
        outs = net.forward(output_layer)
        
        
        class_ids = []
        confidences = []
        boxes = []
        
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    # obj detect
                    
                    center_x = int(detection[0]*width)
                    center_y = int(detection[1]*height)
                    w = int(detection[2]*width)
                    h = int(detection[3]*height)
                    
                    x = int(center_x - w/2)
                    y = int(center_y - h/2)
                    
                    boxes.append([x,y,w,h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
                    
                    
        indexes = cv.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
                    
        font = cv.FONT_HERSHEY_PLAIN
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = str(classes[class_ids[i]])
                if label == 'person':
                    person = True
                
                color = colors[i]
                cv.rectangle(img, (x, y), (x+w, y+h), color, 2)
                cv.putText(img, label, (x, y+30), font, 3, color, 3)
                
        if person:
            person_detected = True
            image_to_send_to_web = img
            ts = time.time()
            web_posts_queue.append({'timestamp': datetime.datetime.fromtimestamp(int(ts))
      .strftime('%Y-%m-%d %H:%M:%S'), 'image': base64.b64encode(cv.imencode('.jpg', img)[1]).decode("utf-8")})
            print ("Person detected")
        else:
            person_detected = False
        # cv.putText(img, str(count1), (0, 0), font, 3, (255, 255, 255), 3)
        # cv.imshow("image", img)
        
    cv.destroyAllWindows()
        
        
    
