# Email Crunch

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/version-0.1--alpha-green.svg)](https://github.com/x1t9/email-crunch/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)]()

**Email Crunch** is an ultra-fast, cross-platform desktop application designed for bulk document parsing and email harvesting across Windows, macOS, and Linux. Built with **PySide6 (Qt)** and an asynchronous, modular extraction architecture, Email Crunch processes thousands of mixed-format files per minute without consuming excess CPU or RAM.

---

## Key Features

- **Segregated Format Parsers**: Format-specific parsers in `engine/parsers/` with automatic discovery.
- **Pluggable Parser Architecture**: Add support for any custom document format simply by dropping a new Python file into the parsers folder.
- **Ultra-Fast Stream & Zip Parsing**: Direct raw XML stream reads for Office OpenXML formats (`.docx`, `.xlsx`, `.pptx`, `.odt`, `.ods`, `.odp`, `.epub`) — up to 10× faster than heavy DOM tree parsers.
- **C-Backed PDF Engine**: Instant text and link extraction via PyMuPDF (`fitz`), with automatic neural OCR fallback for scanned pages.
- **Modular Open-Source OCR**: Zero-telemetry, offline OCR engines (Windows Native Media.Ocr, RapidOCR with ONNX Runtime, Tesseract OCR, and EasyOCR).
- **Dry Run Mode**: Test extraction batches and preview domain share statistics without altering any files or writing exports.
- **Configurable Regex Engine**: Switch between 5 pre-made pattern presets or define and live-test custom regular expressions.
- **Intelligent Resource Management**: Auto-throttling worker pool dynamically caps CPU utilization at ~80% (`max(1, int(cpu_count * 0.80))`).
- **Flexible Export & Splitting**: Auto-split large CSV outputs (default: 20,000 rows per chunk) with global deduplication.
- **Source Post-Processing**: Automatically keep, rename, move to an archive folder, or delete source files upon completion.
- **Professional Flat Interface**: Clean corporate styling with full Dark and Light theme consistency.

---

## Supported File Formats

| Category | Extensions | Underlying Engine |
| :--- | :--- | :--- |
| **Documents** | `.docx`, `.doc`, `.odt`, `.rtf` | Direct zipfile XML stream / olefile binary scrape |
| **Spreadsheets** | `.xlsx`, `.xls`, `.ods`, `.csv`, `.tsv` | Shared strings XML scanner / olefile / text stream |
| **Presentations** | `.pptx`, `.ppt`, `.odp` | Slide XML scanner / olefile binary scrape |
| **PDF** | `.pdf` | PyMuPDF (fitz) + OCR scanned-page fallback |
| **Text & Markup** | `.txt`, `.md`, `.tex`, `.html`, `.htm`, `.mhtml`, `.mht`, `.xml`, `.json`, `.log`, `.eml` | Fast UTF-8 / chardet / Latin-1 buffer stream |
| **E-Books** | `.epub` | Container zipfile XML / HTML parsing |
| **Apple iWork** | `.pages`, `.numbers`, `.key` | Container metadata & preview stream scanner |
| **Images (OCR)** | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp`, `.webp` | RapidOCR (ONNX) / Windows Native / Tesseract |

---

## Modular Architecture & Adding Custom Parsers

Email Crunch uses a decoupled architecture where document parsers are segregated by format inside the `engine/parsers/` directory:

```
email-crunch/
├── engine/
│   ├── parsers/
│   │   ├── __init__.py            # Auto-discovery & dynamic extension router
│   │   ├── base_parser.py         # Abstract BaseParser interface
│   │   ├── doc_parser.py          # .docx, .doc, .odt, .rtf
│   │   ├── spreadsheet_parser.py  # .xlsx, .xls, .ods, .csv, .tsv
│   │   ├── presentation_parser.py # .pptx, .ppt, .odp
│   │   ├── pdf_parser.py          # .pdf
│   │   ├── plaintext_parser.py    # .txt, .md, .html, .mhtml, .eml, etc.
│   │   ├── ebook_parser.py        # .epub
│   │   ├── iwork_parser.py        # .pages, .numbers, .key
│   │   └── image_parser.py        # .png, .jpg, .tiff, .bmp, .webp (OCR)
│   ├── ocr_manager.py             # OCR engine selection & execution
│   ├── output_manager.py          # CSV writer, auto-splitting & deduplication
│   ├── email_utils.py             # Regex presets, validation & normalization
│   └── worker.py                  # QThreadPool concurrency & throttling
├── ui/                            # PySide6 desktop interface
├── build.py                       # Cross-platform PyInstaller builder
├── run.bat                        # Windows launcher
├── run.sh                         # Linux/macOS launcher
└── test_app.py                    # Unit tests
```

### How to Add a Custom Parser in 3 Steps

You can add support for new formats without editing any core application code:

1. Create a new Python file in `engine/parsers/` (or in a `parsers/` folder next to the app executable), e.g. `engine/parsers/markdown_archive_parser.py`.
2. Inherit from `BaseParser` and declare your `SUPPORTED_EXTENSIONS`.
3. Implement the `parse()` method:

```python
"""
CUSTOM PARSER EXAMPLE
Supported Formats: .myext, .archive
"""
from typing import List, Optional, Callable
from engine.parsers.base_parser import BaseParser
from engine.email_utils import extract_emails_from_text

class CustomArchiveParser(BaseParser):
    SUPPORTED_EXTENSIONS = {'.myext', '.archive'}
    PARSER_NAME = "Custom Archive Parser"
    PARSER_DESCRIPTION = "Extracts emails from custom proprietary formats"

    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return extract_emails_from_text(content)
```

Email Crunch automatically discovers, registers, and routes files with `.myext` and `.archive` extensions on the next launch!

---

## Installation & Running from Source

### Prerequisites

- **Python 3.10, 3.11, or 3.12**
- `pip` package manager

### 1. Clone the Repository
```bash
git clone https://github.com/x1t9/email-crunch.git
cd email-crunch
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application

- **Windows**:
  Double-click `run.bat` or run:
  ```powershell
  python main.py
  ```

- **Linux & macOS**:
  Make launcher executable and run:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

---

## Building Standalone Binaries

Email Crunch includes a cross-platform build script using PyInstaller:

```bash
python build.py
```

The resulting standalone executable will be generated inside the `dist/` directory:
- **Windows**: `dist/EmailCrunch/EmailCrunch.exe`
- **macOS**: `dist/EmailCrunch/EmailCrunch.app`
- **Linux**: `dist/EmailCrunch/EmailCrunch`

Pre-compiled binaries for Windows, macOS, and Linux are automatically built and released on GitHub Releases via GitHub Actions.

---

## Running Automated Tests

Run the comprehensive unit test suite:

```bash
python test_app.py
```

All 13 tests verify:
- Pre-made regex matching and normalization
- Document, spreadsheet, presentation, and PDF parsers
- Parser auto-discovery and dynamic third-party drop-in registration
- Multi-core CPU throttling calculation
- CSV chunked auto-splitting and global deduplication
- GUI instantiation and thread pool lifecycle

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
