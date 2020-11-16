# State Parser for Human Subjects Data

## Introduction

This repository contains Python implementation of **State Parser** for AI planning and plan recognition in the ToMCAT project.


<!-- /code_chunk_output -->


## How to run

The default setting uses localhost and port 1883. You can change those in config.json. Make sure mosquitto is running with the same host and port in the config.json file.

### 1. Run state_parser listener

~~~
python state_parser.py
~~~

### 2. Run elkless_replayer to publish data

~~~
python elkless_replayer.py <file name>
~~~

For example:

~~~
python elkless_replayer.py TrialMessages_CondBtwn-TriageSignal_CondWin-FalconEasy-StaticMap_Trial-61_Team-na_Member-32_Vers-1.metadata
~~~

The file states_json.json will be created containing all the state information under the same directory.

## State information

The primary keys in states_json.json are the action numbers. And the state also contains  
**time_stamp**: time stamp in the game;  
**action**: search_room, search_hallway, move, triage;  
**coordinates**: agent's current coordinates (x, z);  
**locations**: current location's id and name;  
**exited_locations**: exited locations;  
**effect in the search actions**: victims showing during the search;  
**effect in the triage actions**: SUCCESSFUL or UNSUCCESSFUL;  
**info**: the search and triage history.

## References

We referenced the codes from below repositories.

- [IHMCLocationMonitor](https://gitlab.asist.aptima.com/asist/testbed/-/blob/master/Agents/IHMCLocationMonitor/src/IHMCLocationMonitor.py)
- [elkless_replayer](https://github.com/ml4ai/tomcat/blob/master/tools/elkless_replayer)
