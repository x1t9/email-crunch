"""
=============================================================================
PRESENTATION PARSER - PowerPoint & OpenDocument Slide Engine
Supported Formats: .pptx, .ppt, .odp
=============================================================================
High-speed extraction for Microsoft PowerPoint (.pptx, .ppt) and
OpenDocument Presentation (.odp) slide decks.
- .pptx: Raw zipfile XML streaming through ppt/slides/, notes, comments
- .odp: Zipfile XML streaming through content.xml
- .ppt: Legacy binary stream scraping via olefile / raw string extraction
"""

import os
import zipfile
from typing import List, Set, Optional, Callable

from engine.parsers.base_parser import BaseParser
from engine.email_utils import (
    extract_emails_from_text,
    extract_emails_from_bytes
)

try:
    import olefile
except ImportError:
    olefile = None


class PresentationParser(BaseParser):
    """
    Parser for PowerPoint (.pptx, .ppt) and OpenDocument Presentation (.odp) files.
    """
    SUPPORTED_EXTENSIONS = {'.pptx', '.ppt', '.odp'}
    PARSER_NAME = "Presentation Parser"
    PARSER_DESCRIPTION = "High-speed parser for .pptx, .ppt, and .odp slide decks"

    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pptx':
            return self._parse_pptx(file_path)
        elif ext == '.odp':
            return self._parse_odp(file_path)
        elif ext == '.ppt':
            return self._parse_legacy_ppt(file_path)
        return []

    def _parse_pptx(self, file_path: str) -> List[str]:
        """Extract emails from .pptx by scanning slides, notes, and comments."""
        filters = ['ppt/slides/', 'ppt/notesslides/', 'ppt/comments']
        emails: Set[str] = set()
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                for name in z.namelist():
                    if any(p in name.lower() for p in filters):
                        try:
                            with z.open(name) as f:
                                emails.update(extract_emails_from_bytes(f.read()))
                        except Exception:
                            continue
        except Exception:
            emails.update(self._scan_all_zip_xml(file_path))
        return list(emails)

    def _parse_odp(self, file_path: str) -> List[str]:
        """Extract emails from OpenDocument Presentation (.odp)."""
        filters = ['content.xml', 'styles.xml', 'meta.xml']
        emails: Set[str] = set()
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                for name in z.namelist():
                    if any(p in name.lower() for p in filters):
                        try:
                            with z.open(name) as f:
                                emails.update(extract_emails_from_bytes(f.read()))
                        except Exception:
                            continue
        except Exception:
            emails.update(self._scan_all_zip_xml(file_path))
        return list(emails)

    def _parse_legacy_ppt(self, file_path: str) -> List[str]:
        """Extract text from legacy binary PowerPoint document (.ppt)."""
        emails: Set[str] = set()
        if olefile and olefile.isOleFile(file_path):
            try:
                ole = olefile.OleFileIO(file_path)
                for stream_name in ole.listdir():
                    try:
                        stream = ole.openstream(stream_name)
                        emails.update(extract_emails_from_bytes(stream.read()))
                    except Exception:
                        continue
                ole.close()
                if emails:
                    return list(emails)
            except Exception:
                pass

        try:
            with open(file_path, 'rb') as f:
                emails.update(extract_emails_from_bytes(f.read()))
        except Exception:
            pass
        return list(emails)

    def _scan_all_zip_xml(self, file_path: str) -> Set[str]:
        """Scans all XML entries inside a zipfile."""
        emails: Set[str] = set()
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                for name in z.namelist():
                    if name.lower().endswith('.xml'):
                        try:
                            with z.open(name) as f:
                                emails.update(extract_emails_from_bytes(f.read()))
                        except Exception:
                            continue
        except Exception:
            pass
        return emails
