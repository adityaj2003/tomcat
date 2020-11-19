import paho.mqtt.client as mqtt

# The callback for when the MQTTC receives a CONNACK response from the server.
def on_connect(MQTTC, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
    MQTTC.subscribe("agents/tomcat_tmm")

# The callback for when a PUBLISH message is received from the server.
def on_message(MQTTC, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    # from elkless_replayer, line 88
    MQTTC.publish("agents/tomcat_planner", "dummy output from planner")


MQTTC = mqtt.Client()
MQTTC.on_connect = on_connect
MQTTC.on_message = on_message

MQTTC.connect("localhost", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
    # manual interface.
MQTTC.loop_forever()
