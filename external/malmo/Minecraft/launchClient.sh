#!/bin/bash
set -u

# =============================================================================

# Set the TOMCAT environment variable, assuming that the directory structure
# mirrors that of the git repository.
TOMCAT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" >/dev/null 2>&1 && pwd)"
export TOMCAT
echo $TOMCAT
source "$TOMCAT"/tools/configuration_helpers


configure_session

# If the above fails, we do not get here.

# Start mosquitto message broker if it is not already running.
if [[ ! $(pgrep -l mosquitto | head -n1 | cut -d' ' -f2) == mosquitto ]]; then
    echo "The mosquitto message broker does not seem to be running, so we "\
         "will start it now."
    if [[ $OSTYPE == "darwin"* && $MACPORTS_FOUND -eq 1 ]]; then
        # If we get to this branch, we assume that MacPorts is not installed,
        # and the package manager is Homebrew. A Homebrew install of mosquitto
        # doesn't allow us to start mosquitto by just typing 'mosquitto' -
        # instead, we would have to do 'brew services start mosquitto'. To get
        # around the need to do this and just invoke the mosquitto executable
        # in the background, we give the full path to the mosquitto executable
        # under the Homebrew prefix.
        MOSQUITTO=$(brew --prefix)/sbin/mosquitto
    else
        MOSQUITTO=mosquitto
    fi

    "$MOSQUITTO" &> ${TOMCAT_TMP_DIR}/mosquitto.log &
fi

# On macOS, uuidgen produces uppercase UUIDS, so we pipe the output
# through 'tr' to get uniform behavior on macOS and Linux.
SESSION_UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
if [[ $? -ne 0 ]]; then exit 1; fi

# Creating an output directory for this session.
SESSION_OUTPUT_DIR="${TOMCAT}"/data/participant_data/"$SESSION_UUID"
mkdir -p "${SESSION_OUTPUT_DIR}"

SPEC_VERSION=$("$TOMCAT"/build/bin/getSpecVersion --spec "$TOMCAT"/docs/spec.yml)

# Generate metadata file for the session
"$TOMCAT"/tools/generate_session_metadata\
    "$SESSION_UUID"\
    "$PLAYER_ID"\
    "$TIME_LIMIT"\
    "$DIFFICULTY"\
    "$SPEC_VERSION" > "$SESSION_OUTPUT_DIR"/metadata.json

if [[ $? -ne 0 ]]; then exit 1; fi
export CURRENT_MISSION="1"
    echo " "
    echo "Running mission ${CURRENT_MISSION} in ${TOMCAT}."
    echo " "
    mission_log="$TOMCAT_TMP_DIR"/mission_"$CURRENT_MISSION".log
    export MISSION_OUTPUT_DIR="${SESSION_OUTPUT_DIR}"/mission_"$CURRENT_MISSION"
    mkdir -p "$MISSION_OUTPUT_DIR"
    messages="$MISSION_OUTPUT_DIR"/messages.txt

start_av_recording() {
    ffmpeg\
    -f ${FFMPEG_FMT_WEBCAM}\
    ${FRAMERATE_OPTION:-}\
    -i ${FFMPEG_INPUT_DEVICE_WEBCAM}\
    -r 30\
    "${MISSION_OUTPUT_DIR}"/webcam_video.mpg\
    &> ${TOMCAT_TMP_DIR}/ffmpeg_webcam_mission_"$CURRENT_MISSION".log &
    pid_webcam_recording=$!
    echo "Recording video of player's face using webcam. Process ID = ${pid_webcam_recording}"

    ffmpeg\
    -nostdin\
    -f ${FFMPEG_FMT_MICROPHONE}\
    -i ${FFMPEG_INPUT_DEVICE_MICROPHONE}\
    "${MISSION_OUTPUT_DIR}"/player_audio.wav\
    &> ${TOMCAT_TMP_DIR}/ffmpeg_microphone_mission_"$CURRENT_MISSION".log &
    pid_microphone_recording=$!

    if (( ENABLE_SYSTEM_AUDIO_RECORDING )); then
        if [[ $OSTYPE == linux-gnu ]]; then
            echo "Recording system audio for Linux."
            # For Linux system audio recording, we will use pacat.
            # We need to extract the alsa output monitor.
            export ALSA_OUTPUT_MONITOR=$(pacmd list-sources | \
                awk '/name:/ && /monitor/ {print $2 }'|sed 's/[<,>]//g')

            # Calling pacat command.
            pacat --record --file-format=wav -d ${ALSA_OUTPUT_MONITOR} \
            > "${MISSION_OUTPUT_DIR}"/system_audio.wav &
            pid_system_audio_recording=$!
        else
            echo "Recording system audio."
            ffmpeg\
            -nostdin\
            -f ${FFMPEG_FMT_SYSTEM_AUDIO}\
            -i ${FFMPEG_INPUT_DEVICE_SYSTEM_AUDIO}\
            "${MISSION_OUTPUT_DIR}"/system_audio.wav\
            &> "$TOMCAT_TMP_DIR"/system_audio_recording_mission_"$CURRENT_MISSION".log &
            pid_system_audio_recording=$!
        fi
    fi
    echo "Recording player audio using microphone. Process ID = ${pid_microphone_recording}"

    # Recording game screen.
    screen_video="${MISSION_OUTPUT_DIR}"/screen_video.mpg

    # On macOS, the -i option must be given before the -s option, and on Ubuntu
    # it's the other way around.
    if [[ "$OSTYPE"  == "darwin"* ]]; then
        ffmpeg -nostdin -f ${FFMPEG_FMT_SCREEN_CAPTURE}\
        -i ${FFMPEG_INPUT_DEVICE_SCREEN_CAPTURE}\
        -s $SCREEN_DIMENSIONS\
        "$screen_video" &> "$TOMCAT_TMP_DIR"/screen_video_recording_mission_"$CURRENT_MISSION".log &
        pid_screen_recording=$!
    else
        ffmpeg -nostdin -f ${FFMPEG_FMT_SCREEN_CAPTURE}\
        -s $SCREEN_DIMENSIONS\
        -i ${FFMPEG_INPUT_DEVICE_SCREEN_CAPTURE}\
        "$screen_video" &> "$TOMCAT_TMP_DIR"/screen_video_recording_mission_"$CURRENT_MISSION".log &
        pid_screen_recording=$!
    fi
    echo "Recording player's screen. Process ID = ${pid_screen_recording}"
}


# run from the script directory
cd "$(dirname "$0")"

replaceable=0
port=0
scorepolicy=0
env=0

while [ $# -gt 0 ]
do
    case "$1" in
        -replaceable) replaceable=1;;
        -port) port="$2"; shift;;
        -scorepolicy) scorepolicy="$2"; shift;;
        -env) env=1;;
        *) echo >&2 \
            "usage: $0 [-replaceable] [-port 10000] [-scorepolicy 0123] [-env]"
            exit 1;;
    esac
    shift
done
  
if ! [[ $port =~ ^-?[0-9]+$ ]]; then
    echo "Port value should be numeric"
    exit 1
fi

if [ \( $port -lt 0 \) -o \( $port -gt 65535 \) ]; then
    echo "Port value out of range 0-65535"
    exit 1
fi

if ! [[ $scorepolicy =~ ^-?[0-9]+$ ]]; then
    echo "Score policy should be numeric"
    exit 1
fi

# Now write the configuration file
if [ ! -d "run/config" ]; then
  mkdir run/config
fi
echo "# Configuration file
# Autogenerated from command-line options

malmoports {
  I:portOverride=$port
}
malmoscore {
  I:policy=$scorepolicy
}
" > run/config/malmomodCLIENT.cfg

if [ $replaceable -gt 0 ]; then
    echo "runtype {
  B:replaceable=true
}
" >> run/config/malmomodCLIENT.cfg
fi

if [ $env -gt 0 ]; then
    echo "envtype {
  B:env=true
}
" >> run/config/malmomodCLIENT.cfg
fi

start_something() {
  echo "receiving recording starting signal..."
mosquitto &
recording_start=$(mosquitto_sub -t recording_start -C 1 &)
while :
      echo "i am here"
do
    if [ $recording_start ];
    then
      echo "start recording now..."
      start_av_recording
      break
    fi
done
}
# Finally we can launch the Mod, which will load the config file

start_something &
while
    ./gradlew setupDecompWorkspace
    ./gradlew build
    ./gradlew runClient
    [ $replaceable -gt 0 ]
do :; done
kill_av_recording_and_mosquitto_sub() {
    echo "Cleaning up ffmpeg/pacat and mosquitto_sub processes."

    if (( ENABLE_FFMPEG )); then
        pkill ffmpeg
        if [[ $ENABLE_SYSTEM_AUDIO_RECORDING -eq 1 &&  $OSTYPE == linux-gnu ]]; then
            pkill pacat
        fi
    fi

    # Kill any remaining mosquitto, mosquitto_sub, and mosquitto_pub processes
    pkill mosquitto_sub
}

kill_av_recording_and_mosquitto_sub




