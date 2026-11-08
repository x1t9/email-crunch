"""
=============================================================================
IMAGE & SCANNED OCR PARSER - Optical Character Recognition Engine
Supported Formats: .png, .jpg, .jpeg, .tiff, .tif, .bmp, .webp
=============================================================================
High-performance OCR image parsing.
Extracts emails from image files using the user-selected OCR engine:
- Windows Native OCR (Windows 10/11)
- RapidOCR (ONNX / Multi-threaded)
- Tesseract OCR
- EasyOCR (PyTorch)
"""

import os
from typing import List, Optional, Callable

from engine.parsers.base_parser import BaseParser
from engine.ocr_manager import run_ocr_on_image


class ImageOCRParser(BaseParser):
    """
    Parser for image files (.png, .jpg, .jpeg, .tiff, .tif, .bmp, .webp) via OCR.
    """
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp'}
    PARSER_NAME = "Image OCR Parser"
    PARSER_DESCRIPTION = "Neural & traditional OCR parsing for scanned documents and images"

    def parse(
        self,
        file_path: str,
        enable_ocr: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        if not enable_ocr:
            return []

        if progress_callback:
            progress_callback(25)

        emails = run_ocr_on_image(file_path)

        if progress_callback:
            progress_callback(100)

        return emails

