"""
=============================================================================
SPREADSHEET PARSER - Excel & OpenDocument Sheet Engine
Supported Formats: .xlsx, .xls, .ods, .csv, .tsv
=============================================================================
High-speed extraction for Microsoft Excel (.xlsx, .xls), OpenDocument
Spreadsheets (.ods), and delimited data (.csv, .tsv).
- .xlsx: Raw zipfile XML streaming through xl/sharedstrings.xml and worksheets
- .ods: Zipfile XML streaming through content.xml
- .xls: Legacy binary stream scraping via olefile / raw string extraction
- .csv & .tsv: Direct streaming text decoding
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


class SpreadsheetParser(BaseParser):
    """
    Parser for Excel (.xlsx, .xls), OpenDocument (.ods), and tabular (.csv, .tsv) files.
    """
    SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.ods', '.csv', '.tsv'}
    PARSER_NAME = "Spreadsheet & Tabular Parser"
    PARSER_DESCRIPTION = "High-speed parser for .xlsx, .xls, .ods, .csv, and .tsv files"

    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.xlsx':
            return self._parse_xlsx(file_path)
        elif ext == '.ods':
            return self._parse_ods(file_path)
        elif ext == '.xls':
            return self._parse_legacy_xls(file_path)
        elif ext in {'.csv', '.tsv'}:
            return self._parse_delimited(file_path)
        return []

    def _parse_xlsx(self, file_path: str) -> List[str]:
        """Extract emails from .xlsx by scanning sharedStrings, sheets, and comments."""
        filters = ['xl/sharedstrings.xml', 'xl/worksheets/', 'xl/comments']
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
            # Fallback scan all XML in zip
            emails.update(self._scan_all_zip_xml(file_path))
        return list(emails)

    def _parse_ods(self, file_path: str) -> List[str]:
        """Extract emails from OpenDocument Spreadsheet (.ods)."""
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

    def _parse_legacy_xls(self, file_path: str) -> List[str]:
        """Extract text from legacy binary Excel document (.xls)."""
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

    def _parse_delimited(self, file_path: str) -> List[str]:
        """Reads CSV / TSV text files with fallback encoding."""
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

