#!/usr/bin/env python3
"""
LLM Speaker class that can evaluate a prompt and start speaking as the response
is generated.
"""
import os
import time
from threading import Thread
from typing import List
from printing import printf, printc

import numpy as np

import llama_cpp
"""Atrribution: uses orca3b-4bit model with citations in references.bib.
https://huggingface.co/TheBloke/orca_mini_3B-GGML
"""
model_param_dict = {
    "orca3b-4bit"  : {
    "file": "orca-mini-3b.ggmlv3.q4_0.bin",
    "ctx" : 2048,
    "eps" : 1e-6,
    "rfb" : 10000,
    "pfx" : "### User: ",
    "sfx" : "### Response:",
    "init": "### System: You are an assistant that talks in a human-like "\
            "conversation style and provides useful, very brief, and concise "\
            "answers. Do not say what the user has said before."
    },
}


class LLMSpeaker(object):

    def __init__(self, model_str="orca3b-4bit"):
        assert model_str in model_param_dict, f"unsupported model {model_str}"
        model_params = model_param_dict[model_str]
        filename = model_params["file"]
        self.n_ctx = model_params["ctx"]
        self.model_str = model_str
        self.prefix = model_params["pfx"]
        self.suffix = model_params["sfx"]
        self.init_prompt = model_params["init"]

        self.n_tokens_processed = 0
        self.total_tokens_processed = 0

        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logfile = f'{dir_path}/llm.log'
        self.tts_logfile = f'{dir_path}/llm_raw.log'

        self.llm_producer_callback = None
        self.response = ''

        # 1) using llama_cpp (python bindings for GGML basically)
        self.llm = llama_cpp.Llama(
            model_path=f"{dir_path}/downloaded/{filename}",
            n_ctx=self.n_ctx,
            rms_norm_eps=model_params["eps"],
            rope_freq_base=model_params["rfb"],
            n_batch=32,
            n_threads=4,
            use_mlock=True,
            use_mmap=False)

    def save_logs(self, sentence):
        if len(sentence.split()) < 1 or len(sentence) == 0:
            printf(self.logfile, f"\\", end="", flush=True)
            return

        if sentence[0] == ' ':
            sentence = sentence[1:]
        printf(self.tts_logfile, f"{sentence}", flush=True)
        printf(self.logfile, f"|", end="", flush=True)

    def set_llm_producer_callback(self, callback):
        self.llm_producer_callback = callback

    def token_mask_fn(self, toks: List[int],
                      logits: List[float]) -> List[float]:
        if self.model_str != "orca3b-4bit":
            print(
                f"WARNING: running token mask for non-orca model {self.model_str}"
            )

        # We want to avoid responses like:
        #
        # Response 13166         # Response 13166
        #: 31871                 #: 31871
        # I 312                  # As 717
        #' 31876                 # an 363
        #m 31836                 # artificial 11139
        # sorry 10157            # intelligence 6216
        # but 504                # program 1221
        # as 362
        # an 363
        # AI 7421
        # language 3067
        # model 2228
        #, 31844

        # sorry, AI, language, model
        filter_tokens = [10157, 7421, 3067, 2228]

        # `:`   -> [As]
        n2_gram_block_map = {
            31871: [717],
        }

        for tok in n2_gram_block_map.get(toks[-1], []) + filter_tokens:
            logits[tok] = -float("inf")

        # print(self.llm.detokenize([toks[-1]]).decode("utf-8", errors="ignore"),
        #       toks[-1])
        return logits

    def reset_state_on_nth_token(self, limit):
        if self.n_tokens_processed > limit:
            self.llm.reset()
            self.n_tokens_processed = 0

    def llm_producer(self, prompt_str):
        self.response_done = False
        ptokens = self.llm.tokenize(bytes(prompt_str, "utf-8"))
        self.n_tokens_processed += len(ptokens)
        self.total_tokens_processed += len(ptokens)

        # 256 tokens should be a reasonable buffer to allow all but the longest
        # responses without resetting the LLM.
        self.reset_state_on_nth_token(self.n_ctx - 256)

        resp_gen = self.llm.generate(
            ptokens,
            top_k=40,
            top_p=0.95,
            temp=0.25,
            repeat_penalty=1.1,
            reset=False,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            tfs_z=1.0,
            mirostat_mode=0,
            mirostat_tau=5.0,
            mirostat_eta=0.1,
            logits_processor=llama_cpp.LogitsProcessorList([self.token_mask_fn
                                                           ]))

        sentence = ""
        first = False
        for tok in resp_gen:
            self.n_tokens_processed += 1
            self.total_tokens_processed += 1

            # This is here just in case a very long response is generated when the llm
            # nears capacity. This should basically never happen because the token
            # limit is conservative.
            self.reset_state_on_nth_token(self.n_ctx)

            if not first:
                printf(self.logfile, f"{prompt_str}", end="", flush=True)
                first = True

            if tok == self.llm.token_eos():
                self.save_logs(sentence)
                sentence = ""
                printf(self.logfile, "\n" + "_" * 70 + "\n")
                break

            word = self.llm.detokenize([tok]).decode("utf-8", errors="ignore")
            if self.llm_producer_callback is not None:
                self.llm_producer_callback(word)
            sentence += word
            self.response += word
            printf(self.logfile, word, end="", flush=True)

            last_word = sentence.split()[-1] if len(
                sentence.split()) > 0 else None
            if last_word in {'and', 'or', 'however', 'as'}:
                self.save_logs(sentence[:-len(last_word)])
                sentence = f" {last_word}"
            if word in {".", "?", "!", ":", ";", " -", ",", "(", '"'} or \
               tok in {self.llm.token_eos(), self.llm.token_nl()}:
                self.save_logs(sentence)
                sentence = ""
        self.response_done = True

    def get_response(self):
        response = None if self.response_done and self.response == '' else self.response
        self.response = ''
        return response

    def start_first(self):
        init_prompt = \
            f"{self.init_prompt}\n\n"\
            f"{self.prefix}Hello!\n"\
            f"{self.suffix}"
        self._start(init_prompt)

    def start(self, user_prompt):
        user_prompt = f"{self.prefix}{user_prompt}\n"\
                      f"{self.suffix}"
        self._start(user_prompt)

    def _start(self, prompt_str):
        self.llm_th = Thread(target=self.llm_producer,
                             args=(prompt_str,),
                             daemon=False)
        printc(
            "yellow", "starting response pipeline ("
            f"seen ctx: {self.n_tokens_processed})")
        self.llm_th.start()

    def wait(self):
        # 1) we must have finished producing all the words in the sequence
        self.llm_th.join()

    def switch_to_chat_mode(self, chat_mode):
        if chat_mode:
            printf(self.tts_logfile, "switching to chat mode", flush=True)
        else:
            printf(self.tts_logfile, "switching to caption mode", flush=True)
