#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import re
from typing import Dict

import numpy as np
from ftfy import fixes

from parser.patterns import patterns


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
    file_name = fixes.fix_character_width(file_name)

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
    print(parse('John.Wick.3.2019.HDRip.XviD.AC3-EVO'))
    print(parse('Avengers.Endgame.2019.1080p.HC.YG'))
    print(parse('Shazam! (2019) [BluRay] [720p] [YTS.LT]'))
    print(parse('Stranger.Things.Season.3.S03.720p.NF.WEB-DL.x265-HETeam'))
    print(parse('Stranger.Things.S03.WEBRip.x264-ION10'))
    print(parse('One-Punch Man - S02E11 - Everyone\'s Dignity.mkv'))
    print(parse('Brightburn.2019.HC.HDRip.XviD.AC3-EVO[TGx]'))

    print(parse('Amarna Miller - 21Roles.mp4'))
    print(parse('野兽家族.Animal.Kingdom.US.S04E05.720p.HDTV.x264.双语字幕精校版-深影字幕组.mp4'))
