#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import re
import itertools
import opencc
import jieba
from pyhanlp import *
import MeCab


# chinese
chinese_ranges = [
        ('\u4e00',  '\u62FF'),
        ( '\u6300',  '\u77FF'),
        ( '\u7800',  '\u8CFF'),
        ( '\u8D00',  '\u9FCC'),
        ( '\u3400',  '\u4DB5'),
        ('\U00020000', '\U000215FF'),
        ('\U00021600', '\U000230FF'),
        ('\U00023100', '\U000245FF'),
        ('\U00024600', '\U000260FF'),
        ('\U00026100', '\U000275FF'),
        ('\U00027600', '\U000290FF'),
        ('\U00029100', '\U0002A6DF'),
        ('\U0002A700', '\U0002B734'),
        ('\U0002B740', '\U0002B81D'),
        ('\U0002B820', '\U0002CEAF'),
        ('\U0002CEB0', '\U0002EBEF'),
        ('\U0002F800', '\U0002FA1F')
    ]

# japanese
# https://www.key-shortcut.com/en/writing-systems/%E3%81%B2%E3%82%89%E3%81%8C%E3%81%AA-japanese
hiragana = [('\u3040', '\u309F')]
katakana = [('\u30A0', '\u30FF')]
katakana_phonetic = [('\u31F0', '\u31FF')]
kanbun = [('\u3190', '\u319F')]
half_width = [('\uFF65', '\uFF9F')]

# korean
# https://www.key-shortcut.com/en/writing-systems/%ED%95%9C%EA%B5%AD-korean-script/hangul-characters-1
korean_ranges = [
    ('\u1100', '\u11FF'), # Hangul Jamo
    ('\u3130', '\u318F'), # Hangul Compatibility Jamo
    ('\uA960', '\uA97F'), # Hangul Jamo Extended-A
]

cyrillic_ranges = [
    ('\u0400', '\u04FF'),
    ('\u0500', '\u052F'),
    ('\u2DE0', '\u2DFF'),
    ('\uA640', '\uA69F')
]

def make_pattern(ranges):
    return r'(\d*[%s]+\d*)' % (''.join(['%s-%s' % (f, s) for f, s in ranges]))


chinese_pattern = make_pattern(chinese_ranges)

japanese_pattern = make_pattern(list(itertools.chain(
    hiragana, katakana, katakana_phonetic, kanbun, half_width, chinese_ranges)))
english_pattern = r'((?:[a-zA-Z]+[,.\-: ()])+[a-zA-Z0-9]+)'

korean_pattern = make_pattern(korean_ranges)

cyrillic_word = r'(?:\d*[%s]+\d*)' % (''.join(['%s-%s' % (f, s) for f, s in cyrillic_ranges]))
cyrillic_pattern = r'(%s(?:[ \-.]%s)+)' % (cyrillic_word, cyrillic_word)


t2s = opencc.OpenCC('t2s')

wakati = MeCab.Tagger("-Owakati")


def preprocess(lang: str, phrases):
    if lang == 'chinese':
        return [' '.join([term.word for term in HanLP.segment(t2s.convert(p))]) for p in phrases]
    elif lang == 'japanese':
        return [wakati.parse(p).strip() for p in phrases]
    elif lang == 'english':
        return [re.sub(r'[,.\-:()]', ' ', phrase).lower() for phrase in phrases]
    # elif lang == 'korean':
    else:
        return phrases

def extract(text: str):
    chinese_phrases = re.findall(chinese_pattern, text, re.UNICODE)
    japanese_phrases = [p for p in re.findall(japanese_pattern, text, re.UNICODE) if p not in chinese_phrases]

    chinese_phrases = [t2s.convert(p) for p in chinese_phrases]
    english_phrases = re.findall(english_pattern, text, re.UNICODE)
    korean_phrases = re.findall(korean_pattern, text, re.UNICODE)
    cyrillic_phrases = re.findall(cyrillic_pattern, text, re.UNICODE)

    return {
        'chinese': preprocess('chinese', chinese_phrases),
        'japanese': preprocess('japanese', japanese_phrases),
        'english': preprocess('english', english_phrases),
        'korean': preprocess('korean', korean_phrases),
        'cyrillic': preprocess('cyrillic', cyrillic_phrases)
    }

if __name__ == '__main__':
    print(extract('南河茜(仲村みう,なかむらみう)，日本女演员，2017年出道。'))
    print(extract('南河茜(仲村みう,なかむらみう)，日本女演员，2017年出道。'))
    print(extract('Anri Sugihara 杉原杏璃 - 東京アンリ Blu-ray'))
    print(extract('60 минут по горячим следам (дневной выпуск в 12_50) от 01.07.19.mp4'))