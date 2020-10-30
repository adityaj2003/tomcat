#!/bin/bash
set -u

# =============================================================================

# Set the TOMCAT environment variable, assuming that the directory structure
# mirrors that of the git repository.
TOMCAT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../" >/dev/null 2>&1 && pwd)"
export TOMCAT
source "$TOMCAT"/tools/recording_helper

start_mosquitto

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

session_cleanup() {
    kill_av_recording_and_mosquitto_sub
    cleanup_status=0
    if [[ ${RECYCLE_MINECRAFT} -lt 2 ]]; then
        if ! "${TOMCAT}/tools/kill_minecraft"; then
            echo "Failed to kill Minecraft."
            exit 1
        fi
    fi

    if [[ $ENABLE_SYSTEM_AUDIO_RECORDING -eq 1 && $CI -eq 0 && "$OSTYPE"  == "darwin"* ]]; then
        # Switching the audio output from the multi-output device to the
        # built-in output.
        if ! SwitchAudioSource -s "$ORIGINAL_OUTPUT_DEVICE"; then
            echo " "
            echo "Failed to switch audio output device back to what it was"\
                "before run_session (${ORIGINAL_OUTPUT_DEVICE})."
            echo " "
            exit 1
        fi
    fi
}

start_recording() {
    echo "Waiting for recording starting signal"
    echo "Once the signal is received"\
         "all clients will start recording at the same time."
    recording_start=$(mosquitto_sub -t recording_start -C 1 &)
    while :
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


start_recording &
while
    ./gradlew setupDecompWorkspace
    ./gradlew build
    ./gradlew runClient
    [ $replaceable -gt 0 ]
do :; done

kill_av_recording_and_mosquitto_sub
session_cleanup




