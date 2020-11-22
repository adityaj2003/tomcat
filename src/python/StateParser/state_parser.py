#!/usr/bin/env python3

"""
State parser for the human subjects data

Encode data into actions and other info (location, effect, etc.)， in which the keys are action numbers

"""

import time
import json
import uuid
import paho.mqtt.client as mqtt
import copy

__author__ = 'liangzh'

connected_to_mqtt = False
trial_infos = {}
TOTAL_TIME = 600
is_searching = False
fov_dict = {}
victims_list = {}

current_coordinates = None
current_location = None
exited_location = None
is_exiting_location = False
is_triaging = False
current_action_start_timestamp = None
current_action_start_observation_number = None
current_action_end_observation_number = None

semantic_map_filename = 'Falcon_sm_v1.0.json'
map_info_json = None

with open(semantic_map_filename) as json_file:
    map_info_json = json.load(json_file)


def get_location_type(current_location_id):
    global map_info_json
    for location in map_info_json['locations']:
        if current_location_id == location['id']:
            return location['type']
    return 'Unknown'


# MQTT Message callback
#  Called when there is a message on the message bus for a topic which we are subscribed to
def on_message(message):
    global missions
    global trial_infos
    global states_json
    global action_number
    global is_searching
    global fov_dict

    global current_action_start_timestamp
    global current_location
    global exited_location
    global current_action_start_observation_number
    global current_action_end_observation_number
    global is_exiting_location
    global current_coordinates
    global is_triaging

    try:
        json_dict = message.jsondata
        message_type = json_dict["header"]["message_type"]
        msg = json_dict["msg"]

        trial_id = msg['trial_id'] if 'trial_id' in msg.keys() else 'NO_TRIAL_ID'
        replay_id = msg['replay_id'] if 'replay_id' in msg.keys() else None
        key = trial_key = trial_id + ":" + str(replay_id)

        data = {}
        if 'data' in json_dict.keys():
            data = json_dict['data']

        sub_type = ''
        if 'sub_type' in msg.keys():
            sub_type = msg['sub_type'].lower()

        # Process Trial Start by initializing the Trial Info and loading the Semantic Map
        if message_type == 'trial' and sub_type == 'start':
            experiment_mission = data['experiment_mission'] if 'experiment_mission' in data.keys() else None
            experiment_id = msg['experiment_id'] if 'experiment_id' in msg.keys() else None
            replay_root_id = msg['replay_root_id'] if 'replay_root_id' in msg.keys() else None

            print(f'New Trial_id: {key}')
            trial_infos[key] = {
                'experiment_id': experiment_id,
                'trial_id': trial_id,
                'replay_root_id': replay_root_id,
                'replay_id': replay_id,
                'players': {}}

            print('new mission = ' + experiment_mission)
            for mission_prefix in missions.keys():
                print(f' checking with prefix: {mission_prefix.lower()}')
                if experiment_mission.lower().startswith(mission_prefix.lower()):
                    trial_infos[key]['mission_file'] = missions[mission_prefix]['filename']
                    states_json['trial_key'] = key
                    return

        if trial_key not in trial_infos.keys():
            return

        if message_type == 'event' and sub_type == 'event:location':
            if not is_triaging:
                if 'locations' in data.keys():
                    if current_location is None:
                        for location in data['locations']:
                            if 'Part of ' not in location['name']:
                                current_location = location
                                return
                    else:
                        for location in data['locations']:
                            if 'Part of ' not in location['name']:
                                if location['name'] == current_location['name']:
                                    return

                        is_exiting_location = True
                        is_searching = False

                        data_tmp = {}
                        data_tmp['time_stamp'] = current_action_start_timestamp

                        data_tmp['action'] = 'search_hallway'
                        data_tmp['coordinates'] = current_coordinates
                        data_tmp['locations'] = []
                        data_tmp['locations'] = [current_location]

                        if get_location_type(current_location['id']) == 'room' or get_location_type(
                                current_location['id']) == 'room_part':
                            data_tmp['action'] = 'search_room'

                        data_tmp['start_observation_number'] = current_action_start_observation_number
                        data_tmp['end_observation_number'] = current_action_end_observation_number
                        states_json[action_number] = data_tmp
                        action_number += 1

                        exited_location = current_location

                        for location in data['locations']:
                            if 'Part of ' not in location['name']:
                                current_location = location
                                break

        if message_type == "observation" and sub_type == 'state':
            if data['mission_timer'] != 'Mission Timer not initialized.':
                if not is_triaging:
                    timestamp = data['mission_timer']
                    observation_number = data['observation_number']
                    x = data['x']
                    z = data['z']

                    if is_searching:
                        current_coordinates = [x, z]
                        current_action_end_observation_number = observation_number

                    else:
                        is_searching = True
                        try:
                            m, s = timestamp.strip().split(":")
                            current_action_start_timestamp = TOTAL_TIME - (int(m) * 60 + int(s))
                        except:
                            current_action_start_timestamp = timestamp

                        current_coordinates = [x, z]
                        current_action_start_observation_number = current_action_end_observation_number = observation_number

                    if is_exiting_location:
                        is_exiting_location = False
                        data_tmp = {}
                        try:
                            m, s = timestamp.strip().split(":")
                            data_tmp['time_stamp'] = TOTAL_TIME - (int(m) * 60 + int(s))
                        except:
                            data_tmp['time_stamp'] = timestamp
                        data_tmp['action'] = 'move'
                        data_tmp['coordinates'] = [x, z]
                        data_tmp['locations'] = []
                        data_tmp['locations'].append({'id': current_location['id'],
                                                      'name': current_location[
                                                          'name'] if 'name' in current_location.keys() else ''})
                        data_tmp['exited_locations'] = []
                        data_tmp['exited_locations'].append({'id': exited_location['id'],
                                                             'name': exited_location[
                                                                 'name'] if 'name' in exited_location.keys() else ''})

                        data_tmp['effect'] = ''
                        states_json[action_number] = data_tmp
                        action_number += 1

        if message_type == 'event' and sub_type == 'event:triage':
            if data['triage_state'] == 'IN_PROGRESS':
                data_tmp = {}
                try:
                    m, s = data['mission_timer'].strip().split(":")
                    data_tmp['time_stamp'] = TOTAL_TIME - (int(m) * 60 + int(s))
                except Exception as ex:
                    data_tmp['time_stamp'] = data['mission_timer']
                data_tmp['action'] = 'triage'
                data_tmp['victim_color'] = data['color']
                data_tmp['victim_coordinates'] = [data['victim_x'], data['victim_z']]
                data_tmp['effect'] = data['triage_state']
                states_json[action_number] = data_tmp
                is_triaging = True
            else:
                states_json[action_number]['effect'] = data['triage_state']
                action_number += 1
                is_triaging = False

            is_searching = False

        if message_type == "observation" and sub_type == 'fov':
            fov_dict[data['observation']] = data['blocks']

    except Exception as ex:
        print(ex)
        print('RX Error, topic = {0}'.format(message.key))


def get_search_effect(start_ob_number, end_ob_number):
    global fov_dict
    victims = {}
    for ob_number in range(int(start_ob_number), int(end_ob_number) + 1):
        for obj in fov_dict[ob_number]:
            victim_room_name = get_location_name(obj['location'][0], obj['location'][2])
            if obj['type'] == 'block_victim_1':
                victims[obj['id']] = {'type': 'Green', 'location': obj['location'], 'room': victim_room_name}
            elif obj['type'] == 'block_victim_2':
                victims[obj['id']] = {'type': 'Yellow', 'location': obj['location'], 'room': victim_room_name}
            elif obj['type'] == 'block_victim_expired':
                victims[obj['id']] = {'type': 'Dead', 'location': obj['location'],'room': victim_room_name}

    return victims


def get_location_name(x, z):
    for location in map_info_json['locations']:
        if 'bounds' in location.keys():
            lt_coordinates = location["bounds"]["coordinates"][0]
            br_coordinates = location["bounds"]["coordinates"][1]
            if lt_coordinates["x"] <= x <= br_coordinates["x"] and lt_coordinates["z"] <= z <= br_coordinates["z"]:
                return location['name'].strip('Part of ')
    return 'The Player is in an Unknown Location!!!'


def process_action_effect():
    global victims_list
    global trial_infos

    current_room = 'Entrance Walkway'

    for state in states_json:
        if current_room not in victims_list.keys():
            victims_list[current_room] = {'green_victim': {}, 'yellow_victim': {}, 'dead_victim': {},
                                          'triaged_green_victim': {}, 'triaged_yellow_victim': {}}
        if state == 'trial_key':
            continue

        if states_json[state]['action'] == 'search_hallway' or states_json[state]['action'] == 'search_room':
            current_room = states_json[state]['locations'][0]['name']
            try:
                searched_victims = get_search_effect(states_json[state]['start_observation_number'],
                                                     states_json[state]['end_observation_number'])
            except:
                states_json[state]['start_observation_number'] = states_json[state]['end_observation_number']
                searched_victims = get_search_effect(states_json[state]['start_observation_number'],
                                                     states_json[state]['end_observation_number'])

            states_json[state]['effect'] = {'victims': searched_victims}

            for victim in searched_victims:
                victim_room_name = get_location_name(searched_victims[victim]['location'][0],
                                                     searched_victims[victim]['location'][2])
                if victim_room_name not in victims_list.keys():
                    victims_list[victim_room_name] = {'green_victim': {}, 'yellow_victim': {}, 'dead_victim': {},
                                                      'triaged_green_victim': {}, 'triaged_yellow_victim': {}}
                if searched_victims[victim]['type'] == 'Green':
                    if victim not in victims_list[victim_room_name]['green_victim']:
                        victims_list[victim_room_name]['green_victim'][victim] = searched_victims[victim]
                elif searched_victims[victim]['type'] == 'Yellow':
                    if victim not in victims_list[victim_room_name]['yellow_victim']:
                        victims_list[victim_room_name]['yellow_victim'][victim] = searched_victims[victim]
                elif searched_victims[victim]['type'] == 'Dead':
                    if victim not in victims_list[victim_room_name]['dead_victim']:
                        victims_list[victim_room_name]['dead_victim'][victim] = searched_victims[victim]
                    if victim in victims_list[victim_room_name]['yellow_victim']:
                        del victims_list[victim_room_name]['yellow_victim'][victim]

        elif states_json[state]['action'] == 'move':
            current_room = states_json[state]['locations'][0]['name']

        elif states_json[state]['action'] == 'triage' and states_json[state]['effect'] == 'SUCCESSFUL':
            if states_json[state]['victim_color'] == 'Yellow':
                vic_x, vic_z = states_json[state]['victim_coordinates']

                victim_room_name = get_location_name(vic_x, vic_z)

                for victim in victims_list[victim_room_name]['yellow_victim']:
                    vic2_x, vic2_z = victims_list[victim_room_name]['yellow_victim'][victim]['location'][0], \
                                     victims_list[victim_room_name]['yellow_victim'][victim]['location'][2]
                    if vic_x == vic2_x and vic_z == vic2_z:
                        victims_list[victim_room_name]['triaged_yellow_victim'][victim] = \
                            victims_list[victim_room_name]['yellow_victim'][victim]
                        del victims_list[victim_room_name]['yellow_victim'][victim]
                        break
            elif states_json[state]['victim_color'] == 'Green':
                vic_x, vic_z = states_json[state]['victim_coordinates']
                # assert current_room == get_location_name(vic_x, vic_z)
                victim_room_name = get_location_name(vic_x, vic_z)
                for victim in victims_list[victim_room_name]['green_victim']:
                    vic2_x, vic2_z = victims_list[victim_room_name]['green_victim'][victim]['location'][0], \
                                     victims_list[victim_room_name]['green_victim'][victim]['location'][2]
                    if vic_x == vic2_x and vic_z == vic2_z:
                        victims_list[victim_room_name]['triaged_green_victim'][victim] = \
                            victims_list[victim_room_name]['green_victim'][victim]
                        del victims_list[victim_room_name]['green_victim'][victim]
                        break

        states_json[state]['info'] = copy.deepcopy(victims_list)

    return


class RawMessage(object):
    def __init__(self, key, payload=None, jsondata=None):
        self.key = key
        self.payload = payload
        if jsondata:
            self.payload = json.dumps(jsondata).encode('utf-8')

    @property
    def jsondata(self):
        return json.loads(self.payload.decode("utf-8"))

    def __repr__(self):
        return f"RawMessage(key='{self.key}',payload={self.payload})"


def __on_message(client, userdata, msg):
    callback = on_message
    if callback:
        try:
            callback(RawMessage(msg.topic, msg.payload))
        except Exception as ex:
            print('Failed message callback')
    else:
        print(str(msg.topic) + " " + str(msg.qos) + " " + str(msg.payload))


missions = {
    "Falcon": {"filename": "Falcon_sm_v1.0.json"},
    "Competency_Test": {"filename": "Competency_Test_sm_v1.0.json"}
}

print("Starting the MQTT Bus pub/sub system...")
message_bus = mqtt.Client("IHMCLocationMonitorAgent:" + str(uuid.uuid4()))

states_json = {}
action_number = 1
waiting_time = 10  # time waiting for parsing
is_starting_parsing = False
time_now = None
is_connected = False

while True:
    if not is_connected:
        try:
            print("- Trying to connect to the MQTT Message Bus...")
            message_bus.connect(host='localhost', port=1883)
            message_bus.loop_start()
            message_bus.on_message = __on_message

            is_connected = True
            print(f'- MQTT Msg Bus on_connection({is_connected})')
            if is_connected:
                print('- Connected to the Message Bus.')
                message_bus.subscribe("trial")
                message_bus.subscribe("observations/state")
                message_bus.subscribe("observations/events/mission")
                message_bus.subscribe("observations/events/player/location")
                message_bus.subscribe("observations/events/player/triage")
                message_bus.subscribe("agent/pygl_fov/player/3d/summary")
        except Exception as ex:
            print("- Failed to connect, MQTT Message Bus is not running!!")
    else:
        trial_keys = list(trial_infos.keys())
        if len(trial_keys) > 0 and not is_starting_parsing:
            is_starting_parsing = True
            time_now = int(round(time.time() * 1000))
            print('start parsing')

        for trial_key in trial_keys:
            if trial_key not in trial_infos.keys():
                continue
            trial_info = trial_infos[trial_key]
            player_keys = list(trial_info['players'])
            for player_key in player_keys:
                if player_key not in trial_info['players'].keys():
                    continue
                player = trial_info['players'][player_key]
                last_timestamp = player['timestamp']

    time.sleep(1)

    # holding 10 seconds for parsing
    if time_now is not None:
        if int(round(time.time() * 1000)) - time_now >= waiting_time * 1000:
            process_action_effect()
            saved_file_name = 'states_json3.json'
            with open(saved_file_name, 'w') as fp:
                json.dump(states_json, fp=fp, indent=4)
            print('finish parsing')
            break
