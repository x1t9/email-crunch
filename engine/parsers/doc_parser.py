"""
=============================================================================
DOCUMENT PARSER - Word & OpenDocument Processing Engine
Supported Formats: .docx, .doc, .odt, .rtf
=============================================================================
High-speed extraction for Microsoft Word (.docx, .doc), OpenDocument Text
(.odt), and Rich Text Format (.rtf).
- .docx & .odt: Raw zipfile XML streaming (up to 10x faster than DOM parsers)
- .doc: Binary stream text scraping via olefile / raw string extraction
- .rtf: Fast streaming text decode
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


class DocumentParser(BaseParser):
    """
    Parser for Word (.docx, .doc), OpenDocument (.odt), and RTF (.rtf) documents.
    """
    SUPPORTED_EXTENSIONS = {'.docx', '.doc', '.odt', '.rtf'}
    PARSER_NAME = "Word & OpenDocument Parser"
    PARSER_DESCRIPTION = "High-speed parser for .docx, .doc, .odt, and .rtf files"

    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.docx':
            return self._parse_docx(file_path)
        elif ext == '.odt':
            return self._parse_odt(file_path)
        elif ext == '.doc':
            return self._parse_legacy_doc(file_path)
        elif ext == '.rtf':
            return self._parse_rtf(file_path)
        return []

    def _parse_docx(self, file_path: str) -> List[str]:
        """Extract emails from .docx by scanning word/ XML streams."""
        filters = [
            'word/document.xml', 'word/footnotes.xml', 'word/endnotes.xml',
            'word/comments.xml', 'word/header', 'word/footer'
        ]
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
            # Fallback to scanning all XML files in zip
            emails.update(self._scan_all_zip_xml(file_path))
        return list(emails)

    def _parse_odt(self, file_path: str) -> List[str]:
        """Extract emails from OpenDocument Text (.odt)."""
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

    def _parse_legacy_doc(self, file_path: str) -> List[str]:
        """Extract text from legacy binary Office document (.doc)."""
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

        # Raw binary scanning fallback
        try:
            with open(file_path, 'rb') as f:
                emails.update(extract_emails_from_bytes(f.read()))
        except Exception:
            pass
        return list(emails)

    def _parse_rtf(self, file_path: str) -> List[str]:
        """Reads Rich Text Format (.rtf)."""
        try:
            with open(file_path, 'rb') as f:
                raw = f.read()
            return extract_emails_from_bytes(raw)
        except Exception:
            return []

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
