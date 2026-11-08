"""
=============================================================================
E-BOOK PARSER - EPUB Electronic Publication Engine
Supported Formats: .epub
=============================================================================
High-speed extraction for electronic publications (.epub).
- Opens the EPUB container as a zip archive
- Extracts emails directly from (X)HTML chapters, OPF manifests, and text streams
- Avoids rendering overhead for maximum throughput
"""

import os
import zipfile
from typing import List, Set, Optional, Callable

from engine.parsers.base_parser import BaseParser
from engine.email_utils import extract_emails_from_bytes


class EBookParser(BaseParser):
    """
    Parser for EPUB e-books.
    """
    SUPPORTED_EXTENSIONS = {'.epub'}
    PARSER_NAME = "EPUB E-Book Parser"
    PARSER_DESCRIPTION = "High-speed parser for .epub e-books"

    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        filters = ['.html', '.xhtml', '.xml', '.opf', '.ncx', '.txt']
        emails: Set[str] = set()

        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                names = z.namelist()
                total = len(names)
                for idx, name in enumerate(names):
                    lower = name.lower()
                    if any(f in lower for f in filters):
                        try:
                            with z.open(name) as entry_file:
                                emails.update(extract_emails_from_bytes(entry_file.read()))
                        except Exception:
                            continue
                    if progress_callback and total > 0 and idx % 20 == 0:
                        progress_callback(int((idx + 1) / total * 100))
        except Exception:
            pass

        return list(emails)

