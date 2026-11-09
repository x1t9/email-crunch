# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path('.').resolve())],
    binaries=[],
    datas=[
        ('engine/parsers/', 'engine/parsers/'),
        ('config.json', '.'),
    ],
    hiddenimports=[
        'engine.parsers',
        'engine.parsers.base_parser',
        'engine.parsers.doc_parser',
        'engine.parsers.spreadsheet_parser',
        'engine.parsers.presentation_parser',
        'engine.parsers.pdf_parser',
        'engine.parsers.plaintext_parser',
        'engine.parsers.ebook_parser',
        'engine.parsers.iwork_parser',
        'engine.parsers.image_parser',
        'engine.ocr_manager',
        'engine.email_utils',
        'engine.worker',
        'engine.output_manager',
        'rapidocr_onnxruntime',
        'onnxruntime',
        'PIL',
        'chardet',
        'olefile',
        'psutil',
        'pymupdf',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['easyocr', 'torch', 'torchvision'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='EmailCrunch',
    debug=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False,
    upx=True,
    name='EmailCrunch',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='EmailCrunch.app',
        bundle_identifier='com.emailcrunch.app',
        info_plist={
            'CFBundleShortVersionString': '0.1-alpha',
            'NSHighResolutionCapable': True,
        },
    )
