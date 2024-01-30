#!/bin/bash
#
# See README.md:  chmod +x ./configure_devices.sh

# USB Audio Device support is experimental.
# Find the first USB devices (if they exist).
USB_SOURCE_STR=$(sudo pactl list short sources | grep -i -m 1 "alsa_input.usb" | awk '{print $2}')
USB_SINK_STR=$(sudo pactl list short sinks | grep -i -m 1 "alsa_output.usb" | awk '{print $2}')

if [ ! -z "$USB_SOURCE_STR" ]; then
   echo "Found USB source:  $USB_SOURCE_STR"
   pactl set-default-source $USB_SOURCE_STR
else
   echo "Did not find USB source"
fi

if [ ! -z "$USB_SINK_STR" ]; then
    echo "Found USB sink:   $USB_SINK_STR"
    pactl set-default-sink $USB_SINK_STR
else
    echo "Did not find USB sink"
fi

# Get default source name string and index number.  Set volume for uctronics.
DEFAULT_SOURCE=$(pactl get-default-source)
DEFAULT_SOURCE_INDEX=$(pactl list short sources | grep "$DEFAULT_SOURCE" | awk '{print $1}')
if [[ $DEFAULT_SOURCE == *"alsa_input.platform-uctronics-sound"* ]]; then
  pactl set-source-volume $DEFAULT_SOURCE_INDEX 0xFFFF
else
  # Set unknown device volume low to offset AI in a Box script correction for
  # AI in a Box hardware (`recorder.py` preprocess_audio() method keeps 4-bits).
  # This combined may cause loss of low-bits when source is 16-bit (?).
  pactl set-source-volume $DEFAULT_SOURCE_INDEX 0x6000
fi
DEFAULT_SOURCE_VOLUME=$(pactl get-source-volume $DEFAULT_SOURCE | grep "Volume: ")

# Get default sink name string and index number.  Set volume for uctronics.
DEFAULT_SINK=$(pactl get-default-sink)
DEFAULT_SINK_INDEX=$(pactl list short sinks | grep "$DEFAULT_SINK"  | awk '{print $1}')
if [[ $DEFAULT_SINK == *"alsa_output.platform-uctronics-sound"* ]]; then
  # Set ALSA mixer gain for AI in a Box speaker.
  amixer -c 2 sset DAC 100%
  pactl set-sink-volume $DEFAULT_SINK_INDEX 0xFFFF
else
  # Set unknown device volume.
  pactl set-sink-volume $DEFAULT_SINK_INDEX 0xE000
fi
DEFAULT_SINK_VOLUME=$(pactl get-sink-volume $DEFAULT_SINK | grep "Volume: ")

echo "Default Source:  $DEFAULT_SOURCE_INDEX  $DEFAULT_SOURCE"
echo $DEFAULT_SOURCE_VOLUME
echo "Default Sink:    $DEFAULT_SINK_INDEX  $DEFAULT_SINK"
echo $DEFAULT_SINK_VOLUME
