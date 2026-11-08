"""
Base Parser Interface for Email Crunch.

All modular parsers in engine/parsers/ inherit from BaseParser.
To add a new document format parser to Email Crunch:
1. Create a new python file in engine/parsers/ (e.g., custom_archive_parser.py)
2. Subclass BaseParser and set SUPPORTED_EXTENSIONS
3. Implement parse(file_path, enable_ocr, progress_callback) -> List[str]
4. The application will automatically discover, register, and use your parser!
"""

from abc import ABC, abstractmethod
from typing import List, Set, Optional, Callable


class BaseParser(ABC):
    """
    Abstract base class for all file format parsers in Email Crunch.
    """
    # Set of lowercase extensions including leading dot (e.g. {'.docx', '.doc'})
    SUPPORTED_EXTENSIONS: Set[str] = set()

    # Human-readable parser name and description
    PARSER_NAME: str = "Base Parser"
    PARSER_DESCRIPTION: str = "Base format parser"

    @abstractmethod
    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        """
        Parses the document and extracts a list of email strings.

        Args:
            file_path: Absolute path to the document file.
            enable_ocr: Whether OCR fallback is enabled for scanned/image pages.
            progress_callback: Optional callback receiving integer percentage (0-100).

        Returns:
            List of unique extracted email addresses.
        """
        raise NotImplementedError
