import csv
from time import time, monotonic, sleep
from datetime import datetime
from common import request_clients_end
from network import receive, send

from .config_rest_state import REST_TIMER


class ServerRestState:
    def __init__(self, to_client_connections: list, from_client_connections: dict, 
                data_save_path: str = '') -> None:
        self._to_client_connections = to_client_connections
        self._from_client_connections = from_client_connections

        header = ['time', 'monotonic_time', 'human_readable_time',
                  'event_type']
        data_path = data_save_path + "/rest_state"

        csv_file_name = data_path + '/' + str(int(time()))

        self._csv_file = open(csv_file_name + ".csv", 'w', newline='')
        self._csv_writer = csv.DictWriter(
            self._csv_file, delimiter=';', fieldnames=header)
        self._csv_writer.writeheader()

    def run(self):
        data = {}
        data["type"] = "state"
        data["state"] = {}
        data["state"]["rest_timer"] = REST_TIMER

        print("[STATUS] Running rest state")
        send(self._to_client_connections, data)


        csv_entry = {"time": time(), "monotonic_time": monotonic(),
                        "human_readable_time": datetime.utcnow().isoformat() + "Z",
                        "event_type": "start_rest_state"}

        self._csv_writer.writerow(csv_entry)

        sleep(0.1)

        while(True):
            responses = receive(self._from_client_connections)
            response = list(responses.values())[0]
            if response["type"] == "STOP":
                csv_entry = {"time": time(), "monotonic_time": monotonic(),
                         "human_readable_time": datetime.utcnow().isoformat() + "Z",
                         "event_type": "end_rest_state"}

                self._csv_writer.writerow(csv_entry)  

                request_clients_end(self._to_client_connections)
                print("[STATUS] Rest state has ended")
                break
            else:
                print("[ERROR] Rest state clients didn't send STOP message for Rest state server to terminate")
