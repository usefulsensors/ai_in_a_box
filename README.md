# AI in a Box.

AI in a Box from [Useful Sensors](https://usefulsensors.com/) showcases
speech-based AI applications.  All models are on-device and run locally with
no internet connection so are private by design.  It ships with a bootable
microSD card containing Ubuntu server operating system and application code.

This repo provides open source code and setup instructions for microSD card.

We do not plan to maintain this repo and encourage interested parties to make
forks.

## Application modes.

AI in a Box has three speech driven modes with different display layouts.

| Mode      | Wake word(s)       | Notes                                  |
| --------- | ------------------ | -------------------------------------- |
| Caption   | "caption"          | Transcription.  English. USB keyboard. |
| Chatty    | "chatty"           | Answers questions.  LLM 4-bit weights. |
| Translate | "translate x to y" | e.g.: translate French to German.      |

Apply power with the USB-C connector on top.

Boots into caption mode for continuous transcription in English.

<img src="images/caption_mode.jpg" alt="caption mode on boot" width="500"/>

Chatty mode.

<img src="images/chatty_mode.jpg" alt="chatty mode" width="500"/>

Translate mode.

<img src="images/translate_mode.jpg" alt="translate mode" width="500"/>


## Connectors and buttons.

Power to the top USB-C connector boots AI in a Box.

<img src="images/power.jpg" alt="power" width="500"/>

 Optional HDMI display if connected before boot (some display resolutions may
 not work such as 800x480).

LAN connection is needed for
[full installation](#full-installation-from-baseline-image).

<img src="images/lan_usbc_keyboard.jpg" alt="lan_usbc" width="200"/>

Optional USB-C keyboard for caption mode transcription in English.

There are four buttons for navigating the pop-up menu:
* Up/Down keys toggle between the three [modes](#application-modes).
* Right key triggers a menu for volume and language selection.
  * use Up/Down to navigate and Right key to select.
  * use Left key to navigate back.

<img src="images/buttons.jpg" alt="buttons" width="200"/>
The volume selection (default `50`) is retained when rebooted.

# Installation.

For this project we use Ubuntu OS, specifically Jammy CLI b18 release from
[here](https://github.com/radxa-build/rock-5a/releases).  It is installed in
the microSD images described below.

The application is coded with Python scripts and runs Python3.10.

The microSD card images have username `ubuntu` and password `ubunturock` for
SSH.

## Quick setup.

Download this compressed image then extract and flash to a 16GB or higher
microSD card.
```console
cd
curl -L -O https:TODO
tar -xf TODO.tar.gz
```
Flash the image file `TODO` using BalenaEtcher or other.

Insert the flashed microSD card in AI in a Box after removing the four screws
securing the rear panel.  Connect USB-C power to boot AI in a Box into the
caption mode.  After around 60 seconds a prompt "Ready..." appears on the
display.

## Full installation from baseline image.

AI in a Box hardware has custom hardware for the display and audio and USB
keyboard.  For the full installation or experimentation we provide a baseline
microSD card image with the OS and needed overlays and configuration for the
custom hardware.  You will also need GitHub access.

This baseline image does not include our application code which is added during
this installation.  The preparation of this image is not documented in this
repo.  It was created on a Sandisk A1 16GB microSD card (SDSQUAR-O16G-GN6MN
with 15,931,539,456 Bytes storage).

Download this compressed image.
```console
cd
curl -L -O https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/ai_in_a_box_baseline_16gb_20240125.img.gz
```
Flash the compressed image file `ai_in_a_box_baseline_16GB_20240125.img.gz`
using BalenaEtcher or other method to a microSD card.  The image file is not
needed for the rest of this installation.

Insert the flashed microSD card into AI in a Box after removing the four screws
securing the rear panel.

### Boot and initial sanity checks.

Connect AI in a Box to LAN network and power-up using the provided USB-C
charger.  A prompt will appear on the display.

Identify the IP address with command `nmap -Pn -p22 --open 192.168.1.0/24` on a
Mac computer, or with a USB keyboard and `ip a` command.  Login through SSH
with `ubuntu` / `ubunturock`.

Optional: check custom hardware interfaces are available with these commands.

For input device check for
`<alsa_input.platform-uctronics-sound.stereo-fallback>`.
```console
pacmd list-sources | grep -e 'name:' -e 'index:' -e 'spec:'
```

For output device check for
`<alsa_output.platform-uctronics-sound.stereo-fallback>`.
```console
pacmd list-sinks | grep -e 'name:' -e 'index:' -e 'spec:'
```

For serial port needed for the USB keyboard feature check `/dev/ttyS6`.
```console
ls /dev/ttyS*
```

#### Support for external devices.
* Power supply of at least 20 W, see Rock 5A [power](https://radxa.com/products/rock5/5a#techspec) support.
* USB keyboard requires a USB-C cable that supports data.  It has been tested on MacBook TextEdit application.  Mac pop-up setup of the unknown keyboard can be cancelled.
* HDMI monitor requires reboot.  However some HDMI displays may not work (for example 800x480 display resolution).
* USB audio devices and the headset audio jack are not supported by our application.


### Software.

Setup GitHub access with SSH Key or other and clone this repo.
```console
git clone git@github.com:usefulsensors/ai_in_a_box.git --depth=1
```

Run installs including packages.
```console
cd
sudo apt update
sudo apt upgrade -y

sudo apt-get install -y pulseaudio
sudo apt-get install -y libasound-dev portaudio19-dev
sudo apt-get install -y libportaudio2 libportaudiocpp0
sudo apt install -y libegl-dev libegl1
sudo apt-get install -y python3-dev

sudo apt install -y python3.10 pip
sudo apt install -y python3-pygame

# Run pip install as root to allow booting into demo.
sudo python3 -m pip install -r ai_in_a_box/requirements.txt
```
During the above installs you may get prompted.
```bash
*** panfrost.conf.bak (Y/I/N/O/D/Z) [default=N] ?
```
If you see this prompt choose default `N`.

Check the memlock limits.
```console
sudo nano /etc/security/limits.conf

# Add these two lines before end, uncomment and save.
#*               soft    memlock         unlimited
#*               hard    memlock         unlimited
```
![/etc/security/limits.conf](images/memlock.jpg)

### Model download and extraction.

The five models used on AI in a Box are outlined [below](#model-details).

We download ~ 3 GB of archives over the internet and move to locations on the
card.  This step is best run inside a terminal multiplexer such as `tmux`
in case the SSH session disconnects.  Sudo password
`ubunturock` is needed during the first install.

```console
cd
ai_in_a_box/get_model_archives.sh
```
After download readme files and licence texts are in `models/` folder, model
files are in `downloaded/` folder.


### Permissions for scripts.

This script configures audio devices and is used in launcher script.
```console
cd
chmod +x ai_in_a_box/configure_devices.sh
```

This script is the launcher for AI in a Box boot.
```console
cd
chmod +x ai_in_a_box/run_chatty.sh
```

### Test run AI in a Box.

We can make a test run of AI in a Box.  This step is optional and you may
proceed to the [next section](#startup-service).

First reboot AI in a Box after above installation.
```console
sudo reboot
```
SSH back in to AI in a Box and start the launcher script.  AI in a Box takes
around 60 seconds to start caption mode `Ready...`.  Note it is run as
superuser.
```console
cd
sudo ai_in_a_box/run_chatty.sh
```
Ignore this error in the SSH session.
```bash
/usr/local/lib/python3.10/dist-packages/pygame_menu/sound.py:204: UserWarning: sound error: No such device.
  warn('sound error: ' + str(e))
```
The above error is superceded with this status.
```bash
audio input stream started successfully: True
```

If needed we can terminate the application in another SSH session with this
command.
```console
sudo pkill -9 python
```

### Startup service.

This section describes how to configure AI in a Box to boot to the application.

Create a startup service.  It will be run as superuser.
```console
sudo nano /etc/systemd/system/run-chatty-startup.service
```

Add this text and save.
```bash
[Unit]
Description=AI in a Box Startup Service

[Service]
ExecStart=/bin/sh -c '/home/ubuntu/ai_in_a_box/run_chatty.sh > /tmp/run_chatty_log.txt 2>&1'
WorkingDirectory=/home/ubuntu
StandardOutput=file:/tmp/run_chatty_log.txt
StandardError=file:/tmp/run_chatty_log.txt

[Install]
WantedBy=default.target

```

Reload the Systemd configuration and enable the service to auto start.
```console
sudo systemctl daemon-reload
sudo systemctl enable run-chatty-startup
```

AI in a Box does not need any LAN internet connection following this step.
```console
sudo reboot
```
AI in a Box will boot into [caption mode](#application-modes) `Ready...` after
about 60 seconds.  Speak to the box to see a transcription on the display.

The full installation is now complete.

You may now remove and reinsert the USB-C power to hard boot AI in a Box.

### Optional steps.

Optional: inspect the application log in an SSH session.
```console
watch -n 1 tail -n 20 /tmp/run_chatty_log.txt
```

Optional: remove the system startup configuration in an SSH session if booting
into AI in a Box application is not wanted.
```console
sudo systemctl disable run-chatty-startup
sudo rm /etc/systemd/system/run-chatty-startup.service
```

Optional: remove GitHub SSH key authentication and configuration.
```console
rm ~/.ssh/*
git config --global user.email ""
git config --global user.name ""
```

# Model details.

We provide copies of all models used in AI in a Box each with license, original
source URL and readme in compressed tarball archive files - details for
each archive file are provided in this table.

During the full installation above we used this
[script](/get_model_archives.sh) to automate the download and extraction onto
the AI in a Box microSD card.

| Name and source URL              | download URL | microSD location | Task                       |
| -------------------------------- | ------------ | ------------------- | --------------------------------------- |
| [useful-transformers_wheel.tar.gz](https://github.com/usefulsensors/useful-transformers) | [link](https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/useful-transformers_wheel.tar.gz) | python3.10 package  | Speech to text (S2T) in all modes       |
| [nllb-200-distilled-600M.tar.gz](https://huggingface.co/facebook/nllb-200-distilled-600M)   | [link](https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/nllb-200-distilled-600M.tar.gz) | downloaded/         | Language translation for translate mode |
| [orca-mini-3b.tar.gz](https://huggingface.co/TheBloke/orca_mini_3B-GGML)              | [link](https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/orca-mini-3b.tar.gz) | downloaded/         | LLM for chatty mode                     |
| [piper_tts_en_US.tar.gz](https://github.com/rhasspy/piper)           | [link](https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/piper_tts_en_US.tar.gz) | downloaded/         | Text to speech (TTS) for chatty mode  |
| [silero_vad.tar.gz](https://github.com/snakers4/silero-vad)                | [link](https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/silero_vad.tar.gz) | downloaded/         | Voice activity detection                |

The translate mode supports the fonts in [this](/fonts) folder.

# Contributors.
* Nat Jeffries (@njeffrie)
* Manjunath Kudlur (@keveman)
* William Meng (@wlmeng11)
* Guy Nicholson (@guynich)
* James Wang (@JamesUseful)
* Pete Warden (@petewarden)
* Ali Zartash (@aliz64)
