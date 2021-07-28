MQTT_HOST="localhost"
MQTT_PORT=1883

for FILE in trials/*; do ./replayer --trial_directory $FILE --mqtt_host $MQTT_HOST --mqtt_port $MQTT_PORT > $FILE.metadata_replay; done
