import os


def lang_to_font(lang):
    base_dir = os.path.realpath(os.path.dirname(__file__))
    if lang == 'chinese':
        return os.path.join(base_dir, 'fonts/noto_zh.ttf')
    elif lang == 'japanese':
        return os.path.join(base_dir, 'fonts/noto_jp.ttf')
    elif lang == 'korean':
        return os.path.join(base_dir, 'fonts/noto_kr.ttf')
    elif lang == 'thai':
        return os.path.join(base_dir, 'fonts/noto_thai.ttf')
    else:
        return os.path.join(base_dir, 'fonts/noto_default.ttf')
