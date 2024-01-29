#!/usr/bin/bash -xe
# Downloads model compressed archives, extracts and moves to card locations.

# Courtesy of https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Licences and readme text files are saved here.
MODEL_FOLDER="${SCRIPT_DIR}/models"
# Models go here.
DOWNLOADED_FOLDER="${SCRIPT_DIR}/downloaded"

echo "SUDO authentication needed after first model download."

cd
mkdir -p $DOWNLOADED_FOLDER
mkdir -p $MODEL_FOLDER

cd $MODEL_FOLDER

DEST_FOLDER="useful-transformers_wheel/"
mkdir -p $DEST_FOLDER
cd $DEST_FOLDER
curl -L -O https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/useful-transformers_wheel.tar.gz
tar -xf *.tar.gz
echo "Archive extraction succeeded in ${MODEL_FOLDER}/${DEST_FOLDER}."
sudo python3 -m pip install ${MODEL_FOLDER}/${DEST_FOLDER}useful_transformers-0.1-cp310-cp310-linux_aarch64.whl
rm *.tar.gz
rm *.whl

cd $MODEL_FOLDER

DEST_FOLDER="nllb-200-distilled-600M/"
mkdir -p $DEST_FOLDER
cd $DEST_FOLDER
curl -L -O https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/nllb-200-distilled-600M.tar.gz
tar -xf *.tar.gz
echo "Archive extraction succeeded in ${MODEL_FOLDER}/${DEST_FOLDER}."
mv $DEST_FOLDER $DOWNLOADED_FOLDER
rm *.tar.gz

cd $MODEL_FOLDER

DEST_FOLDER="piper_tts_en_US/"
mkdir -p $DEST_FOLDER
cd $DEST_FOLDER
curl -L -O https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/piper_tts_en_US.tar.gz
tar -xf *.tar.gz
echo "Archive extraction succeeded in ${MODEL_FOLDER}/${DEST_FOLDER}."
mv en_US-lessac-low* $DOWNLOADED_FOLDER
rm *.tar.gz

cd $MODEL_FOLDER

DEST_FOLDER="orca-mini-3b/"
mkdir -p $DEST_FOLDER
cd $DEST_FOLDER
curl -L -O https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/orca-mini-3b.tar.gz
tar -xf *.tar.gz
echo "Archive extraction succeeded in ${MODEL_FOLDER}/${DEST_FOLDER}."
mv orca-mini-3b.ggmlv3.q4_0.bin $DOWNLOADED_FOLDER
rm *.tar.gz

cd $MODEL_FOLDER

DEST_FOLDER="silero_vad/"
mkdir -p $DEST_FOLDER
cd $DEST_FOLDER
curl -L -O https://storage.googleapis.com/download.usefulsensors.com/ai_in_a_box/silero_vad.tar.gz
tar -xf *.tar.gz
echo "Archive extraction succeeded in ${MODEL_FOLDER}/${DEST_FOLDER}."
mv snakers4_silero-vad_master/ $DOWNLOADED_FOLDER
rm *.tar.gz

exit 0
