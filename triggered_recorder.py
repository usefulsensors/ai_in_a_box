#!/usr/bin/env python3
"""
Triggered Recorder that records audio while keystroke is held pressed.

"""
import copy
import queue
import sys
import time
from threading import Event

import numpy as np
import sounddevice as sd

from input_chunk_filter import ChunkHPFilter
from transcriber import Transcriber

WHISPER_FRAME_RATE = 16000
WHISPER_DURARION = 30


class VadTriggeredRecorder(object):

    def __init__(self):
        self.recording_sta = Event()
        self.recording_end = Event()
        self.max_duration = WHISPER_DURARION
        self.rate = WHISPER_FRAME_RATE
        self.chunk_sz = 1600  # 100ms @ 16KHz
        self.channels = 1
        self.buff_idx = 0
        self.in_stream = None
        self.sta_time = None
        self.end_time = None

        # audio buffer in int16
        self.buff = np.zeros((self.max_duration * self.rate), dtype=np.int16)

        self.initialize_audio_devices()
        self.q = queue.Queue()
        self.no_vad_count = 0
        self.hp_filter = ChunkHPFilter()
        self.prompt_end_delay = 0.8  #seconds

        self.upper_thres = -35  # start when VAD goes above this level
        self.lower_thres = -42  # end when VAD falls below this
        self.n_vad_trigger = 3  # num. consecutive +ve activity blocks needed
        self.n_vad_lookback = 3  # if triggered, num. blocks to include as well
        self._reset_potential_prefix_state()

    def _reset_potential_prefix_state(self):
        self.potential_prefix = [np.zeros((self.chunk_sz,), np.int16) for _ in \
            range(self.n_vad_lookback + self.n_vad_trigger)]
        self.potential_prefix_vad = [-float("inf") for _ in \
            range(self.n_vad_lookback + self.n_vad_trigger)]

    def get_recording(self, dtype="float32"):
        if dtype == "float32":
            return self.buff.astype(np.float32) / (2**15)
        else:
            assert False, f"dtype {dtype} not implemented"

    def initialize_audio_devices(self):
        sd.default.channels = self.channels, self.channels
        sd.default.dtype = 'int16', 'int16'
        sd.default.samplerate = self.rate, self.rate

        # TODO(guy): select device.
        self.in_stream = sd.InputStream(
            samplerate=self.rate,
            blocksize=self.chunk_sz,
            # device=sd.default.device[0],
            channels=self.channels,
            callback=self._audio_callback)

    def _get_vad(self, indata):
        arr = np.array(copy.copy(indata)).astype(np.float32) / (2**15 - 1)
        arr = self.hp_filter.run(arr)
        val = 20. * np.log10(np.mean(arr**2)**0.5)
        return val

    def _has_continuous_vad(self):
        return all([vad > self.upper_thres for vad in \
            self.potential_prefix_vad[-self.n_vad_trigger:]])

    def _audio_callback(self, indata, frames, time_info, status):
        self.q.put(np.frombuffer(indata, dtype=np.int16).flatten())

    def handle_incoming_audio(self):
        indata = self.q.get()
        curr_vad = self._get_vad(indata)
        self.potential_prefix = self.potential_prefix[1:] + [indata]
        self.potential_prefix_vad = self.potential_prefix_vad[1:] + [curr_vad]

        # When voice activity is detected, reset count-down to "end of phrase"
        if curr_vad > self.upper_thres:
            self.no_vad_count = 0

        # Begin recording if new voice activity has been detected continuously
        if not self.recording_sta.is_set() and self._has_continuous_vad():
            self.sta_time = time.time()
            self.recording_sta.set()
            self.buff_idx = 0
            self.buff = np.zeros((self.max_duration * self.rate),
                                 dtype=np.int16)
            # add all the chunks in the potential prefix except for the last one
            # the last chunk will be handled by the code below i.e. the general
            # case when recording is occurring
            for i in range(self.n_vad_lookback + self.n_vad_trigger - 1):
                self.buff[self.buff_idx:self.buff_idx + self.chunk_sz] = \
                    self.potential_prefix[i]
                self.buff_idx += self.chunk_sz

            print(f'begin recording')

        # Count down to end of voice recording when no voice detected.
        if self.recording_sta.is_set() and curr_vad < self.lower_thres:
            self.no_vad_count += 1
            if self.no_vad_count > self.prompt_end_delay * 10:
                self.recording_end.set()
                self.end_time = time.time()
                self._reset_potential_prefix_state()
                self.hp_filter.reset()
                self.in_stream.stop()
                self.q.empty()
                print('end recording')
                return

        if not self.recording_sta.is_set():
            return

        assert self.recording_sta.is_set()
        assert not self.recording_end.is_set()
        self.buff[self.buff_idx:self.buff_idx + self.chunk_sz] = indata
        self.buff_idx += self.chunk_sz

        if self.buff_idx == self.max_duration * self.rate:
            printc("magenta",
                   f"At max duration ({self.max_duration}s)! Exiting...")
            self.recording_end.set()
            self.in_stream.stop()
            self.end_time = time.time()

    def reset(self):
        self.recording_sta.clear()
        self.recording_end.clear()
        if self.in_stream.active:
            self.in_stream.stop()

    def get_audio_if_ready(self):
        if not self.in_stream.active:
            self.recording_sta.clear()
            self.recording_end.clear()
            self.in_stream.start()

        if not self.recording_end.is_set():
            self.handle_incoming_audio()
            return None
        else:
            self.in_stream.stop()
            recorded_time = self.buff_idx / self.rate
            printc(
                "magenta", f"recorded {recorded_time}s of audio in "
                f"{self.end_time - self.sta_time:.3f}s")
            return self.get_recording()


def main():
    t = Transcriber()

    r = VadTriggeredRecorder()
    while True:
        wav = None
        while wav is None:
            wav = r.get_audio_if_ready()

        print("playing recorded audio")
        # TODO: this play method does not always work properly i.e. it plays
        # with cracked audio, the `sf.write` method seems to work well though
        sd.play(wav[0:r.buff_idx], r.rate)
        #sf.write("a.wav", wav[0:r.buff_idx], r.rate)

        print("Transcription:\n", t.run(wav), "\n")
        sd.wait()


if __name__ == "__main__":
    sys.exit(main())
