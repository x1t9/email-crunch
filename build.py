"""
Cross-Platform Build Script for Email Crunch v0.1-alpha.
Generates standalone executables using PyInstaller:
- Windows: dist/EmailCrunch.exe
- macOS: dist/EmailCrunch.app
- Linux: dist/EmailCrunch

Run:
    python build.py
"""

import os
import sys
import subprocess
import shutil

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(APP_DIR, "main.py")
DIST_DIR = os.path.join(APP_DIR, "dist")
BUILD_DIR = os.path.join(APP_DIR, "build")

# Path separator for PyInstaller --add-data
SEP = ";" if sys.platform == "win32" else ":"

HIDDEN_IMPORTS = [
    "engine.parsers.base_parser",
    "engine.parsers.doc_parser",
    "engine.parsers.spreadsheet_parser",
    "engine.parsers.presentation_parser",
    "engine.parsers.pdf_parser",
    "engine.parsers.plaintext_parser",
    "engine.parsers.ebook_parser",
    "engine.parsers.iwork_parser",
    "engine.parsers.image_parser",
    "engine.ocr_manager",
    "rapidocr_onnxruntime",
    "chardet",
    "olefile",
    "pymupdf",
    "psutil",
    "PIL",
]

if sys.platform == "win32":
    HIDDEN_IMPORTS.append("winocr")


def clean():
    """Removes previous build artifacts."""
    for d in [BUILD_DIR, DIST_DIR]:
        if os.path.exists(d):
            print(f"Cleaning {d}...")
            shutil.rmtree(d, ignore_errors=True)


def build():
    print(f"Building Email Crunch v0.1-alpha for {sys.platform}...")
    clean()

    parsers_dir = os.path.join(APP_DIR, "engine", "parsers")
    data_arg = f"{parsers_dir}{SEP}engine/parsers"

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconsole",
        "--name", "EmailCrunch",
        "--onedir",
        "--clean",
        "--add-data", data_arg,
    ]

    for imp in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", imp])

    cmd.append(MAIN_PY)

    print("Executing command:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=APP_DIR)

    if result.returncode != 0:
        print(f"Build failed with code {result.returncode}")
        sys.exit(result.returncode)

    print("\n=======================================================")
    print("Build successful!")
    print(f"Output folder: {DIST_DIR}")
    print("=======================================================")


if __name__ == "__main__":
    build()

