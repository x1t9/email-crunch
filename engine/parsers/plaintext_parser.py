"""
=============================================================================
PLAIN TEXT & MARKUP PARSER - Streaming Buffer Text Engine
Supported Formats: .txt, .md, .tex, .html, .htm, .mhtml, .mht, .xml, .json, .log, .eml
=============================================================================
High-performance streaming plain text and markup parser.
- Multi-tier encoding detection: Fast UTF-8 -> chardet sample -> Latin-1 fallback
- Handles structured markup (.html, .mhtml, .xml, .json)
- Direct email extraction from logs and email files (.log, .eml)
"""

import os
from typing import List, Optional, Callable

from engine.parsers.base_parser import BaseParser
from engine.email_utils import extract_emails_from_text

try:
    import chardet
except ImportError:
    chardet = None


class PlainTextParser(BaseParser):
    """
    Parser for plain text, markup, logs, and email messages.
    """
    SUPPORTED_EXTENSIONS = {
        '.txt', '.md', '.tex', '.html', '.htm',
        '.mhtml', '.mht', '.xml', '.json', '.log', '.eml'
    }
    PARSER_NAME = "Plain Text & Markup Parser"
    PARSER_DESCRIPTION = "High-speed text streaming parser with adaptive encoding detection"

    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        with open(file_path, 'rb') as f:
            raw = f.read()

        if not raw:
            return []

        # 1. Fast UTF-8
        try:
            text = raw.decode('utf-8')
            return extract_emails_from_text(text)
        except UnicodeDecodeError:
            pass

        # 2. chardet detection fallback
        detected_encoding = None
        if chardet is not None:
            try:
                res = chardet.detect(raw[:50000])
                detected_encoding = res.get('encoding')
            except Exception:
                detected_encoding = None

        if detected_encoding:
            try:
                text = raw.decode(detected_encoding, errors='ignore')
                return extract_emails_from_text(text)
            except Exception:
                pass

        # 3. Latin-1 / ASCII safe fallback
        text = raw.decode('latin-1', errors='ignore')
        return extract_emails_from_text(text)
