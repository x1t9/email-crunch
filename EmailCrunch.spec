# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:/samiru/code/email app/main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:/samiru/code/email app/engine/parsers', 'engine/parsers')],
    hiddenimports=['engine.parsers.base_parser', 'engine.parsers.doc_parser', 'engine.parsers.spreadsheet_parser', 'engine.parsers.presentation_parser', 'engine.parsers.pdf_parser', 'engine.parsers.plaintext_parser', 'engine.parsers.ebook_parser', 'engine.parsers.iwork_parser', 'engine.parsers.image_parser', 'engine.ocr_manager', 'rapidocr_onnxruntime', 'chardet', 'olefile', 'pymupdf', 'psutil', 'PIL', 'winocr'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EmailCrunch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EmailCrunch',
)
