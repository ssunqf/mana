#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import itertools

# https://fileinfo.com/filetypes/common

text_types = [
    'DOC',  # Microsoft Word Document
    'DOCX',  # Microsoft Word Open XML Document
    'LOG',  # Log File
    'MSG',  # Outlook Mail Message
    'ODT',  # OpenDocument Text Document
    'PAGES',  # Pages Document
    'RTF',  # Rich Text Format File
    'TEX',  # LaTeX Source Document
    'TXT',  # Plain Text File
    'WPD',  # WordPerfect Document
    'WPS'  # Microsoft Works Word Processor Document
]

data_types = [
    'CSV',  # Comma Separated Values File
    'DAT',  # Data File
    'GED',  # GEDCOM Genealogy Data File
    'KEY',  # Keynote Presentation
    'KEYCHAIN',  # Mac OS X Keychain File
    'PPS',  # PowerPoint Slide Show
    'PPT',  # PowerPoint Presentation
    'PPTX',  # PowerPoint Open XML Presentation
    'SDF',  # Standard Data File
    'TAR',  # Consolidated Unix File Archive
    'TAX2016',  # TurboTax 2016 Tax Return
    'TAX2018',  # TurboTax 2018 Tax Return
    'VCF',  # vCard File
    'XML'  # XML File
]

audio_types = [
    'AIF',	#Audio Interchange File Format
    'IFF',	#Interchange File Format
    'M3U',	#Media Playlist File
    'M4A',	#MPEG-4 Audio File
    'MID',	#MIDI File
    'MP3',	#MP3 Audio File
    'MPA',	#MPEG-2 Audio File
    'WAV',	#WAVE Audio File
    'WMA',	#Windows Media Audio File
]

vedio_types = [
    '3G2',	#3GPP2 Multimedia File
    '3GP',	#3GPP Multimedia File
    'ASF',	#Advanced Systems Format File
    'AVI',	#Audio Video Interleave File
    'FLV',	#Flash Video File
    'M4V',	#iTunes Video File
    'MOV',	#Apple QuickTime Movie
    'MP4',	#MPEG-4 Video File
    'MPG',	#MPEG Video File
    'RM',	#RealMedia File
    'SRT',	#SubRip Subtitle File
    'SWF',	#Shockwave Flash Movie
    'VOB',	#DVD Video Object File
    'WMV',	#Windows Media Video File
]


ebook_types = [
    'ACSM',	#Adobe Content Server Message File
    'AEP',	#Activ E-Book Project
    'APNX',	#Amazon Page Number Index File
    'AVA',	#AvaaBook eBook
    'AZW',	#Amazon Kindle eBook File
    'AZW1',	#Amazon Topaz eBook
    'AZW3',	#Amazon KF8 eBook File
    'AZW4',	#Amazon Print Replica eBook
    'BKK',	#BookBuddi eBook File
    'BPNUEB',	#PNU eBook File
    'CBC',	#Comic Book Collection
    'CEB',	#Apabi eBook File
    'CEBX',	#Apabi XML eBook File
    'DNL',	#DNAML eBook File
    'EA',	#Kindle End Actions File
    'EAL',	#Kindle End Actions File
    'EBK',	#eBook Pro eBook File
    'EDN',	#Adobe eBook Activation File
    'EPUB',	#Open eBook File
    'ETD',	#Adobe Reader EBX Transfer Data File
    'FB2',	#FictionBook 2.0 File
    'FKB',	#Flipkart eBook File
    'HAN',	#Amazon Kindle eBook Data File
    'HTML0',	#Book Designer File
    'HTMLZ',	#Zipped HTML eBook
    'HTXT',	#Hanvon eBook File
    'HTZ4',	#HyperMaker 4 Publication
    'HTZ5',	#HyperMaker 5 Publication
    'IBOOKS',	#Multi-Touch iBook
    'KFX',	#Amazon KF10 eBook File
    'KOOB',	#Koob E-Book File
    'LIT',	#eBook File
    'LRF',	#Sony Portable Reader File
    'LRS',	#Librie Reader Source File
    'LRX',	#Sony Portable Reader File
    'MART',	#MartView eBook File
    'MBP',	#Mobipocket Notes File
    'MOBI',	#Mobipocket eBook
    'NCX',	#EPUB Navigation Control XML File
    'NVA',	#NVA Document
    'OEB',	#Open eBook File
    'OEBZIP',	#Zipped Open eBook File
    'OPF',	#Open Packaging Format File
    'ORB',	#Original eBook Reader File
    'PEF',	#PEF Braille Book File
    'PHL',	#Kindle Popular Highlights File
    'PML',	#Palm Markup Language File
    'PMLZ',	#Zipped Palm Markup Language File
    'POBI',	#Kindle Touch Periodical File
    'PRC',	#Mobipocket eBook File
    'QMK',	#YanCEyDesktop Quickmarks File
    'RZB',	#Red Zion Book File
    'RZS',	#Red Zion Security File
    'SNB',	#Shanda Bambook eBook
    'TCR',	#Psion Series 3 eBook File
    'TK3',	#TK3 Multimedia eBook
    'TPZ',	#Kindle Topaz eBook File
    'TR',	#TomeRaider 2 eBook File
    'TR3',	#TomeRaider eBook File
    'VBK',	#VitalSource eBook
    'WEBZ',	#WEBZ Compressed eBook File
    'YBK',	#YanCEyWare eBook

]
image_3d_types = [
    '3DM',	#Rhino 3D Model
    '3DS',	#3D Studio Scene
    'MAX',	#3ds Max Scene File
    'OBJ',	#Wavefront 3D Object File
]

image_2d_types = [
    'BMP',	#Bitmap Image File
    'DDS',	#DirectDraw Surface
    'GIF',	#Graphical Interchange Format File
    'HEIC',	#High Efficiency Image Format
    'JPG',	#JPEG Image
    'PNG',	#Portable Network Graphic
    'PSD',	#Adobe Photoshop Document
    'PSPIMAGE',	#PaintShop Pro Image
    'TGA',	#Targa Graphic
    'THM',	#Thumbnail Image File
    'TIF',	#Tagged Image File
    'TIFF',	#Tagged Image File Format
    'YUV',	#YUV Encoded Image File
]

image_vector_types = [
    'AI',	#Adobe Illustrator File
    'EPS',	#Encapsulated PostScript File
    'SVG',	#Scalable Vector Graphics File
]

page_layout_types = [
    'INDD',	#Adobe InDesign Document
    'PCT',	#Picture File
    'PDF',	#Portable Document Format File
]

spreadsheet_types = [
    'XLR',	#Works Spreadsheet
    'XLS',	#Excel Spreadsheet
    'XLSX',	#Microsoft Excel Open XML Spreadsheet
]

datebase_types = [
    'ACCDB',	#Access 2007 Database File
    'DB',	#Database File
    'DBF',	#Database File
    'MDB',	#Microsoft Access Database
    'PDB',	#Program Database
    'SQL',	#Structured Query Language Data File
]

executable_types = [
    'APK',	#Android Package File
    'APP',	#macOS Application
    'BAT',	#DOS Batch File
    'CGI',	#Common Gateway Interface Script
    'COM',	#DOS Command File
    'EXE',	#Windows Executable File
    'GADGET',	#Windows Gadget
    'JAR',	#Java Archive File
    'WSF',	#Windows Script File
]

game_types = [
    'B',	#Grand Theft Auto 3 Saved Game File
    'DEM',	#Video Game Demo File
    'GAM',	#Saved Game File
    'NES',	#Nintendo (NES) ROM File
    'ROM',	#N64 Game ROM File
    'SAV',	#Saved Game
]

cad_types = [
    'DWG',	#AutoCAD Drawing Database File
    'DXF',	#Drawing Exchange Format File
]

gis_types = [
    'GPX',	#GPS Exchange File
    'KML',	#Keyhole Markup Language File
    'KMZ',	#Google Earth Placemark File
]

web_types = [
    'ASP',	#Active Server Page
    'ASPX',	#Active Server Page Extended File
    'CER',	#Internet Security Certificate
    'CFM',	#ColdFusion Markup File
    'CSR',	#Certificate Signing Request File
    'CSS',	#Cascading Style Sheet
    'DCR',	#Shockwave Media File
    'HTM',	#Hypertext Markup Language File
    'HTML',	#Hypertext Markup Language File
    'JS',	#JavaScript File
    'JSP',	#Java Server Page
    'PHP',	#PHP Source Code File
    'RSS',	#Rich Site Summary
    'XHTML',	#Extensible Hypertext Markup Language File

]

plugin_types = [
    'CRX',	#Chrome Extension
    'PLUGIN',	#Mac OS X Plugin
]

font_types = [
    'FNT',	#Windows Font File
    'FON',	#Generic Font File
    'OTF',	#OpenType Font
    'TTF',	#TrueType Font
]


system_types = [
    'CAB',	#Windows Cabinet File
    'CPL',	#Windows Control Panel Item
    'CUR',	#Windows Cursor
    'DESKTHEMEPACK',	#Windows 8 Desktop Theme Pack File
    'DLL',	#Dynamic Link Library
    'DMP',	#Windows Memory Dump
    'DRV',	#Device Driver
    'ICNS',	#macOS Icon Resource File
    'ICO',	#Icon File
    'LNK',	#Windows File Shortcut
    'SYS',	#Windows System File
]

setting_types = [
    'CFG',	#Configuration File
    'INI',	#Windows Initialization File
    'PRF',	#Outlook Profile File
]

encode_types = [
    'HQX',	#BinHex 4.0 Encoded File
    'MIM',	#Multi-Purpose Internet Mail Message File
    'UUE',	#Uuencoded File
]

compress_types = [
    '7Z',	#7-Zip Compressed File
    'CBR',	#Comic Book RAR Archive
    'DEB',	#Debian Software Package
    'GZ',	#Gnu Zipped Archive
    'PKG',	#Mac OS X Installer Package
    'RAR',	#WinRAR Compressed Archive
    'RPM',	#Red Hat Package Manager File
    'SITX',	#StuffIt X Archive
    'TAR.GZ', 	# Compressed Tarball File
    'ZIP',	#Zipped File
    'ZIPX',	#Extended Zip File
]

disk_image_types = [
    'BIN',	#Binary Disc Image
    'CUE',	#Cue Sheet File
    'DMG',	#Mac OS X Disk Image
    'ISO',	#Disc Image File
    'MDF',	#Media Disc Image File
    'TOAST',	#Toast Disc Image
    'VCD',	#Virtual CD
]

developer_types = [
    'C',	#C/C++ Source Code File
    'CLASS',	#Java Class File
    'CPP',	#C++ Source Code File
    'CS',	#C# Source Code File
    'DTD',	#Document Type Definition File
    'FLA',	#Adobe Animate Animation
    'H',	#C/C++/Objective-C Header File
    'JAVA',	#Java Source Code File
    'LUA',	#Lua Source File
    'M',	#Objective-C Implementation File
    'PL',	#Perl Script
    'PY',	#Python Script
    'SH',	#Bash Shell Script
    'SLN',	#Visual Studio Solution File
    'SWIFT',	#Swift Source Code File
    'VB',	#Visual Basic Project Item File
    'VCXPROJ',	#Visual C++ Project
    'XCODEPROJ',	#Xcode Project
]

backup_types = [
    'BAK',	#Backup File
    'TMP',	#Temporary File
]

misc_types = [
    'CRDOWNLOAD',	#Chrome Partially Downloaded File
    'ICS',	#Calendar File
    'MSI',	#Windows Installer Package
    'PART',	#Partially Downloaded File
    'TORRENT',	#BitTorrent File
]

file_pattern = '|'.join(itertools.chain(
    text_types, data_types, audio_types, vedio_types, ebook_types,
    image_3d_types, image_2d_types, image_vector_types,
    page_layout_types, spreadsheet_types, datebase_types,
    executable_types, game_types, cad_types, gis_types,
    web_types, plugin_types, font_types, system_types,
    setting_types, encode_types, compress_types, disk_image_types,
    developer_types, backup_types, misc_types))



def filter_path(metainfo):
    pattern = r'\b_____padding_file_'
