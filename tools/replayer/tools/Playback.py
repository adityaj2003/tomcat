import json
import os
import sys
import time
import sched
from datetime import datetime
import paho.mqtt.client as mqtt
from operator import itemgetter, attrgetter

##################################
# End Imports
##################################

class observation:
    timestamp = None
    message = None
    topic = None
    timeObj = None

    def __init__(self, observation):
        self.timestamp = observation.get("@timestamp")
        self.message = json.dumps(observation) #observation.get("message")
        self.topic = observation.get("topic")
        self.timeObj = datetime.strptime(self.timestamp,"%Y-%m-%dT%H:%M:%S.%fZ")

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)

class header:
    version = None
    message_type = None
    timestamp = None

    def __init__(self, observation):
        self.version = observation.get("version")
        self.message_type = observation.get("message_type")
        self.timestamp = observation.get("timestamp")

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)



##################################
# End Sub Classes
##################################


class PlayBack:

    dataset = []
    mqttc = None

    def cut_pre_mission_msgs(self, arr):
        idx = 0
        for el in arr:
            if el.topic == 'observations/events/mission' \
                    and el.message.casefold().find("\"mission_state\":\"start\"") != -1:
                break
            idx += 1
        return arr[idx:]

    def __init__(self, file):
        #Generate MQTT Client
        self.mqttc = mqtt.Client("Psi-Coach Agent", True, None)
        self.mqttc.connect("localhost", 1883, 600)
        self.dataset = []
        with open(file) as json_file:
            line = json_file.readline()
            while line:
                if line == None:
                    break
                self.dataset.append(observation(json.loads(line)))
                line = json_file.readline()
        data_sorted = sorted(self.dataset, key=attrgetter('timeObj'))
        #mission_only = self.cut_pre_mission_msgs(data_sorted)
        self.dataset = data_sorted #mission_only
        self.start()

    def publish(self, topic, message):
        self.mqttc.publish(topic, message, 0, True)

    def start(self):
        messageTime = self.dataset[0].timeObj
        s = sched.scheduler(time.time, time.sleep)
        for i in range(0, len(self.dataset)):
            currentTime =self.dataset[i].timeObj
            s.enter((currentTime - messageTime).total_seconds(), 1, self.publish, argument=(self.dataset[i].topic, self.dataset[i].message,))
        s.run()


if __name__ == "__main__":
    pb = PlayBack(sys.argv[1])

