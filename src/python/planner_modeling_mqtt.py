import paho.mqtt.client as mqtt
import time

#  # Subscribing within on_connect() renewconnection if disconnected. 
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Now connected with result code "+str(rc))
    else:
        print("Bad connection. Result code =", rc)
    client.subscribe("agents/tomcat_tmm")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("on_message:", msg.topic+" "+str(msg.payload))
    # arg 1 = topic.   arg 2 = "the message itself." 
    client.publish("agents/tomcat_planner", "dummy data from planner"
                   " hard-coded inside planner_modeling_mqtt.py")

# Create client
MQTTC = mqtt.Client()

# Binds callback functions. Without these, then the on_connect() and
  #the on_message() functions won't be called.
MQTTC.on_connect = on_connect
MQTTC.on_message = on_message

# Connects to broker
MQTTC.connect("localhost", 1883, 60)

MQTTC.loop_forever()
