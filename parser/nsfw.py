#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import os
import re
from parser.parse import parse
from ahocorapy.keywordtree import KeywordTree
import itertools

basedir = os.path.abspath(os.path.dirname(__file__))

keywords = {
    'porno', 'asshole', 'fucked', 'pussy', 'cumshot',
    'sis001', 'hjd2048', '18p2p', 'sod99', 't66y', 'mo6699', 'dioguitar23', 'kan224',
    'sex8', 'sexinsex', 'fxxx', 'xxx', 'huge tits'
}


def load_dict():
    headwords = set()
    with open(os.path.join(basedir, '../data/dict/nsfw.en')) as input:
        for line in input:
            word, count = line.strip().split(',')
            count = int(count)
            if count < 10:
               break
            headwords.add(word)

    with open(os.path.join(basedir, '../data/dict/nsfw.zh')) as input:
        for line in input:
            word = line.strip()
            headwords.add(word)
    return headwords


def load_words():
    words = set()
    with open(os.path.join(basedir, '../data/dict/words.txt')) as input:
        for line in input:
            words.add(line.strip())
    return words

keywords.update(load_dict())
keywords.update(load_words())

keyword_pattern = re.compile('(' + '|'.join(keywords) + ')', re.IGNORECASE)

keyword_tree = KeywordTree(case_insensitive=True)
for word in keywords:
    keyword_tree.add(word)
keyword_tree.finalize()

def nsfw_text(text: str):
    if keyword_tree.search(text):
        return True
    return False

anti_filter_pattern = r'(?<= )(\w)(?= )'

def anti_fiter(text: str):
    if len(re.findall(anti_filter_pattern, text)) > 6:
        return True
    return False


def detect_nsfw(metainfo):
    if ('publisher' in metainfo and metainfo['publisher'] not in {'Mp4Ba'}) or 'publisher-url' in metainfo:
        return True
    text = '\n'.join([metainfo['name']] + [file['path'] for file in metainfo.get('files', [])])
    if nsfw_text(text) or anti_fiter(metainfo['name']):
        return True

    info, _ = parse(text)
    if 'code' in info:
        return True

    return False


if __name__ == '__main__':
    print(nsfw_text('FakeTaxi - Sexy redhead with huge tits'))
    print(nsfw_text('苗 條 胸 小 美 女 和 男 友 高 層 公 寓 大 開 窗 邊'))
    print(nsfw_text('注册梦缘看美丽主播—18岁妹妹偷偷自慰扣穴高潮'))
    print(nsfw_text('ymdha@草榴社區@Tokyo Hot n0633 美乳新人女優再起不能姦 中島まゆみ加藤夏希系之新人美乳女優一次破壞怠盡作品'))
    print(nsfw_text('ymdha@草榴社區@MOKO美空徐莹私拍套图'))
    print(nsfw_text('狼群.特效中英字幕.The.Wolfpack.2015.HD1080P.X264.AAC.English.CHS-ENG.Mp4Ba'))
    print(nsfw_text('上原深雪'))
    print(nsfw_text('自慰扣穴高潮'))
    print(anti_fiter('苗 條 胸 小 美 女 和 男 友 高 層 公 寓 大 開 窗 邊'))
    print(anti_fiter('FakeTaxi - Sexy redhead with huge tits'))
