#!/usr/bin/env python3
"""
Chatty - a talking robot
"""

import sys
import time
import fasteners

from buttons import ButtonHandler
from fontfile import lang_to_font
from llm_speaker import LLMSpeaker
from post_processing import combine_words
from prediction_filters import PredictionFilters
from printing import printc, printf
from recorder import Recorder
from render import BaseDisplay
from render import MainMenu
from render import SingleScreenRenderer
from render import SplitScreenRenderer
from state_machine import AIBoxState
from state_machine import StateMachine
from transcriber import Transcriber
from translator import Translator
from volume_file import get_current_volume
from tts import TTS_LOCKFILE
import serial
import copy


def tts_playing(tts_lock):
    if tts_lock.acquire(blocking=False):
        tts_lock.release()
        return False
    else:
        return True


def main(model_str):
    display = BaseDisplay()
    renderer = SingleScreenRenderer(display)
    splitscreen_renderer = SplitScreenRenderer(display)
    renderer.clear()
    renderer.addWord('booting...')
    whisper = Transcriber(model='tiny')
    llm_speaker = LLMSpeaker(model_str)
    state_machine = StateMachine()
    main_menu = MainMenu(display, state_machine.get_source_languages(),
                         state_machine.get_target_languages())
    buttons = ButtonHandler()
    serial_output = serial.Serial('/dev/ttyS6', 115200, timeout=1)

    recorder = Recorder()
    pred_filter = PredictionFilters()
    translator = Translator()

    first_llm_invocation = False
    total_string = ''

    # Purge audio buffer while transient occurs.
    audio, vad = recorder.get_audio()
    time.sleep(1.0)
    audio, vad = recorder.get_audio()

    renderer.clear()

    renderer.addWord("Ready...")

    tts_lock = fasteners.InterProcessLock(TTS_LOCKFILE)

    def handle_menu(draw, prompt_word=''):
        if buttons.enter_pressed():
            volume, src_lang, tgt_lang = main_menu.open_menu()
            if draw:
                splitscreen_renderer.clear()
            else:
                renderer.clear()
                renderer.addWord(prompt_word)
            buttons.clear()  # clear enter presses.
            recorder.reset()
            if src_lang is not None and tgt_lang is not None:
                state_machine.set_translate_languages(src_lang, tgt_lang)
            src_lang, tgt_lang = state_machine.get_translate_languages()
            splitscreen_renderer.setLanguages(src_lang, tgt_lang, draw=draw)

    while True:
        if state_machine.get_state() == AIBoxState.CAPTION:
            handle_menu(draw=False, prompt_word='Ready...')
            if tts_playing(tts_lock):
                continue
            wav, vad_chunks = recorder.get_audio()
            s = ""
            if vad_chunks != 0:
                s = whisper.run(wav).strip()
                s = pred_filter.filter_hallucinations(s)
            else:
                time.sleep(0.1)

            if total_string == "" and len(s) > 0:
                renderer.clear()
            old_total_string = copy.copy(total_string)
            total_string, needs_update, a_words = combine_words(total_string, s)
            first_difference = len(old_total_string)
            for i in range(len(old_total_string)):
                if old_total_string[i] != total_string[i]:
                    first_difference = i
                    break
            n_updated = len(old_total_string) - first_difference
            string_to_write = ''
            for _ in range(n_updated):
                string_to_write += '\b'
            string_to_write += total_string[first_difference:]
            serial_output.write(bytes(string_to_write, 'utf-8'))

            if needs_update:
                words_to_update = total_string.split()
                # We will never need to update more than 20 words across the last two lines.
                renderer.updateNLines(
                    2, words_to_update[-20 - a_words:len(words_to_update) -
                                       a_words])
            if a_words > 0:
                renderer.addWords(total_string.split()[-a_words:])

            state_change = state_machine.update_state(s, buttons.up_pressed(),
                                                      buttons.down_pressed())
            if state_change == AIBoxState.CHATTY:
                # Switching from caption box to chatty
                renderer.clear()
                llm_speaker.switch_to_chat_mode(True)
                if first_llm_invocation:
                    llm_speaker.start_first()
                    llm_speaker.wait()
                    first_llm_invocation = False
                recorder.reset()
            elif state_change == AIBoxState.TRANSLATE:
                renderer.clear()
                recorder.reset()
                src_lang, tgt_lang = state_machine.get_translate_languages()
                splitscreen_renderer.setLanguages(src_lang, tgt_lang)
        elif state_machine.get_state() == AIBoxState.CHATTY:
            if tts_playing(tts_lock):
                continue
            renderer.addWord('Prompt:')
            wav = None
            next_button_pressed = False
            prev_button_pressed = False
            while wav is None and not (next_button_pressed or
                                       prev_button_pressed):
                wav = recorder.record_voice()
                handle_menu(draw=False, prompt_word='Prompt:')
                next_button_pressed = buttons.up_pressed()
                prev_button_pressed = buttons.down_pressed()
            s = None
            if wav is not None:
                s = whisper.run(wav).strip()
                printc("yellow", s)
            state_change = state_machine.update_state(s, next_button_pressed,
                                                      prev_button_pressed)
            if state_change == AIBoxState.CAPTION:
                renderer.clear()
                renderer.addWord("Ready...")
                # Switching from chatty to caption box
                llm_speaker.switch_to_chat_mode(False)
                if get_current_volume() != 0:
                    time.sleep(2.0)
                # Wait for tts.
                total_string = ''
                recorder.reset()
            elif state_change == AIBoxState.TRANSLATE:
                renderer.clear()
                recorder.reset()
                src_lang, tgt_lang = state_machine.get_translate_languages()
                splitscreen_renderer.setLanguages(src_lang, tgt_lang)
            elif s is not None:
                for word in s.split():
                    renderer.addWord(word)
                llm_speaker.start(s)
                renderer.scroll()
                renderer.addWord("Response:")
                response = llm_speaker.get_response()
                while response is not None:
                    renderer.addWord(response, add_spaces=False)
                    response = llm_speaker.get_response()
                llm_speaker.wait()
                renderer.scroll()
        else:
            wav = None
            next_button_pressed = False
            prev_button_pressed = False
            while wav is None and not (next_button_pressed or
                                       prev_button_pressed):
                wav = recorder.record_voice()
                handle_menu(draw=True)
                next_button_pressed = buttons.up_pressed()
                prev_button_pressed = buttons.down_pressed()
            s = None
            if wav is not None:
                s = whisper.run(wav).strip()
                printc("yellow", s)

            src_lang, tgt_lang = state_machine.get_translate_languages()
            src_lang_code, tgt_lang_code = state_machine.get_translate_language_codes(
            )
            state_change = state_machine.update_state(s, next_button_pressed,
                                                      prev_button_pressed)
            if state_change == AIBoxState.CAPTION:
                splitscreen_renderer.clear()
                renderer.addWord("Ready...")
                # Switching from chatty to caption box
                llm_speaker.switch_to_chat_mode(False)
                if get_current_volume() != 0:
                    time.sleep(2.0)
                # Wait for tts.
                total_string = ''
                recorder.reset()
            elif state_change == AIBoxState.CHATTY:
                # Switching from caption box to chatty
                splitscreen_renderer.clear()
                llm_speaker.switch_to_chat_mode(True)
                if first_llm_invocation:
                    llm_speaker.start_first()
                    llm_speaker.wait()
                    first_llm_invocation = False
                recorder.reset()
            elif state_change == AIBoxState.TRANSLATE:  # Switch languages
                splitscreen_renderer.clear()
                src_lang, tgt_lang = state_machine.get_translate_languages()
                splitscreen_renderer.setLanguages(src_lang, tgt_lang)
                recorder.reset()
            elif s is not None:
                if src_lang != 'en':
                    s = whisper.run(wav, src_lang=src_lang_code).strip()
                splitscreen_renderer.clearTop()
                splitscreen_renderer.clearBottom()
                fontfile = lang_to_font(src_lang)
                splitscreen_renderer.addTextTop(s)

                if len(s) > 100:
                    s = s[-100:]
                s = translator.translate(s, tgt_lang_code)
                s = s.replace('<unk>', '')
                fontfile = lang_to_font(tgt_lang)
                print(f'tgt font {fontfile}')
                splitscreen_renderer.addTextBottom(s)


if __name__ == "__main__":
    assert len(sys.argv) == 2, "usage: python3 main.py <model_name>"
    sys.exit(main(sys.argv[1]))
