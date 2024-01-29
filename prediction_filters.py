"""Methods to screen model prediction text that is unexpected or pathological.

We're looking for:
1. Filtering any model hallucinations. Hallucinations take the form of repeated
   phrases up to a few words long. Extract repeats past a threshold from the
   text.

2. An unexpected amount of words given the number of one-second segments of
   of audio exceeind an experimentally-determined voice activity threshold.
"""

import numpy as np
import copy


class PredictionFilters():

    def _filter_hallucination_impl(self, words):
        ''' If a pattern with up to PHRASE_LEN is found more than REPEAT_THRESHOLD times,
            all further repeats are sliced from the output string.
        '''
        REPEAT_THRESHOLD = 3
        PHRASE_LEN = 8
        for idx in range(len(words) - REPEAT_THRESHOLD):
            for phrase_len in range(1, PHRASE_LEN):
                if idx + phrase_len * REPEAT_THRESHOLD <= len(words):
                    first_phrase = words[idx:idx + phrase_len]
                    repeats_found = 1
                    words_left = len(words) - idx
                    for repeat_num in range(1, int(words_left / phrase_len)):
                        start_idx = idx + repeat_num * phrase_len
                        test_phrase = words[start_idx:start_idx + phrase_len]
                        if first_phrase == test_phrase:
                            repeats_found += 1
                        else:
                            break

                    if repeats_found > REPEAT_THRESHOLD:
                        left = words[:idx + REPEAT_THRESHOLD * phrase_len]
                        right = words[idx + repeats_found * phrase_len:]
                        return left + right, True
        return words, False

    def filter_hallucinations(self, text, characters=False):
        ''' Filter repeatedly until all hallucinations have been removed from the
            text. Filtering repeatedly seems helpful in cases where the user
            intentionally says a word more than the threshold number of times,
            then a legitimate hallucination is found.
        '''
        # Certain hallucinatinos appear as a sequence of '!!!!' with no spaces.
        if len(text) > 15 and len(text.split()) <= 1:
            return ''
        # "you" is the default output of whisper with no audio. '.' or '...' show up in silent clips.
        if text is None or text == 'you' or text == '.' or text == '...':
            print("filtering - no new meaningful text found")
            return ''
        words = copy.copy(text) if characters else text.split()
        keep_filtering = True
        while keep_filtering:
            words, keep_filtering = self._filter_hallucination_impl(words)

        return words if characters else ' '.join(words)
