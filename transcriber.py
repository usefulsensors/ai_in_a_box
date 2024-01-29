from useful_transformers.whisper import WhisperModel
import numpy as np


class Transcriber():

    def __init__(self, model='tiny.en'):
        self.model = WhisperModel(model=model)

    def run(self, buff, task='transcribe', src_lang='en'):
        mel = self.model.mel_spectrogram(buff[np.newaxis])
        tokens = self.model.decode_no_timestamps(mel,
                                                 task=task,
                                                 src_lang=src_lang)
        return self.model.tokenizer.decode(tokens)
