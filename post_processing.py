from Levenshtein import distance


# Given two sequences of words, determine the ratio of correct matches to incorrect matches.
def similarity(a, b, use_distance=True):
    overlap = 0
    for idx in range(min(len(a), len(b))):
        if use_distance:
            overlap += int(distance(a[idx], b[idx]) <= 2)
        else:
            overlap += int(a[idx] == b[idx])
    return overlap


def combine_characters(a, b):
    ''' Line up the two input strings of utf8 characters so that they match as
    closely as possible then splice them together.

    Returns (spliced string, needs_update, number of new characters)
    '''
    if a == "":
        return b, False, len(b)
    if b == "":
        return a, False, 0

    COMBINATION_WINDOW_LEN = 15
    MAX_NEW_WORDS = 10
    max_similarity = 0
    max_similarity_offset = 0
    for offset in range(min(len(b), MAX_NEW_WORDS)):
        a_idx = max(0, len(a) - len(b) + offset)
        sim = similarity(a[a_idx:], b, use_distance=False)
        if sim > max_similarity:
            max_similarity = sim
            max_similarity_offset = offset

    if max_similarity == 0:
        return a + b, False, len(b)
    # Prevent editing of old text when nothing new is present.
    if max_similarity_offset == 0 and len(b) < len(a):
        return a, False, 0

    a_end_idx = len(b) - max_similarity_offset
    out_string = a[:-a_end_idx] + b

    words_to_check = min(MAX_NEW_WORDS, len(a),
                         len(out_string) - max_similarity_offset)

    start_out = len(out_string) - words_to_check - max_similarity_offset
    end_out = len(out_string) - max_similarity_offset
    start_a = len(a) - words_to_check
    end_a = len(a)

    out_comp = [out_string[i] for i in range(start_out, end_out)]
    a_comp = [a[i] for i in range(start_a, end_a)]
    needs_update = out_comp != a_comp

    return out_string, needs_update, max_similarity_offset


def combine_words(a, b):
    ''' Line up the two input strings so that they match as closely as possible
    then splice them together.

    Returns (spliced string, needs_update, number of new words)
    '''
    if a == "":
        return b, False, len(b)
    if b == "":
        return a, False, 0

    COMBINATION_WINDOW_LEN = 15
    MAX_NEW_WORDS = 10
    a_s = [word for word in a.split(' ') if word != '']
    b_s = [word for word in b.split(' ') if word != ''
          ][-COMBINATION_WINDOW_LEN:]
    max_similarity = 0
    max_similarity_offset = 0
    for offset in range(min(len(b_s), MAX_NEW_WORDS)):
        a_idx = max(0, len(a_s) - len(b_s) + offset)
        sim = similarity(a_s[a_idx:], b_s)
        if sim > max_similarity:
            max_similarity = sim
            max_similarity_offset = offset

    if max_similarity == 0:
        return a + ' ' + b, False, len(b_s)
    # Prevent editing of old text when nothing new is present.
    if max_similarity_offset == 0 and len(b_s) < len(a_s):
        return a, False, 0

    # Shorten to max overlap length for combination step.
    b_s = b_s[-MAX_NEW_WORDS:]
    a_end_idx = len(b_s) - max_similarity_offset
    out_wordlist = a_s[:-a_end_idx] + b_s

    words_to_check = min(MAX_NEW_WORDS, len(a_s),
                         len(out_wordlist) - max_similarity_offset)

    needs_update = any([
        out_wordlist[-i - max_similarity_offset] != a_s[-i]
        for i in range(words_to_check)
    ])

    return ' '.join(out_wordlist), needs_update, max_similarity_offset
