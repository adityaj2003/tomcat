#!/usr/bin/env python3

"""
State parser for the human subjects data

Encode data into actions and other info (location, effect, etc.)， in which the keys are action numbers

"""

import os
import time
import json
import uuid
from datetime import datetime
from RawConnection import RawConnection, RawMessage
from SemanticMap import SemanticMap
import copy

__author__ = 'liangzh'

connected_to_mqtt = False
trial_infos = {}
TOTAL_TIME = 600
is_searching = False
fov_dict = {}
victims_list = {}


def check_location_update(trial_info_key, timestamp, name, x, z, observation_number):
    global trial_infos
    global states_json
    global action_number
    global is_searching

    if trial_info_key not in trial_infos.keys():
        return

    trial = trial_infos[trial_info_key]

    # get the current info for this player in this trial or create it if not there
    first_time = False
    if name not in trial['players'].keys():
        print(f'New player: {name} in trial: {trial_info_key}')
        player_info = {'name': name, 'x': 0.0, 'z': 0.0, 'previous': {'locations': [], 'connections': []}}
        trial['players'][name] = player_info
        first_time = True

    player_info = trial['players'][name]

    # update the last time we received something from this player
    player_info['timestamp'] = int(round(time.time() * 1000))

    # If the player has not moved just return
    if player_info['x'] == x and player_info['z'] == z:
        return

    # Update the player's position
    player_info['x'] = x
    player_info['z'] = z

    current_locations = trial['semantic_map'].get_locations_containing(round(x), round(z))

    for current_location in current_locations:
        if 'Part of ' not in current_location['name']:
            current_locations = [current_location]
            break

    current_connections = trial['semantic_map'].get_connections_containing(round(x), round(z))

    exiting_locations = []
    exiting_connections = []

    previous_locations = player_info['previous']['locations']
    previous_connections = player_info['previous']['connections']

    for location in previous_locations:
        if 'Part of ' in location['name']:
            continue
        for current_location in current_locations:
            if 'Part of ' in current_location['name']:
                continue
            if location['name'] != current_location['name']:
                exiting_locations.append(location)
                break

    # if nothing has changed, then do not send an update!!
    if not first_time and \
            len(current_locations) == len(previous_locations) and \
            len(current_connections) == len(previous_connections) and \
            len(exiting_locations) == 0 and len(exiting_connections) == 0:
        return

    player_info['previous']['locations'] = current_locations
    player_info['previous']['connections'] = current_connections

    data = {}

    try:
        m, s = timestamp.strip().split(":")
        data['time_stamp'] = TOTAL_TIME - (int(m) * 60 + int(s))
    except:
        data['time_stamp'] = timestamp

    data['action'] = 'search_hallway'
    data['coordinates'] = [x, z]

    if len(current_locations) <= 0 and len(current_connections) <= 0:
        data['locations'] = [{'id': 'UNKNOWN', 'name': 'The Player is in an Unknown Location!!!'}]
    else:
        if len(current_locations) > 0:
            data['locations'] = []
            for location in current_locations:
                if 'Part of ' not in location['name']:
                    data['locations'].append({'id': location['id'],
                                              'name': location['name'] if 'name' in location.keys() else ''})
                    break

            if location['type'] == 'room' or location['type'] == 'room_part':
                data['action'] = 'search_room'

        else:
            data['locations'] = [{'id': 'UNKNOWN', 'name': 'The Player is in an Unknown Location!!!'}]

        if not is_searching:
            data['start_observation_number'] = data['end_observation_number'] = observation_number
        else:
            data['end_observation_number'] = observation_number

    if len(exiting_locations) > 0:
        data['exited_locations'] = []
        for location in exiting_locations:
            data['exited_locations'].append({'id': location['id'],
                                             'name': location['name'] if 'name' in location.keys() else ''})
        data['action'] = 'move'
        is_searching = False

    data['effect'] = ''

    if is_searching:
        action_number -= 1
        states_json[action_number]['coordinates'] = data['coordinates']
        states_json[action_number]['end_observation_number'] = data['end_observation_number']
    else:
        if data['action'] == 'search_hallway' or data['action'] == 'search_room':
            states_json[action_number] = data
            is_searching = True
        else:
            del data['end_observation_number']
            states_json[action_number] = data

    action_number += 1

    send_event_msg('location', trial, timestamp, data)

    return


# Send an Observation Message with all the appropriate headers
def send_event_msg(sub_type, trial, timestamp, data=None):
    global message_bus

    json_dict = {}
    json_dict["header"] = {}
    json_dict["header"]["timestamp"] = str(datetime.utcnow().isoformat()) + 'Z'
    json_dict["header"]["version"] = "1.0"
    json_dict["header"]["message_type"] = "event"

    json_dict["msg"] = {}
    json_dict["msg"]["sub_type"] = 'Event:' + sub_type
    json_dict["msg"]["timestamp"] = timestamp
    json_dict["msg"]["experiment_id"] = trial['experiment_id']
    json_dict["msg"]["trial_id"] = trial['trial_id']
    if trial['replay_root_id'] is not None:
        json_dict["msg"]["replay_root_id"] = trial['replay_root_id']
    if trial['replay_id'] is not None:
        json_dict["msg"]["replay_id"] = trial['replay_id']
    json_dict["msg"]["version"] = "1.0"
    json_dict["msg"]["source"] = "IHMCLocationMonitorAgent"

    if data is not None:
        json_dict["data"] = data

    message_bus.publish(RawMessage("observations/events/player/" + sub_type, jsondata=json_dict))


# Send an groundtruth Message with all the appropriate headers
def send_groundtruth_msg(topic_type, sub_type, trial, timestamp, data=None):
    global message_bus

    json_dict = {}
    json_dict["header"] = {}
    json_dict["header"]["timestamp"] = str(datetime.utcnow().isoformat()) + 'Z'
    json_dict["header"]["version"] = "1.0"
    json_dict["header"]["message_type"] = "groundtruth"

    json_dict["msg"] = {}
    json_dict["msg"]["sub_type"] = 'SemanticMap:' + sub_type
    json_dict["msg"]["timestamp"] = timestamp
    json_dict["msg"]["experiment_id"] = trial['experiment_id']
    json_dict["msg"]["trial_id"] = trial['trial_id']
    if trial['replay_root_id'] is not None:
        json_dict["msg"]["replay_root_id"] = trial['replay_root_id']
    if trial['replay_id'] is not None:
        json_dict["msg"]["replay_id"] = trial['replay_id']
    json_dict["msg"]["version"] = "1.0"
    json_dict["msg"]["source"] = "IHMCLocationMonitorAgent"

    if data is not None:
        json_dict["data"] = data

    message_bus.publish(RawMessage("ground_truth/semantic_map/" + topic_type.lower(), jsondata=json_dict))


# MQTT Connection callback
#   Called when connected to or disconneted from the MQTT Message bus
def on_connection(is_connected, rc):
    global connected_to_mqtt
    global message_bus

    if connected_to_mqtt == is_connected:
        return

    connected_to_mqtt = is_connected
    print(f'- MQTT Msg Bus on_connection({is_connected})')
    if connected_to_mqtt:
        print('- Connected to the Message Bus.')
        message_bus.subscribe("trial")
        message_bus.subscribe("observations/state")
        message_bus.subscribe("observations/events/mission")
        message_bus.subscribe("ground_truth/mission/blockages_list")
        message_bus.subscribe("ground_truth/mission/victims_list")
        message_bus.subscribe("observations/events/player/triage")
        message_bus.subscribe("agent/pygl_fov/player/3d/summary")
    else:
        print('- Disconnected from the Message Bus!!')


# MQTT Message callback
#  Called when there is a message on the message bus for a topic which we are subscribed to
def on_message(message):
    global missions
    global trial_infos
    global states_json
    global action_number
    global is_searching
    global fov_dict

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
                'semantic_map': SemanticMap(),
                'players': {}}

            print('new mission = ' + experiment_mission)
            for mission_prefix in missions.keys():
                print(f' checking with prefix: {mission_prefix.lower()}')
                if experiment_mission.lower().startswith(mission_prefix.lower()):
                    print("Loading semanticMap: '" + missions[mission_prefix]['filename'] + "'")
                    trial_infos[key]['mission_file'] = missions[mission_prefix]['filename']
                    trial_infos[key]['semantic_map'].load_semantic_map(
                        os.path.join(configFolder, missions[mission_prefix]['filename']))

                    states_json['trial_key'] = key
                    return

        if trial_key not in trial_infos.keys():
            return

        if message_type == "observation" and sub_type == 'state':
            if data['mission_timer'] != 'Mission Timer not initialized.':
                timestamp = data['mission_timer']
                name = data['name']
                observation_number = data['observation_number']
                x = data['x']
                z = data['z']
                check_location_update(key, timestamp, name, x, z, observation_number)

        ti = trial_infos[trial_key]

        if message_type == 'groundtruth':
            if sub_type.lower() == 'mission:blockagelist' and 'mission_blockage_list' in data.keys():
                ti['semantic_map'].apply_blockages_list(data['mission_blockage_list'])
                ti['blockages_applied'] = True
            elif sub_type.lower() == 'mission:victimlist' and 'mission_victim_list' in data.keys():
                ti['semantic_map'].add_victims(data['mission_victim_list'])
                ti['victims_added'] = True

        if message_type == 'event' and sub_type == 'event:missionstate':
            if 'mission_state' in data.keys() and data['mission_state'].lower() == 'start':
                updates = ti['semantic_map'].get_updates()
                if len(updates) > 0:
                    # post a ground truth semantic map update message to the bus
                    gt_data = {'semantic_map': trial_info['mission_file'],
                               'updates': updates}
                    send_groundtruth_msg('updates', 'All_Updates', ti, msg['timestamp'], gt_data)

        if message_type == 'event' and sub_type == 'event:triage':
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

            if states_json[action_number - 1]['action'] == 'triage':
                action_number -= 1
                states_json[action_number]['victim_color'] = data['color']
                states_json[action_number]['effect'] = data['triage_state']
            else:
                states_json[action_number] = data_tmp
            action_number += 1
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
            if obj['type'] == 'block_victim_1':
                victims[obj['id']] = {'type': 'Green', 'location': obj['location']}
            elif obj['type'] == 'block_victim_2':
                victims[obj['id']] = {'type': 'Yellow', 'location': obj['location']}
            elif obj['type'] == 'block_victim_expired':
                victims[obj['id']] = {'type': 'Dead', 'location': obj['location']}

    return victims


def get_location_name(x, z):
    global states_json
    trial = trial_infos[states_json['trial_key']]

    current_locations = trial['semantic_map'].get_locations_containing(round(x), round(z))
    current_location = 'The Player is in an Unknown Location!!!'
    for current_location in current_locations:
        if 'Part of ' not in current_location['name']:
            current_location = current_location
            break
    return current_location['name']


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
                        victims_list[victim_room_name]['green_victim'] = {victim: searched_victims[victim]}
                        break
                elif searched_victims[victim]['type'] == 'Yellow':
                    if victim not in victims_list[victim_room_name]['yellow_victim']:
                        victims_list[victim_room_name]['yellow_victim'] = {victim: searched_victims[victim]}
                        break
                elif searched_victims[victim]['type'] == 'Dead':
                    if victim not in victims_list[victim_room_name]['dead_victim']:
                        victims_list[victim_room_name]['dead_victim'] = {victim: searched_victims[victim]}
                    if victim in victims_list[victim_room_name]['yellow_victim']:
                        del victims_list[victim_room_name]['yellow_victim'][victim]
                        break

        elif states_json[state]['action'] == 'move':
            current_room = states_json[state]['locations'][0]['name']

        elif states_json[state]['action'] == 'triage' and states_json[state]['effect'] == 'SUCCESSFUL':
            if states_json[state]['victim_color'] == 'Yellow':
                vic_x, vic_z = states_json[state]['victim_coordinates']
                for victim in victims_list[current_room]['yellow_victim']:
                    vic2_x, vic2_z = victims_list[current_room]['yellow_victim'][victim]['location'][0], \
                                     victims_list[current_room]['yellow_victim'][victim]['location'][2]
                    if vic_x == vic2_x and vic_z == vic2_z:
                        victims_list[current_room]['triaged_yellow_victim'][victim] = \
                            victims_list[current_room]['yellow_victim'][victim]
                        del victims_list[current_room]['yellow_victim'][victim]
                        break
            elif states_json[state]['victim_color'] == 'Green':
                vic_x, vic_z = states_json[state]['victim_coordinates']
                for victim in victims_list[current_room]['green_victim']:
                    vic2_x, vic2_z = victims_list[current_room]['green_victim'][victim]['location'][0], \
                                     victims_list[current_room]['green_victim'][victim]['location'][2]
                    if vic_x == vic2_x and vic_z == vic2_z:
                        victims_list[current_room]['triaged_green_victim'][victim] = \
                            victims_list[current_room]['green_victim'][victim]
                        del victims_list[current_room]['green_victim'][victim]
                        break

        states_json[state]['info'] = copy.deepcopy(victims_list)

    return


missions = {}
# Load config file
configFolder = ''
with open('config.json') as config_file:
    config = json.load(config_file)
    if 'maps' in config.keys():
        missions = config['maps']

print("Starting the MQTT Bus pub/sub system...")
message_bus = RawConnection("IHMCLocationMonitorAgent:" + str(uuid.uuid4()))
message_bus.onConnectionStateChange = on_connection
message_bus.onMessage = on_message

states_json = {}
action_number = 1
waiting_time = 10  # time waiting for parsing
is_starting_parsing = False
time_now = None

while True:
    if not connected_to_mqtt:
        try:
            print("- Trying to connect to the MQTT Message Bus...")
            message_bus.connect()
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
            saved_file_name = 'states_json.json'
            with open(saved_file_name, 'w') as fp:
                json.dump(states_json, fp=fp, indent=4)
            print('finish parsing')
            break
