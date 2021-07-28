# Replayer 
### Prerequisites
* ffmpeg: http://ffmpeg.org/
* python: https://www.python.org/
* Boost Library: https://www.boost.org/ 

###  Trial data structuring 
The trial_directory option represents a directory containing the .wav and .metadata files for a given trial. If you are using the batch script, you should put all of your trial directories into the directory named "trials" located in the build directory. 

### Build the program
```
mkdir build && cd build
cmake ..
make
```
### Running the program (individual)
```
./replayer --trial_directory PATH_TO_TRIAL_DIRECTORY --mqtt_host localhost --mqtt_port 1883
```
The replayer outputs messages to the console by default. To capture those messages, you can redirect the output to a file:

```
./replayer --trial_directory PATH_TO_TRIAL_DIRECTORY --mqtt_host localhost --mqtt_port 1883 > PATH_TO_FILE
``` 

### Running the program (multiple)
To run multiple trials back to back, you can use the run_batch script. The script will run the replayer for all of the trials in the trials directory.
```
bash tools/run_batch.sh
```
You may need to modify this file before you run it depending on the command line options you use.




