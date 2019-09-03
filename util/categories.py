#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import re
import os
import asyncio
from collections import Counter
from typing import Dict
from pprint import pprint
from better_bencode import loads as bdecode, dumps as bencode
import mimetypes

categories = [
    ('video', '影视'),
    ('audio', '音乐'),
    ('archive', '文档'),
    ('ebook', '书藉'),
    ('software', '软件'),
    ('image', '图片'),
    ('other', '其它')
]

rar_part_re = re.compile("^\.(r[0-9]+|md[0-9]+)$")


def guess_file(filename):
    typ = None
    mime = mimetypes.guess_type(filename, strict=False)[0]
    if mime:
        typ = mime_to_category(mime)
    if typ is None:
        ext = os.path.splitext(filename)[1]
        if ext:
            typ = extension_to_category(ext)
    return typ


def extension_to_category(ext):
    ext = ext.lower()
    if ext in {
        '.m2ts', '.clpi', '.vob', '.rmvb', '.ifo', '.bup', '.cdg', '.m4v', '.bdmv', '.bik', '.f4v', '.idx', '.vp6',
        '.ogm', '.divx', '.mpg', '.avi',
        '.m2v', '.tp', '.ratdvd', '.iva', '.m2t'
    }:
        return 'video'
    elif ext in {
        '.pak', '.arc', '.sub', '.ccd', '.accurip', '.img', '.vghd', '.psarc', '.wv', '.tta', '.mds', '.gz', '.msu',
        '.pimx', '.mdf', '.pima', '.package',
        '.pck', '.cso', '.sfz', '.wbfs', '.ova', '.xz', '.bz2', '.vpk', '.nrg'
    }:
        return 'archive'
    elif ext in {
        '.ncw', '.nki', '.ape', '.mka', '.ac3', '.m4b', '.sb', '.exs', '.tak', '.wem', '.m4r', '.fsb', '.cue', '.rx2',
        '.shn', '.sdat', '.nkm', '.aac', '.nmsv',
        '.at3', '.pcm', '.nkc', '.swa', '.nkx', '.m4p', '.dtshd', '.ksd', '.dts'
    }:
        return 'audio'
    elif ext in {'.dds', '.tga', '.webp', '.raw', '.abr', '.max', '.wmf', '.xm', '.ipl', '.pam'}:
        return 'image'
    elif ext in {'.nfo', '.epub', '.log', '.mobi', '.lit', '.azw3', '.prc', '.asd', '.vtx', '.fb2', '.cas', '.md',
                 '.ps3'}:
        return 'ebook'
    elif ext in {
        '.php', '.lua', '.cmd', '.opa', '.pyd', '.cs', '.strings', '.res', '.properties', '.manifest', '.nib', '.mo',
        '.rpyc', '.rpy', '.x32', '.fda', '.mui'
                                         '.nds', '.fx', '.prg', '.rsrc', '.scss', '.dmt', '.catalyst', '.pkg', '.bin',
        '.so', '.sql', '.man', '.mui', '.nds', '.qm', '.3ds', '.chd', '.inf'
    }:
        return 'software'
    elif ext in {
        '.sldprt', '.url', '.mpls', '.ass', '.dat', '.ini', '.db', '.xrm-ms', '.xxx', '.upk', '.mst', '.fxp', '.ans',
        '.opal', '.w3x', '.zdct', '.ff', '.gmp',
        '.fbl', '.map', '.md5', '.dcp', '.reg', '.lrtemplate', '.lmk', '.bc!', '.assets', '.poi', '.gp3', '.gp4',
        '.3dl', '.toc', '.diz', '.cfg', '.nka', '.smc', '.lim',
        '.nm2', '.lng', '.amt', '.big', '.paz', '.h2p', '.ssa', '.szs', '.xnb', '.dwg', '.ide', '.sys', '.index',
        '.3dc', '.rlf', '.lst', '.ftr', '.ozf2', '.sxt', '.ipa',
        '.nes', '.data', '.fxb', '.bndl', '.lyc', '.smarch', '.bfdca', '.sims3pack', '.fuz', '.fpa', '.fsp', '.sdfdata',
        '.meta', '.bk2', '.unity3d', '.nkp', '.dsf', '.loc',
        '.lnk', '.nksn', '.lzarc', '.mpq', '.plist', '.hdr', '.gmspr', '.avs', '.rxdata', '.bnk', '.rvdata2', '.sabs',
        '.pz2', '.w3m', '.bsp', '.msp', '.sse', '.aep',
        '.efd', '.ngrr', '.rpym', '.dff', '.obf', '.unr', '.sba', '.ffp', '.nm7', '.rpymc', '.jcd', '.pkz', '.vdb',
        '.fxc', '.grir', '.dylib', '.gpx', '.dl_', '.pub', '.txd',
        '.sgdt', '.s', '.afpk', '.cmp', '.atw', '.gp5', '.sabl', '.cci', '.smd', '.config', '.mcd', '.prp', '.ifs',
        '.dmp', '.pxs', '.icc', '.icns', '.yrdm', '.prt_omn', '.sob',
        '.rwd', '.sgo', '.torrent', '.key', '.ttf', '.sig', '.otf', '.m3u8', '.pac', '.npk', '.ph', '.pup'
    }:
        return 'other'
    elif ext in {'.pea'} or rar_part_re.match(ext):
        return 'archive'
    else:
        return None


def mime_to_category(mime):
    typ, sub_typ = mime.split('/')
    sub_typ = sub_typ.lower()
    if typ == "video":
        return 'video'
    elif typ == "audio":
        return "audio"
    elif typ == "archive":
        return "archive"
    elif typ == "image":
        return "image"
    elif typ in {"model", "message", "chemical"}:
        return 'ebook'
    elif typ == "text":
        if sub_typ in {
            'vnd.dmclientscript', 'x-c++hdr', 'x-c++src', 'x-chdr', 'x-crontab',
            'x-csh', 'x-csrc', 'x-java', 'x-makefile', 'x-moc', 'x-pascal', 'x-pcs-gcd',
            'x-perl', 'x-python', 'x-sh', 'x-tcl', 'x-dsrc', 'x-haskell', 'x-literate-haskell',
        }:
            return 'software'
        elif sub_typ in {"vnd.abc", "x-lilypond"}:
            return "audio"
        else:
            return 'ebook'
    elif typ == "application":
        if sub_typ in {"dicom"}:
            return "image"
        elif sub_typ in {
            "ecmascript", "java-archive", "javascript", "java-vm", "vnd.android.package-archive",
            "x-debian-package", "x-msdos-program", "x-msi", "x-python-code", "x-redhat-package-manager",
            "x-ruby", "x-shockwave-flash", "x-silverlight", 'x-cab', 'x-sql', 'x-msdownload'
        }:
            return "software"
        elif sub_typ in {
            "gzip", "rar", "x-rar-compressed", "x-7z-compressed", "x-apple-diskimage",
            "x-iso9660-image", "x-lha", "x-lzh", "x-gtar-compressed", "x-tar", "zip"
        }:
            return 'archive'
        elif sub_typ in {"json", "msword", "oebps-package+xml", "onenote", "pdf", "postscript", "rtf", "smil+xml",
                         "x-abiword", "x-hdf", "x-cbr", "x-cbz"}:
            return 'ebook'
        elif any(sub_typ.startswith(t) for t in
                 ["vnd.ms-", "vnd.oasis.opendocument", "vnd.openxmlformats-officedocument", "vnd.stardivision",
                  "vnd.sun.xml"]):
            return 'ebook'
        else:
            return None
    elif mime == "x-epoc/x-sisx-app":
        return 'software'
    else:
        return None


def guess_metainfo(metainfo: Dict):
    if 'files' in metainfo:
        counter = Counter()
        for file in metainfo['files']:
            counter[guess_file(file['path'])] += file['length']
        return max(counter.items(), key=lambda x: x[1])[0]
    else:
        return guess_file(metainfo['name'])


CODE_PREFIX = [
    'abc', 'abp', 'abs', 'aby', 'adn', 'adz', 'affa', 'afs', 'aka', 'akph',
    'ama', 'ambi', 'annd', 'ap', 'apaa', 'apae', 'apak', 'apkh', 'apnh', 'apns',
    'aqsh', 'ara', 'arso', 'at', 'atfb', 'atid', 'atom', 'aukg', 'avkh', 'avop', 'avsa',

    'bazx', 'bbad', 'bban', 'bbi', 'bcdp', 'bcdv', 'bcv', 'bdsr', 'bf', 'bgn', 'bid', 'bijn', 'blk', 'blor', 'bra', 'bt', 'bur',

    'ccx', 'cesd', 'chn', 'chrv', 'chs', 'cjod', 'club', 'cmd', 'cmi', 'cnd', 'crc', 'crpd', 'cwm',

    'dandy', 'dap', 'dasd', 'davi', 'dcol', 'dcv', 'ddk', 'dic', 'dism', 'diy', 'djsk', 'dmbl', 'dmdg', 'docp', 'doks', 'dom', 'dtrs', 'dvaj', 'dvdes', 'dvdms',

    'ebod', 'ecb', 'edd', 'ekdv', 'ekw', 'emp', 'esk', 'etqr', 'eyan',

    'faa', 'fc2ppv', 'fch', 'fiv', 'fone', 'fset', 'fsgd', 'fskt', 'fsre', 'fsta', 'fstc', 'ftn',

    'gapl', 'gar', 'gcicd', 'gdhh', 'gdju', 'gdtm', 'gent', 'gets', 'gfd', 'ggg', 'gne', 'gtal', 'gtj', 'gun', 'gvg',

    'har', 'havd', 'hawa', 'hbad', 'hdi', 'hdka', 'herr', 'hiz', 'hjmo', 'hmgl', 'hmpd', 'hnd', 'hndb', 'hnds', 'hntv', 'hodv', 'homa', 'honb', 'hrrb', 'hunt', 'hunta', 'husr', 'hzgd',

    'ibw', 'id', 'idbd', 'iene', 'iesp', 'inct', 'inu', 'ipsd', 'iptd', 'ipx', 'ipz',

    'jag', 'jan', 'jks', 'jmty', 'juc', 'jufd', 'jux', 'juy',

    'kagp', 'kane', 'kawd', 'kbi', 'kdg', 'kdkj', 'kibd', 'kird', 'km', 'kmhr', 'ksbj', 'ksdo', 'ktds',
    'ktkc', 'ktkl', 'ktkp', 'ktkq', 'ktkx', 'ktkz', 'ktr', 'ktra', 'kwbd', 'kws', 'kwsd',

    'lad', 'laf', 'lafbd', 'lid', 'lid03', 'lod', 'lol', 'love', 'lxvs', 'lzpl',

    'madm', 'magn', 'mann', 'maraa', 'mas', 'maxa', 'mcsr', 'mct', 'mdar', 'mdb', 'mds', 'mdtm', 'mdyd',
    'mdym', 'mei', 'meyd', 'mgt', 'miad', 'miae', 'mibd', 'midd', 'mide', 'mifd', 'migd', 'mird', 'mism',
    'mist', 'mium', 'mizd', 'mkbd', 'mkd', 'mkmp', 'mmgh', 'mmkz', 'mmna', 'mmnd', 'mmts', 'mmus', 'mmxd',
    'moc', 'momj', 'mrxd', 'mudr', 'mukd', 'mum', 'mvsd', 'mxgs', 'mxsps',

    'nacr', 'nacs', 'nafi', 'naka', 'nanx', 'nass', 'natr', 'ngod', 'nhdta', 'nhdtb', 'nise', 'nkkd', 'nks',
    'nnf', 'nnpj', 'npv', 'nsr', 'nttr',

    'ofje', 'ogpp', 'okad', 'oksn', 'once', 'oned', 'onet', 'onez', 'ongp', 'onsd', 'opud', 'oyc', 'oyj',
    'parm', 'pat', 'pgd', 'piyo', 'pjd', 'pk', 'pkpd', 'pla', 'post', 'pppd', 'pps', 'ppt', 'pred', 'prou', 'prtd', 'pt', 'ptko', 'ptks', 'pxh',
    'qp',

    'r18', 'raw', 'rbd', 'rct', 'rctd', 'rdd', 'rdt', 'real', 'rebdb', 'red', 'rega', 'rhj', 'rki', 'rtp',

    'saba', 'sace', 'sama', 'scop', 'scpx', 'sdab', 'sdde', 'sden', 'sdiy', 'sdmu', 'sdnm', 'sdsi', 'sero',
    'sfba', 'sga', 'shic', 'shkd', 'shx', 'siro', 'sis', 'siv', 'sl', 'smdv', 'smile', 'snis', 'soav', 'soe',
    'sprd', 'spz', 'sqte', 'srs', 'srxv', 'ssni', 'sspd', 'star', 'stss', 'suji', 'supa', 'supd', 'svdvd', 'sw', 'sy',

    't28', 'tbl', 'team', 'tek', 'tem', 'temp', 'tikb', 'tikc', 'tikm', 'tikp', 'tki', 'tmcy', 'tmem', 'tmhp', 'tmvi',
    'tokyo', 'tomn', 'tppn', 'tre', 'trp', 'trum', 'tus', 'tyod',

    'uby', 'umd', 'umso', 'upsm', 'urlh',

    'vdd', 'vec', 'venu', 'vgd', 'vicd', 'voss', 'vrtm', 'vvp',

    'wanz', 'whx', 'wkd', 'www',

    'xrw', 'xv', 'xvsr',

    'yal', 'ymdd', 'yrh', 'yst',

    'zex', 'zizg', 'zuko']


if __name__ == '__main__':

    torrent = {
        'name': 'Milena.Velba.Milena.Velba.Hitomi.Tanaka.Okita.Anri.Language.School.720p.mp4',
        'files': [
            {
                'path': 'Milena.Velba.feat.Hitomi.Tanaka.Okita.Anri.Language.School.2016.11.29.mp4',
                'length': 902218271
            },
            {
                'path': 'RARBG.com.txt',
                'length': 33
            },
            {
                'path': 'poster.jpg',
                'length': 35504
            },
            {
                'path': 'screens.jpg',
                'length': 317734
            }
        ]
    }

    print(guess_metainfo(torrent))

    test2 = {"name": "[ishikawaemi_]_zekkyou_gakkyuu_tenshou_1-3.rar", "length": 161149609}
    print(guess_metainfo(test2))

    filename = 'Tizon, Hector - Cuentos completos [28577] (r1.0).epub'
    print(guess_file('[ishikawaemi_]_zekkyou_gakkyuu_tenshou_1-3.rar'))

    typ = None
    mime = mimetypes.guess_type(filename, strict=False)[0]
    print('mime ', mime)
    if mime:
        typ = mime_to_category(mime)
        print(typ)
    if typ is None:
        ext = os.path.splitext(filename)[1].lower()
        if ext:
            typ = extension_to_category(ext)

    print(typ)