#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-


import re
import numpy as np
from parser.patterns import patterns
import MeCab
import romkan
from typing import Dict
import itertools
import unicodedata


def set_field(infos: Dict, name: str, val_type, raw :str):
    if val_type == int:
        infos[name] = int(raw)
    elif val_type == bool:
        infos[name] = True
    elif val_type == str:
        infos[name] = raw
    elif val_type == list:
        l = infos.get(name, [])
        if raw not in l:
            l.append(raw)
        infos[name] = l


def parse(file_name: str):
    infos = {}

    masks = np.zeros(len(file_name), dtype='bool')
    clean_name = file_name.replace('_', ' ')
    for name, val_type, pattern, norm_func in patterns:
        matches = re.findall(pattern, clean_name, re.I)
        if len(matches) == 0:
            continue

        for match in matches:
            index = clean_name.index(match[0])
            masks[index:index+len(match[0])] = True

            set_field(infos, name, val_type, norm_func(match[1]))

    def normalize(part: str):
        # title
        title = part.split('(')[0]
        if title.startswith('- '):
            title = title[2:]
        if '.' in title and ' ' not in title:
            title = title.replace('.', ' ')
        title = title.replace('_', ' ')
        return title

    for i, c in enumerate(file_name):
        if c in '()[]（）【】“”"':
            masks[i] = True
    start = 0
    phrases = []
    while start < len(file_name):
        if not masks[start]:
            end = start + 1
            while end < len(masks) and not masks[end]:
                end += 1
            phrase = normalize(file_name[start:end])
            phrases.append(phrase.strip('._-@[]【 】()（）'))
            start = end
        else:
            start += 1
    if len(phrases) > 0:
        set_field(infos, 'Title', str, max(phrases, key=lambda p: len(p)))

    return infos, [p for p in phrases if len(p) > 0]

'''
class Parser:
    def _escape_regex(self, string):
        return re.sub('[\-\[\]{}()*+?.,\\\^$|#\s]', '\\$&', string)

    def __init__(self):
        self.torrent = None
        self.excess_raw = None
        self.group_raw = None
        self.start = None
        self.end = None
        self.title_raw = None
        self.parts = None

    def _part(self, name, match, raw, clean):
        # The main core instructuions
        self.parts[name] = clean

        if len(match) != 0:
            # The instructions for extracting title
            index = self.torrent['name'].find(match[0])
            if index == 0:
                self.start = len(match[0])
            elif self.end is None or index < self.end:
                self.end = index

        if name != 'excess':
            # The instructions for adding excess
            if name == 'group':
                self.group_raw = raw
            if raw is not None:
                self.excess_raw = self.excess_raw.replace(raw, '')

    def _late(self, name, clean):
        if name == 'group':
            self._part(name, [], None, clean)
        elif name == 'episodeName':
            clean = re.sub('[\._]', ' ', clean)
            clean = re.sub('_+$', '', clean)
            self._part(name, [], None, clean.strip())

    def parse(self, name):
        self.parts = {}
        self.torrent = {'name': name}
        self.excess_raw = name
        self.group_raw = ''
        self.start = 0
        self.end = None
        self.title_raw = None

        for key, value_type, pattern in patterns:
            clean_name = re.sub('_', ' ', self.torrent['name'])
            match = re.findall(pattern, clean_name, re.I)
            
            if len(match) == 0:
                continue

            index = {}
            if isinstance(match[0], tuple):
                match = list(match[0])
            if len(match) > 1:
                index['raw'] = 0
                index['clean'] = 1
            else:
                index['raw'] = 0
                index['clean'] = 0

            if key in types.keys() and types[key] == 'boolean':
                clean = True
            else:
                clean = match[index['clean']]
                if key in types.keys() and types[key] == 'integer':
                    clean = int(clean)


            if key == 'group':
                if re.search(patterns[5][1], clean, re.I) \
                        or re.search(patterns[4][1], clean):
                    continue  # Codec and quality.
                if re.match('[^ ]+ [^ ]+ .+', clean):
                    key = 'episodeName'
            if key == 'episode':
                sub_pattern = self._escape_regex(match[index['raw']])
                self.torrent['map'] = re.sub(
                    sub_pattern, '{episode}', self.torrent['name']
                )
            self._part(key, match, match[index['raw']], clean)

        # Start process for title
        raw = self.torrent['name']
        if self.end is not None:
            raw = raw[self.start:self.end].split('(')[0]

        clean = re.sub('^ -', '', raw)
        if clean.find(' ') == -1 and clean.find('.') != -1:
            clean = re.sub('\.', ' ', clean)
        clean = re.sub('_', ' ', clean)
        clean = re.sub('([\[\(_]|- )$', '', clean).strip()

        self._part('title', [], raw, clean)

        # Start process for end
        clean = re.sub('(^[-\. ()]+)|([-\. ]+$)', '', self.excess_raw)
        clean = re.sub('[\(\)\/]', ' ', clean)
        match = re.split('\.\.+| +', clean)
        if len(match) > 0 and isinstance(match[0], tuple):
            match = list(match[0])

        clean = filter(bool, match)
        clean = [item for item in filter(lambda a: a != '-', clean)]
        clean = [item.strip('-') for item in clean]
        if len(clean) != 0:
            group_pattern = clean[-1] + self.group_raw
            if self.torrent['name'].find(group_pattern) == \
                    len(self.torrent['name']) - len(group_pattern):
                self._late('group', clean.pop() + self.group_raw)

            if 'map' in self.torrent.keys() and len(clean) != 0:
                episode_name_pattern = (
                    '{episode}'
                    '' + re.sub('_+$', '', clean[0])
                )
                if self.torrent['map'].find(episode_name_pattern) != -1:
                    self._late('episodeName', clean.pop(0))

        if len(clean) != 0:
            if len(clean) == 1:
                clean = clean[0]
            self._part('excess', [], self.excess_raw, clean)
        return self.parts
'''


if __name__ == '__main__':

    print(parse('Mad.Dog.Made.S01E02.WEBRip.x264-TBS[eztv].mkv'))
    print(parse('[Bolsilibros] [Seleccion Terror 410] Garland, Curtis - Hotel de horrores [49470] (r1.0).epub'))
    print(parse('Lady.Sonia.Jessica.Foxwell.The.Members.Wife.720p.XXX.b00bastic.avi'))
    print(parse('PornMegaLoad.19.03.22.Luna.Bunny.A.Double.Dick-Down.For.A.Big-Titted.Brunette.XXX.SD.MP4-KLEENEX'))
    print(parse('WeLiveTogether.18.09.02.Ryan.Ryans.And.Vanessa.Veracruz.Stretching.Her.Out..480p.MP4-XXX'))
    print(parse('Blade.Runner.2049.2017.1080p.WEB-DL.DD5.1.H264-FGT-[rarbg.to]'))
    print(parse('[ Torrent9.tv ] Outlander.S03E08.FRENCH.WEBRip.XviD-ZT.avi'))

    print(parse('(C95) [サボテンビンタ (河上康)] 曙にゃんとニャンニャンする本 (艦隊これくしょん -艦これ-).zip'))
    print(parse('[LCBD-00712LCDV-40712] Anri Sugihara 杉原杏璃 - 東京アンリ Blu-ray [MP43.88GB&2.61GB]1080p+720p'))
    print(parse('Jungstedt, Mari - [Anders Knutas 11] No estas sola [46742] (r1.0).epub'))
    print(parse('uubbs.com 爱幼论坛 幼交 12岁俄罗斯萝莉小学生幼女视频'))

    print(parse('Amarna Miller - 21Roles.mp4'))
