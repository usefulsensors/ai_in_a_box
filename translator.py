import os

import ctranslate2
import transformers


class Translator(object):
    """ Attribution: uses FaceBook model with licence CC-BY-NC 4.0.
    https://huggingface.co/facebook/nllb-200-distilled-600M
    """

    def __init__(self):
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'downloaded/nllb-200-distilled-600M')
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(model_path)
        self.translator = ctranslate2.Translator(model_path)

    def translate(self, source, tgt_lang_code):
        tokens = self.tokenizer.convert_ids_to_tokens(
            self.tokenizer.encode(source))
        results = self.translator.translate_batch(
            [tokens], target_prefix=[[tgt_lang_code]])
        target_tokens = results[0].hypotheses[0][1:]
        target_text = self.tokenizer.decode(
            self.tokenizer.convert_tokens_to_ids(target_tokens))
        return target_text
