Regarding planner_modeling_mqtt.py

This program enables messages written from agents/tomcat_tmm to be received
into agents/tomcat_planner. There is a hard-coded message in this mqtt file to
ensure communication. Feel free to delete that.

To run, open three different terminals.
Terminal 1: $python planner_modeling_mqtt.py
Terminal 2: $mosquitto_sub -t agents/tomcat_planner
Terminal 3: $mosquitto_pub -t agents/tomcat_tmm -m "messages from modeling."

Messages published in terminal 3 are printed in terminal 1
Hard-coded message in planner_modeling_mqtt.py will print in terminal 2.
If you modify the mqtt file, you must disconnect, then reconnect for changes to show
in the terminals.

updated 19 November 2020
