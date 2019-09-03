#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

# copy from https://github.com/divijbindlish/parse-torrent-name/blob/master/PTN/patterns.py
# add chinese, japanese support
import os
import re
from parser.file import file_pattern
from util.code import codes

'''
JAV_CODE_PREFIX = '|'.join([
    'abc', 'abp', 'abs', 'aby', 'adn', 'adz', 'affa', 'afs', 'aka', 'akph',
    'ama', 'ambi', 'annd', 'ap', 'apaa', 'apae', 'apak', 'apkh', 'apnh', 'apns',
    'aqsh', 'ara', 'arso', 'arm', 'at', 'atfb', 'atid', 'atom', 'aukg', 'avkh', 'avop', 'avsa',

    'bazx', 'bbad', 'bban', 'bbi', 'bcdp', 'bcdv', 'bcv', 'bdsr', 'beb', 'bf', 'bobb', 'bgn', 'bid', 'bijn', 'blk', 'blor', 'bra',
    'bt', 'bur',

    'ccx', 'cead', 'cesd', 'chn', 'chrv', 'chs', 'cjod', 'club', 'cmd', 'cmi', 'cnd', 'crc', 'crpd', 'cwm',

    'dandy', 'dap', 'dasd', 'davi', 'dcol', 'dcv', 'ddk', 'ddt', 'dic', 'dism', 'diy', 'djsk', 'dmbl', 'dmdg', 'docp', 'doks',
    'dom', 'dtrs', 'dv', 'dvaj', 'dvdes', 'dvdms',

    'ebod', 'ecb', 'edd', 'ekdv', 'ekw', 'emp', 'esk', 'etqr', 'eyan', 'eq',

    'faa', 'fc2ppv', 'fch', 'fiv', 'fone', 'fset', 'fsgd', 'fskt', 'fsre', 'fsta', 'fstc', 'ftn',

    'gapl', 'gar', 'gcicd', 'gdhh', 'gdju', 'gdtm', 'gent', 'gets', 'gfd', 'ggg', 'gg', 'gne', 'gs', 'gtal', 'gtj', 'gun', 'gvg',

    'har', 'havd', 'hawa', 'hbad', 'hdi', 'hdka', 'herr', 'heyzo', 'hiz', 'hjmo', 'hmgl', 'hmpd', 'hnd', 'hndb', 'hnds', 'hntv',
    'hodv', 'homa', 'honb', 'hrrb', 'hunt', 'hunta', 'husr', 'hzgd',

    'ibw', 'id', 'idbd', 'iene', 'iesp', 'inct', 'inu', 'ipsd', 'iptd', 'ipx', 'ipz',

    'jag', 'jan', 'jks', 'jmty', 'jrzd', 'juc', 'jufd', 'jufe', 'jux', 'juy', 'jksr',

    'kagp', 'kane', 'kawd', 'kbi', 'kdg', 'kdkj', 'kibd', 'kidm', 'kird',  'ko', 'km', 'kmhr', 'ksbj', 'ksdo', 'ktds',
    'ktkc', 'ktkl', 'ktkp', 'ktkq', 'ktkx', 'ktkz', 'ktr', 'ktra', 'kwbd', 'kws', 'kwsd', 'kv'

    'lad', 'laf', 'lafbd', 'lid', 'lid03', 'lod', 'lol', 'love', 'lxvs', 'lzpl',

    'madm', 'magn', 'mann', 'maraa', 'mas', 'maxa', 'mcsr', 'mct', 'mdar', 'mdb', 'mds', 'mdtm', 'mdyd',
    'mdym', 'mei', 'meyd', 'mgt', 'miaa', 'miad', 'miae', 'mibd', 'midd', 'mide', 'mifd', 'migd', 'mird', 'mism',
    'mist', 'mium', 'mizd', 'mkbd', 'mkd', 'mkmp', 'mmgh', 'mmkz', 'mmna', 'mmnd', 'mmts', 'mmus', 'mmxd',
    'moc', 'momj', 'mrxd', 'mudr', 'mukd', 'mum', 'mvsd', 'mxgs', 'mxsps', 'mond', 'mywife',

    'nacr', 'nacs', 'nafi', 'naka', 'nanx', 'nass', 'natr', 'ngod', 'nhdta', 'nhdtb', 'nise',  'nitr', 'nkkd', 'nks',
    'nnf', 'nnpj', 'npv', 'nsps', 'nsr', 'ntr', 'nttr',

    'oba', 'ofje', 'ogpp', 'okad', 'oksn', 'om', 'once', 'oned', 'onet', 'onez', 'ongp', 'onsd', 'opud', 'oyc', 'oyj',
    'parm', 'pat', 'pgd', 'piyo', 'pjd', 'pk', 'pkpd', 'pla', 'post', 'pppd', 'pps', 'ppt', 'pred', 'prnfle', 'prou', 'prtd',
    'pt', 'ptko', 'ptks', 'pxh',
    'qp',

    'r18', 'raw', 'rbd', 'rct', 'rctd', 'rdd', 'rdt', 'real', 'rebdb', 'red', 'rega', 'rhj', 'rki', 'rtp',

    'saba', 'sace', 'sama', 'scop', 'scpx', 'sdab', 'sdde', 'sden', 'sdiy', 'sdmu', 'sdmt', 'sdnm', 'sdsi', 'sero', 'sky',
    'sfba', 'sga', 'she', 'shic', 'shkd', 'shx', 'siro', 'sis', 'siv', 'sl', 'smdv', 'smile', 'snis', 'soav', 'soe', 'sora',
    'sprd', 'spz', 'sqte', 'srs', 'srxv', 'ssni', 'sspd', 'star', 'stars', 'stp', 'stss', 'suji', 'supa', 'supd', 'svdvd', 'sw', 'sy',

    't28', 'tbl', 'team', 'tek', 'tem', 'temp', 'tikb', 'tikc', 'tikm', 'tikp', 'tki', 'tmcy', 'tmem', 'tmhp', 'tmvi',
    'tokyo', 'tomn', 'tppn', 'tre', 'trp', 'trum', 'tus', 'tyod',

    'uby', 'umd', 'umso', 'upsm', 'urlh',

    'vagu', 'vdd', 'vec', 'venu', 'vgd', 'vicd', 'voss', 'vrtm', 'vvp',

    'wanz', 'whx', 'wkd', 'www',

    'xrw', 'xv', 'xvsr',

    'yal', 'ymdd', 'yrh', 'yst',

    'zex', 'zizg', 'zuko', 'zzy'])
'''

jav_code_pattern = r'\b(((%s)[\-_. ]?0{0,2}([0-9]{3,6})(\w\b)?))' % ('|'.join(codes))


def normalize_jav_code(text: str):
    assert re.match(jav_code_pattern, text)
    return re.sub(jav_code_pattern, r'\3-\4\5', text).upper()


def normalize_general(text: str):
    return text


def normalize_resolution(text: str):
    return re.sub(r'[.\-_\s]', '', text)


patterns = [
    ('code', list, r'\b(((%s)[\-_. ]?[0-9]{2,8}(?=\w|\b)?))' % ('|'.join(codes)), normalize_general),
    ('season', list, r'(?i)\b(s?([0-9]{1,2}))[ex]', normalize_general),
    ('season', list, r'(?i)\b(s(?:eason[._\- ]?)?([0-9]{1,2}))', normalize_general),
    ('episode', list, r'(?i)(e(?:p(?:isode)?)?([0-9]{2,4}))\D', normalize_general),
    ('episode', list, r'(-\s+([0-9]{1,2}))(?:[^0-9]|$)', normalize_general),
    ('year', list, r'\b(((?:19[0-9]|20[0-9])[0-9]))\b', normalize_general),
    ('date', list,
     r'\b((((?:19[0-9]|20[0-9])[0-9]|[012789][0-9]|[1-9])[.\-_]?(0[1-9]|1[0-2])[.\-_]?(0[1-9]|[12][0-9]|3[01])?))\b',
     normalize_general),

    ('cracked', bool, r'\b((cracked|Crack|keygen|破解版))\b', normalize_general),
    ('subtitle_group', str, r'\b((.{2, 4}字幕组))', normalize_general),

    ('resolution', list, r'(?i)\D(m?([0-9]{3,4}[ip]|4K|[0-9]{2,4}[._\- ]?k(bps)?))\b', normalize_resolution),
    ('quality',
     list,
     r'(?i)[^a-z](((PPV\.)?[HP]DTV|(HD)?CAM|B[DR]Rip|(HD-?)?TS|(PPV )?WEB-?DL((DVD)?Rip)?|HD(TV)?Rip|DVDRip|TVRip|CamRip|W[EB]BRip|Blu-?Ray|DvDScr|telesync))[^a-z]',
     normalize_general),

    ('codec', str, r'(?i)\b((xvid|[hx]\.?26[45]))', normalize_general),
    ('tag', list, r'(?i)((无码|有码|骑兵|步兵|無碼))', normalize_general),
    ('person', list, r'(?i)((明日花绮罗))', normalize_general),
    ('audio', str, r'(?i)\b((MP3|DD5\.?1|Dual[\- ]Audio|LiNE|DTS|AAC[.-]LC|AAC(\.?2\.0)?|AC3([\. ]5\.1)?([.-]EVO)?))\b',
     normalize_general),
    ('region', str, r'(?i)\b(R([0-9]))\b', normalize_general),
    ('size', list, r'(?i)((\d+(\.\d+)?(?:GB|MB)))\W', normalize_general),
    ('website', str, r'^(\[ ?([^\]]+?) ?\])', normalize_general),
    ('url', str, r'(?i)\b((www\.\w+\.\w{2,4}|\w+\.(org|net|com|tv|io|ru|cz)|ytz))(?:[^a-z]|$)', normalize_general),
    ('version', str, r'(?i)\b((((v(er(sion)?)?|r(ev(ision)?)?)[.\-_ ]?(\d+)([.\-_]\d+){0,3})))', normalize_general),
    ('version', str, r'(?i)\b((\d+(\.\d+)?[ ]?build[ ]?\d+))\b', normalize_general),
    ('language', list, r'(?i)\b((rus|ita|eng|chs|FRENCH))\b', normalize_general),
    ('sbs', str, r'(?i)\b(((?:Half-)?SBS))\b', normalize_general),
    ('container', str, r'(?i)\b((MKV|AVI|MP4))\b', normalize_general),

    # ('build_dir_tree', str, r'\b(- ?([^\-]+(?:-={[^\-]+-?$)?))$', normalize_general),

    ('extended', bool, r'(?i)\b(EXTENDED(:?.CUT)?)\b', normalize_general),
    ('hardcoded', bool, r'(?i)\b((HC))\b', normalize_general),
    ('proper', bool, r'(?i)\b((PROPER))\b', normalize_general),
    ('repack', bool, r'(?i)\b((REPACK))\b', normalize_general),
    ('widescreen', bool, r'(?i)\b((WS))\b', normalize_general),
    ('unrated', bool, r'(?i)\b((UNRATED))\b', normalize_general),
    ('3d', bool, r'(?i)\b((3D))\b', normalize_general),
    ('suffix', str, r'(?i)(\.(%s))$' % file_pattern, normalize_general),
]

spam_patterns = r'(論壇文宣|_____padding_file_)'
