import os
import queue
import subprocess
import time

import numpy as np
import sounddevice as sd
import torch

from input_chunk_filter import ChunkHPFilter


class Recorder(object):

    def __init__(self, tts_signal=True):
        self.max_duration = 10  # seconds
        self.rate = 16000
        self.buff_size = int(30 * self.rate)  # Record a 30-second buffer.
        self.chunk_sz = self.rate // 10  # 100ms @ 16KHz
        self.channels = 1
        self.buff_idx = 0
        self.vad_chunk_idx = 0
        self.recording_voice = False

        # audio buffer in int16
        self.buff = np.zeros((self.buff_size), dtype=np.float32)
        self.vad_chunks = np.zeros((int(self.buff_size / self.chunk_sz)),
                                   dtype=np.float32)

        self.q = queue.Queue()
        self.hp_filter = ChunkHPFilter(fc=50)
        torch.set_num_threads(1)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.vad, _ = torch.hub.load(
            repo_or_dir=(f"{dir_path}/downloaded/snakers4_silero-vad_master"),
            source='local',
            model='silero_vad',
            force_reload=False,
            onnx=True)
        sd.default.channels = self.channels, self.channels
        sd.default.dtype = 'int32', 'int32'
        sd.default.samplerate = self.rate, self.rate

        self.in_stream = sd.InputStream(samplerate=self.rate,
                                        blocksize=self.chunk_sz,
                                        channels=self.channels,
                                        callback=self._audio_callback)
        self.in_stream.start()

        # Signal to tts that audio output can start.  This is required for
        # AI in a Box because audio input must be configured before audio output
        # with the current onboard audio drivers.  Not required for main().
        if tts_signal:
            with open('/tmp/audio_input_running.bool', 'w') as fp:
                pass
            print(
                f'audio input stream started successfully: {self.in_stream.active}'
            )

    def _audio_callback(self, indata, frames, time_info, status):
        self.q.put(np.frombuffer(indata, dtype=np.int32).flatten())

    def preprocess_audio(self, audio):
        # 20-bits of audio are copied into lowest 16-bits, meaning we should
        # keep 4 extra bits.
        x = audio.astype(dtype=np.float32)
        x = self.hp_filter.run(x) / (2**27)
        x = x.astype(np.float32)
        return x, self.vad(torch.from_numpy(x), 16000).item()

    def process_audio_chunk(self):
        audio, vad = self.preprocess_audio(self.q.get())
        if self.buff_idx < self.buff_size:
            self.buff[self.buff_idx:self.buff_idx + self.chunk_sz] = audio
            self.vad_chunks[self.vad_chunk_idx] = vad
            self.buff_idx += self.chunk_sz
            self.vad_chunk_idx += 1
        else:
            self.buff[:-self.chunk_sz] = self.buff[self.chunk_sz:]
            self.buff[-self.chunk_sz:] = audio
            self.vad_chunks[:-1] = self.vad_chunks[1:]
            self.vad_chunks[-1] = vad

    def record_voice(self):
        if not self.recording_voice:
            self.recording_voice = True
            self.reset()

        for _ in range(self.q.qsize()):
            self.process_audio_chunk()

        preamble_chunks = 3  # 300ms of extra audio.
        vad_inds = np.nonzero(self.vad_chunks > 0.9)[0]
        if len(vad_inds) == 0:
            return None
        first_vad_sample = max(0, vad_inds[0] - preamble_chunks)

        last_idx = self.vad_chunk_idx
        for i in range(len(vad_inds) - 1, 0, -1):
            if last_idx - vad_inds[i] > 10:
                src_start_idx = first_vad_sample * self.chunk_sz
                src_end_idx = (vad_inds[i] + 10) * self.chunk_sz
                samples_to_copy = src_end_idx - src_start_idx
                audio_buff = np.zeros((self.buff_size), dtype=np.float32)
                audio_buff[:samples_to_copy] = self.buff[
                    src_start_idx:src_end_idx]
                self.buff_idx = 0
                self.vad_chunk_idx = 0
                self.buff.fill(0.0)
                self.vad_chunks.fill(0.0)
                self.recording_voice = False
                return audio_buff
            last_idx = vad_inds[i]

    def get_audio(self):
        for _ in range(self.q.qsize()):
            self.process_audio_chunk()

        end_idx = self.vad_chunk_idx
        audio_start_idx = max(
            0, end_idx - self.max_duration * 10)  # Return ten seconds buffer.
        vad_start_idx = max(0, end_idx - 3 * 10)  # 3 seconds of voice activity.
        last_ten_seconds = self.buff[audio_start_idx * self.chunk_sz:end_idx *
                                     self.chunk_sz]
        # Return samples padded to native whisper length.
        x = np.pad(last_ten_seconds, (0, (30 - self.max_duration) * self.rate),
                   'constant')
        chunks_with_vad = np.sum(self.vad_chunks[vad_start_idx:end_idx] > 0.5)
        return x, chunks_with_vad

    def reset(self):
        for _ in range(self.q.qsize()):
            self.process_audio_chunk()
        self.buff_idx = 0
        self.buff.fill(0.0)
        self.vad_chunk_idx = 0
        self.vad_chunks.fill(0.0)
        self.hp_filter.reset()
        self.vad.reset_states()


from transcriber import Transcriber
import time
if __name__ == '__main__':
    """Example call:  `taskset -c 4-7 python3 recorder.py`."""
    recorder = Recorder(tts_signal=False)
    recorder.reset()

    t = Transcriber()
    while True:
        clip, vad = recorder.get_audio()
        print(f'vad {vad}')

        if (vad > 0):
            print("Transcription:\n", t.run(clip), "\n")
        else:
            time.sleep(1)
