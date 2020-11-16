#!/usr/bin/env python3

"""
IHMC Location Monitor

Reads Area information from a JSON Map file and reports entity Area
change events when they occur

Author: Roger Carff
email:rcarff@ihmc.us
"""

import os
import time
import json
import uuid
from datetime import datetime
from RawConnection import RawConnection, RawMessage
from SemanticMap import SemanticMap

__author__ = 'rcarff'

connected_to_mqtt = False
trial_infos = {}


def check_location_update(trial_info_key, timestamp, name, x, z):
    global trial_infos

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

    # print(f'{name} is at ({x},{z}) at {timestamp}')

    current_locations = trial['semantic_map'].get_locations_containing(x, z)
    current_connections = trial['semantic_map'].get_connections_containing(x, z)

    exiting_locations = []
    exiting_connections = []

    previous_locations = player_info['previous']['locations']
    previous_connections = player_info['previous']['connections']

    for location in previous_locations:
        if location not in current_locations:
            exiting_locations.append(location)
    for connection in previous_connections:
        if connection not in current_connections:
            exiting_connections.append(connection)

    # if nothing has changed, then do not send an update!!
    if not first_time and \
            len(current_locations) == len(previous_locations) and \
            len(current_connections) == len(previous_connections) and \
            len(exiting_locations) == 0 and len(exiting_connections) == 0:
        return

    player_info['previous']['locations'] = current_locations
    player_info['previous']['connections'] = current_connections

    data = {'playername': name}
    if len(current_locations) <= 0 and len(current_connections) <= 0:
        data['locations'] = [{'id': 'UNKNOWN', 'name': 'The Player is in an Unknown Location!!!'}]
    else:
        if len(current_locations) > 0:
            data['locations'] = []
            for location in current_locations:
                data['locations'].append({'id': location['id'],
                                          'name': location['name'] if 'name' in location.keys() else ''})
        if len(current_connections) > 0:
            data['connections'] = []
            for connection in current_connections:
                data['connections'].append({'id': connection['id'],
                                            'connected_locations': connection['connected_locations']
                                            if 'connected_locations' in connection.keys() else []})
    if len(exiting_locations) > 0:
        data['exited_locations'] = []
        for location in exiting_locations:
            data['exited_locations'].append({'id': location['id'],
                                             'name': location['name'] if 'name' in location.keys() else ''})
    if len(exiting_connections) > 0:
        data['exited_connections'] = []
        for connection in exiting_connections:
            data['exited_connections'].append({'id': connection['id'],
                                               'connected_locations': connection['connected_locations']
                                               if 'connected_locations' in connection.keys() else []})
    print(data)

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
    else:
        print('- Disconnected from the Message Bus!!')


# MQTT Message callback
#  Called when there is a message on the message bus for a topic which we are subscribed to
def on_message(message):
    global missions
    global trial_infos

    try:
        json_dict = message.jsondata
        message_type = json_dict["header"]["message_type"]
        msg = json_dict["msg"]

        trial_id = msg['trial_id'] if 'trial_id' in msg.keys() else 'NO_TRIAL_ID'
        replay_id = msg['replay_id'] if 'replay_id' in msg.keys() else None
        key = trial_id + ":" + str(replay_id)

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
                    return

        if trial_key not in trial_infos.keys():
            return

        if message_type == "observation" and sub_type == 'state':
            timestamp = msg['timestamp']
            name = data['name']
            x = data['x']
            z = data['z']

            check_location_update(key, timestamp, name, x, z)

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

    except Exception as ex:
        print(ex)
        print('RX Error, topic = {0}'.format(message.key))


missions = {}

# see if the config.json file exists and load the maps filename mapping.
configFolder = ''
# if not os.path.exists(configFolder):
#     configFolder = '../ConfigFolder'
# if os.path.exists(configFolder + '/config.json'):
#     with open(configFolder + '/config.json') as config_file:
#         config = json.load(config_file)
#         if 'maps' in config.keys():
#             missions = config['maps']

with open('config.json') as config_file:
    config = json.load(config_file)
    if 'maps' in config.keys():
        missions = config['maps']

print("Starting the MQTT Bus pub/sub system...")
message_bus = RawConnection("IHMCLocationMonitorAgent:" + str(uuid.uuid4()))
message_bus.onConnectionStateChange = on_connection
message_bus.onMessage = on_message

while True:
    if not connected_to_mqtt:
        try:
            print("- Trying to connect to the MQTT Message Bus...")
            message_bus.connect()
        except Exception as ex:
            print("- Failed to connect, MQTT Message Bus is not running!!")
    else:
        time_now = int(round(time.time() * 1000))
        trial_keys = list(trial_infos.keys())
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
                if time_now > last_timestamp + 2000:
                    print(
                        f'- No new info for player: {trial_key}:{player_key} in over 2 seconds so they have been removed.')
                    del trial_info['players'][player_key]
                    if len(trial_info['players']) <= 0:
                        print(f'- No Players associated with trial:{trial_key} so it has been removed.')
                        del trial_infos[trial_key]
                # else:
                #     # TODO: Could output an update here every second if we want to
    time.sleep(1)
