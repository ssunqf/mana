#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import re
import itertools
import opencc
import jieba
from pyhanlp import *
import MeCab

jieba.load_userdict('./dict/words.txt')

# chinese
chinese_ranges = [
        ('\u2E80', '\u2EFF'),
        ('\u2F00', '\u2FDF'),
        ('\u3400', '\u4DBF'),
        ('\u4e00',  '\u62FF'),
        ('\u6300',  '\u77FF'),
        ('\u7800',  '\u8CFF'),
        ('\u8D00',  '\u9FCC'),

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
    return r'([%s]+)' % (''.join(['%s-%s' % (f, s) for f, s in ranges]))


chinese_pattern = make_pattern(chinese_ranges)

japanese_pattern = make_pattern(list(itertools.chain(
    hiragana, katakana, katakana_phonetic, kanbun, half_width, chinese_ranges)))
english_pattern = r'((?:[a-zA-Z]+[,.\-: ()&])?[a-zA-Z0-9]+)'

korean_pattern = make_pattern(korean_ranges)

cyrillic_word = r'(?:[%s]+)' % (''.join(['%s-%s' % (f, s) for f, s in cyrillic_ranges]))
cyrillic_pattern = r'(%s(?:[ \-.]%s)+)' % (cyrillic_word, cyrillic_word)


tradition2simple = opencc.OpenCC('t2s')

wakati = MeCab.Tagger("-Owakati")


def preprocess(lang: str, phrases):
    if lang == 'chinese':
        return [' '.join([term.word for term in HanLP.segment(tradition2simple.convert(p))]) for p in phrases]
    elif lang == 'japanese':
        return [wakati.parse(p).split() for p in phrases]
    elif lang == 'english':
        return [re.sub(r'[,.\-:()]', ' ', phrase).lower() for phrase in phrases]
    # elif lang == 'korean':
    else:
        return phrases


def extract(text: str):
    chinese_phrases = re.findall(chinese_pattern, text, re.UNICODE)
    japanese_phrases = [p for p in re.findall(japanese_pattern, text, re.UNICODE) if p not in chinese_phrases]

    chinese_phrases = [tradition2simple.convert(p) for p in chinese_phrases]
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


word_pattern = make_pattern(list(itertools.chain(
    hiragana, katakana, katakana_phonetic, kanbun, half_width, chinese_ranges,
    korean_ranges, cyrillic_ranges, [('a', 'z'), ('A', 'Z')])))


def contain(ranges, c):
    for start, end in ranges:
        if start <= c <= end:
            return True
    return False


def tokenize(text: str):

    def _tokenize(text: str):
        start = 0
        while start < len(text):
            end = start
            lang = 'unknown'

            if '0' <= text[end] <= '9':
                while end < len(text) and '0' <= text[end] <= '9':
                    end += 1
                    lang = 'number'
            elif 'a' <= text[end].lower() <= 'z':
                # ENGLISH
                while end < len(text) and 'a' <= text[end].lower() <= 'z':
                    end += 1
                    lang = 'english'

            elif contain(list(itertools.chain(
                    hiragana, katakana, katakana_phonetic, kanbun, half_width, chinese_ranges)), text[end]):
                # CJK
                while end < len(text) and contain(list(itertools.chain(
                        hiragana, katakana, katakana_phonetic, kanbun, half_width, chinese_ranges)), text[end]):
                    end += 1
                    lang = 'cjk'

                if lang == 'cjk':
                    for c in text[start:end]:
                        if not contain(chinese_ranges, c):
                            lang = 'japanese'
                            break
                    else:
                        lang = 'chinese'
            elif contain(korean_ranges, text[end]):
                # KOREAN
                while end < len(text) and contain(korean_ranges, text[end]):
                    end += 1
                    lang = 'korean'
            elif contain(cyrillic_ranges, text[end]):
                # cyrillic
                while end < len(text) and contain(cyrillic_ranges, text[end]):
                    end += 1
                    lang = 'cyrillic'

            if end > start:
                yield lang, text[start:end]
                start = end
            else:
                yield lang, text[start:start+1]
                start += 1

    words = []
    for lang, word in _tokenize(text):
        if lang == 'chinese':
            words.extend(jieba.cut(tradition2simple.convert(word)))
        elif lang == 'japanese':
            words.extend([tradition2simple.convert(w) for w in wakati.parse(word).split()])
        elif lang == 'english':
            words.append(word.lower())
        else:
            words.append(word)

    return [w for w in words if w not in '._-+&@()[]（）【】「」=、/\\, \t\'\"#!~`']


if __name__ == '__main__':
    print(extract('南河茜(仲村みう,なかむらみう)，日本女演员，2017年出道。'))
    print(extract('南河茜(仲村みう,なかむらみう)，日本女演员，2017年出道。'))
    print(extract('Anri Sugihara 杉原杏璃 - 東京アンリ Blu-ray'))
    print(extract('60 минут по горячим следам (дневной выпуск в 12_50) от 01.07.19.mp4'))

    print(tokenize('[Heavy Blues] Lonely Kamel 2008-2014 (Jamal The Moroccan)'))
    print(tokenize('Luther Wright & The Wrongs - Rebuild The Wall - 2001'))
    print(tokenize('한국 & 외국 영화 엑기스 모음 3 Edited By HHan'))
    print(tokenize('Antman.And.The.Wasp.2018.TRUEFRENCH.HDRiP.MD.XViD-STVFRV.avi'))
    print(tokenize('みまさか(iuu05.com)欧美萝莉-西洋萝莉 lolita -ロリ'))
    print(tokenize('[190619]逢田梨香子 1st EP「Principal」(CD+DVD初回限定盤)[320K].rar'))
    print(tokenize('ymdha@草榴社區@MOKO美空徐莹私拍套图'))
    print(tokenize('请所有支持热爱色中色的会员互相转帖告知！让世人知道真相。916事件'))