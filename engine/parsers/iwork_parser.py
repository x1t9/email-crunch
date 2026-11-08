"""
=============================================================================
APPLE iWORK PARSER - Pages, Numbers & Keynote Engine
Supported Formats: .pages, .numbers, .key
=============================================================================
High-speed extraction for Apple iWork suite files:
- Pages documents (.pages)
- Numbers spreadsheets (.numbers)
- Keynote presentations (.key)
Unzips container to extract preview XML, index blobs, or direct binary streams.
"""

import os
import zipfile
from typing import List, Set, Optional, Callable

from engine.parsers.base_parser import BaseParser
from engine.email_utils import extract_emails_from_bytes


class IWorkParser(BaseParser):
    """
    Parser for Apple iWork suite files (.pages, .numbers, .key).
    """
    SUPPORTED_EXTENSIONS = {'.pages', '.numbers', '.key'}
    PARSER_NAME = "Apple iWork Suite Parser"
    PARSER_DESCRIPTION = "High-speed parser for .pages, .numbers, and .key documents"

    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        emails: Set[str] = set()

        # Try unzipping container
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                for name in z.namelist():
                    lower = name.lower()
                    # Skip media assets
                    if any(lower.endswith(img) for img in ['.jpg', '.jpeg', '.png', '.mp4', '.mov']):
                        continue
                    try:
                        with z.open(name) as entry:
                            emails.update(extract_emails_from_bytes(entry.read()))
                    except Exception:
                        continue
            if emails:
                return list(emails)
        except Exception:
            pass

        # Binary stream scan fallback
        try:
            with open(file_path, 'rb') as f:
                emails.update(extract_emails_from_bytes(f.read()))
        except Exception:
            pass

        return list(emails)
