#!/usr/bin/bash -xe
# Courtesy of https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

ulimit -l 2000000
ulimit -Sn 8192

sudo pulseaudio --start

${SCRIPT_DIR}/configure_devices.sh

rm -f /tmp/audio_input_running.bool
rm -f ${SCRIPT_DIR}/llm_raw.log ${SCRIPT_DIR}/llm.log
touch ${SCRIPT_DIR}/llm_raw.log ${SCRIPT_DIR}/llm.log
sudo taskset -c 0-3 python3 ${SCRIPT_DIR}/tts.py &
sudo taskset -c 4-7 python3 ${SCRIPT_DIR}/main.py orca3b-4bit

kill %1
