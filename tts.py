import argparse
import subprocess
import io
import os
import queue
import sys

import numpy as np
import sounddevice as sd
import piper
import fasteners
import time
from volume_file import get_current_volume
from piper.download import find_voice

dir_path = os.path.dirname(os.path.realpath(__file__))
LLM_FILE = f'{dir_path}/llm_raw.log'
TTS_LOCKFILE = f'{dir_path}/tts.lock'
tts_sr = 16000
blocksize = 1600
q = queue.Queue()


def callback(outdata, frames, time, status):
    if status:
        print(f'tts: {status}')

    if q.empty():
        outdata.fill(0)
    else:
        outdata[:] = q.get_nowait()


def set_tts_rate_based_on_queue_len(size, len_scale=1.2):
    return min(0.9, len_scale - float(size) / 800)


def tts_thread(len_scale: float, log: bool = True):
    m, c = find_voice("en_US-lessac-low", [f"{dir_path}/downloaded/"])
    tts = piper.PiperVoice.load(m, config_path=c, use_cuda=False)
    tts_config = {
        "speaker_id": None,
        "length_scale": len_scale,
        "noise_scale": None,
        "noise_w": None,
        "sentence_silence": 0.010,
    }

    # Wait for audio input to start. This is required because audio input must be configured before audio output with the current onboard audio drivers.
    while not os.path.exists('/tmp/audio_input_running.bool'):
        time.sleep(1)
    aud_s = sd.OutputStream(samplerate=tts_sr,
                            blocksize=blocksize,
                            channels=1,
                            dtype="int16",
                            callback=callback)
    aud_s.start()
    print(f'audio output stream started successfully: {aud_s.active}')

    tts_lock = fasteners.InterProcessLock(TTS_LOCKFILE)
    with open(LLM_FILE, 'r') as f:
        linebuffer = ''
        while True:
            # Release lock if no TTS is being played.
            if q.empty():
                try:
                    tts_lock.release()
                except:
                    pass
            c = f.read(1)
            volume = get_current_volume()
            if c and volume != 0:
                # Acquire lock while TTS is being played.
                tts_lock.acquire(blocking=False)
                if c == '\n':
                    # convert linebuffer to a wav and pad to a multiple of blocksize
                    tts_config[
                        'length_scale'] = set_tts_rate_based_on_queue_len(
                            q.qsize(), len_scale=len_scale)
                    s = io.BytesIO()
                    raw_audio_stream = tts.synthesize_stream_raw(
                        linebuffer, **tts_config)
                    print(f'tts playing {linebuffer}')
                    print(
                        f'audio output stream running successfully: {aud_s.active}'
                    )
                    for chunk in raw_audio_stream:
                        s.write(chunk)
                    wav = np.frombuffer(s.getvalue(), dtype=np.int16)
                    volume_factor = volume / 100
                    wav = wav * volume_factor
                    nframes = wav.shape[0]
                    # split the wav into chunks and put them in the q
                    for i in range(nframes // blocksize):
                        frames = wav[i * blocksize:(i + 1) * blocksize,
                                     np.newaxis]
                        q.put(frames)
                    linebuffer = ''

                    if log:
                        max_value = np.max(np.abs(wav / np.iinfo(np.int16).max))
                        if max_value > 0.9:
                            print(f'tts: high wav value {max_value:0.1f}')
                else:
                    linebuffer += c

    aud_s.stop()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-l',
        '--length_scale',
        type=float,
        default=1.2,
        help=
        ('Scales word rate, hence length of tts speech.  A lower value has '
         'faster word rate. Does not affect length when speech queue is empty '
         '(default: %(default)s).'))
    parser.add_argument('--log',
                        default=True,
                        action=argparse.BooleanOptionalAction,
                        help='Whether to log to stdout')
    args = parser.parse_args()

    tts_thread(len_scale=args.length_scale, log=args.log)


if __name__ == "__main__":
    main()
