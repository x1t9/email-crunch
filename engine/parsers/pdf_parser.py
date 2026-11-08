"""
=============================================================================
PDF PARSER - High-Speed C-Engine & OCR PDF Extraction
Supported Formats: .pdf
=============================================================================
Ultra-fast PDF processing via PyMuPDF (fitz C-backed engine):
- Native text stream extraction per page
- Interactive link and mailto: URI extraction
- Optional neural OCR fallback for scanned pages with empty text streams
- Multi-threaded progress reporting
"""

import os
from typing import List, Set, Optional, Callable

from engine.parsers.base_parser import BaseParser
from engine.email_utils import (
    extract_emails_from_text,
    clean_candidate_email
)
from engine.ocr_manager import run_ocr_on_bytes

# PyMuPDF (fitz)
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class PDFParser(BaseParser):
    """
    High-speed PDF parser using PyMuPDF with optional OCR page fallback.
    """
    SUPPORTED_EXTENSIONS = {'.pdf'}
    PARSER_NAME = "PDF Document Parser"
    PARSER_DESCRIPTION = "High-speed C-backed PDF parsing via PyMuPDF with OCR fallback"

    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        if fitz is None:
            raise RuntimeError("PyMuPDF (fitz) is not installed. Run: pip install pymupdf")

        emails: Set[str] = set()
        doc = fitz.open(file_path)
        total_pages = len(doc)

        try:
            for idx in range(total_pages):
                page = doc[idx]
                text = page.get_text("text")

                # 1. Check for mailto: links in annotations
                try:
                    for link in page.get_links():
                        uri = link.get("uri", "")
                        if uri and "mailto:" in uri.lower():
                            valid = clean_candidate_email(uri)
                            if valid:
                                emails.add(valid)
                except Exception:
                    pass

                # 2. Extract emails from raw text stream
                extracted = extract_emails_from_text(text)
                emails.update(extracted)

                # 3. If text is empty/minimal and OCR enabled, run OCR on page pixmap
                if enable_ocr and len(extracted) == 0 and len(text.strip()) < 30:
                    try:
                        pix = page.get_pixmap(dpi=150)
                        page_ocr_emails = run_ocr_on_bytes(pix.tobytes("png"))
                        emails.update(page_ocr_emails)
                    except Exception:
                        pass

                if progress_callback and total_pages > 0:
                    progress_callback(int((idx + 1) / total_pages * 100))
        finally:
            doc.close()

        return list(emails)
