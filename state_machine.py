import string
from enum import Enum
from useful_transformers.tokenizer import LANGUAGES


class AIBoxState(Enum):
    NO_CHANGE = 0
    CAPTION = 1
    CHATTY = 2
    TRANSLATE = 3


class StateMachine:

    def __init__(self):
        self.state = AIBoxState.CAPTION
        self.src_lang = 'english'
        self.tgt_lang = 'spanish'
        self.lang_to_flores200_dict = {
            'chinese': 'zho_Hans',
            'dutch': 'nld_Latn',
            'english': 'eng_Latn',
            'french': 'fra_Latn',
            'german': 'deu_Latn',
            'greek': 'ell_Grek',
            'italian': 'ita_Latn',
            'japanese': 'jpn_Jpan',
            'korean': 'kor_Hang',
            'norwegian': 'nob_Latn',
            'portuguese': 'por_Latn',
            'russian': 'rus_Cyrl',
            'spanish': 'spa_Latn',
            'thai': 'tha_Thai',
            'turkish': 'tur_Latn',
            'vietnamese': 'vie_Latn'
        }
        self.src_lang_code = self.lang_to_whisper(self.src_lang)
        self.tgt_lang_code = self.lang_to_flores200(self.tgt_lang)

    def lang_to_whisper(self, lang):
        lang = lang.lower()
        lang_codes = {v: k for k, v in LANGUAGES.items()}
        return lang_codes[lang] if lang in lang_codes.keys(
        ) and lang in self.lang_to_flores200_dict.keys() else None

    def lang_to_flores200(self, lang):
        return self.lang_to_flores200_dict[
            lang] if lang in self.lang_to_flores200_dict.keys() else None

    def get_source_languages(self):
        return [k for k in self.lang_to_flores200_dict.keys()]

    def get_target_languages(self):
        return [k for k in self.lang_to_flores200_dict.keys()]

    # Returns true is state has changed, false otherwise.
    def update_state(self, text, next_button=False, prev_button=False):
        if next_button:
            self.state = self.next_state()
            return self.state
        elif prev_button:
            self.state = self.prev_state()
            return self.state
        if text is None:
            return AIBoxState.NO_CHANGE
        if self.state in [AIBoxState.CAPTION, AIBoxState.TRANSLATE
                         ] and 'chatty' in text.lower():
            self.state = AIBoxState.CHATTY
            return AIBoxState.CHATTY
        elif self.state in [AIBoxState.CHATTY, AIBoxState.TRANSLATE
                           ] and 'caption' in text.lower():
            self.state = AIBoxState.CAPTION
            return AIBoxState.CAPTION
        elif 'translate' in text.lower():
            # Expect command in format "translate <src lang> to <dst lang>"
            text = text.translate(str.maketrans('', '', string.punctuation))
            words = text.lower().split()
            if 'translate' in words and len(
                    words) > words.index('translate') + 3:
                src_lang = words[words.index('translate') + 1]
                src_lang_code = self.lang_to_whisper(src_lang)
                to = words[words.index('translate') + 2]
                tgt_lang = words[words.index('translate') + 3]
                tgt_lang_code = self.lang_to_flores200(tgt_lang)

                if src_lang_code is not None and tgt_lang_code is not None and to == 'to':
                    self.state = AIBoxState.TRANSLATE
                    self.src_lang = src_lang
                    self.src_lang_code = src_lang_code
                    self.tgt_lang = tgt_lang
                    self.tgt_lang_code = tgt_lang_code
                    return AIBoxState.TRANSLATE

        return AIBoxState.NO_CHANGE

    def get_translate_languages(self):
        if self.state == AIBoxState.TRANSLATE:
            return self.src_lang, self.tgt_lang
        else:
            return None, None

    def get_translate_language_codes(self):
        if self.state == AIBoxState.TRANSLATE:
            return self.src_lang_code, self.tgt_lang_code
        else:
            return None, None

    def set_translate_languages(self, src_lang, tgt_lang):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.src_lang_code = self.lang_to_whisper(self.src_lang)
        self.tgt_lang_code = self.lang_to_flores200(self.tgt_lang)

    def get_state(self):
        return self.state

    def next_state(self):
        if self.state == AIBoxState.CAPTION:
            return AIBoxState.CHATTY
        elif self.state == AIBoxState.CHATTY:
            return AIBoxState.TRANSLATE
        else:
            return AIBoxState.CAPTION

    def prev_state(self):
        if self.state == AIBoxState.CAPTION:
            return AIBoxState.TRANSLATE
        elif self.state == AIBoxState.CHATTY:
            return AIBoxState.CAPTION
        else:
            return AIBoxState.CHATTY
