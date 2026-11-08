"""
OCR Engine Manager for Email Crunch.
Manages modular open-source and OS-native OCR engines:
- Windows Native OCR (Windows.Media.Ocr / winocr)
- RapidOCR (PaddleOCR models with ONNX Runtime, Apache-2.0)
- Tesseract OCR (Google / UB-Mannheim, Apache-2.0)
- EasyOCR (JaidedAI / PyTorch, Apache-2.0)

Handles cross-platform fallbacks (Windows, macOS, Linux).
"""

import os
import sys
import io
import asyncio
from typing import List, Set, Dict, Optional
from pathlib import Path

from engine.email_utils import (
    extract_emails_from_text,
    clean_candidate_email,
    load_user_config
)

# PIL / Pillow
try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

# 1. Windows Native Media.Ocr (built-in Windows 10/11)
_HAS_WINOCR = False
if sys.platform == 'win32':
    try:
        import winocr
        _HAS_WINOCR = True
    except Exception:
        _HAS_WINOCR = False

# 2. RapidOCR (RapidAI on GitHub, Apache-2.0, ONNX) - Primary cross-platform engine
try:
    from rapidocr_onnxruntime import RapidOCR
    _rapidocr_engine = RapidOCR()
    _HAS_RAPIDOCR = True
except Exception:
    _rapidocr_engine = None
    _HAS_RAPIDOCR = False

# 3. Tesseract OCR (Google / UB-Mannheim on GitHub)
try:
    import pytesseract
    _HAS_TESSERACT = True
except Exception:
    pytesseract = None
    _HAS_TESSERACT = False

# 4. EasyOCR (JaidedAI on GitHub, PyTorch)
try:
    import easyocr
    _HAS_EASYOCR = True
except Exception:
    easyocr = None
    _HAS_EASYOCR = False


# Supported OCR Engines metadata and download sources
OCR_ENGINES_INFO = {
    "windows_native": {
        "name": "Windows Native OCR (Windows.Media.Ocr)",
        "type": "Built-in OS Engine",
        "description": "Native Windows 10/11 C++ OCR runtime. 100% offline, highly accurate, requires zero external binaries.",
        "license": "Proprietary Windows Component (Free / Built-in)",
        "github": "https://github.com/microsoft/Windows-Universal-Samples",
        "pip_package": "winocr",
        "available": _HAS_WINOCR,
        "platform_supported": sys.platform == 'win32'
    },
    "rapidocr": {
        "name": "RapidOCR (ONNX / Open Source)",
        "type": "Neural ONNX Multi-threaded",
        "description": "Ultra-fast open-source OCR based on PaddleOCR models with ONNX Runtime. Cross-platform, multi-threaded, and low footprint.",
        "license": "Apache-2.0 (Open Source)",
        "github": "https://github.com/RapidAI/RapidOCR",
        "pip_package": "rapidocr-onnxruntime",
        "available": _HAS_RAPIDOCR,
        "platform_supported": True
    },
    "tesseract": {
        "name": "Tesseract OCR (Google / UB-Mannheim)",
        "type": "Traditional Open Source OCR",
        "description": "The classic, battle-tested open-source OCR engine. Cross-platform with support for 100+ languages.",
        "license": "Apache-2.0 (Open Source)",
        "github": "https://github.com/tesseract-ocr/tesseract",
        "windows_installer": "https://github.com/UB-Mannheim/tesseract/wiki",
        "pip_package": "pytesseract",
        "available": _HAS_TESSERACT,
        "platform_supported": True
    },
    "easyocr": {
        "name": "EasyOCR (JaidedAI / PyTorch)",
        "type": "Deep Learning PyTorch OCR",
        "description": "Ready-to-use OCR with 80+ supported languages and all popular writing scripts.",
        "license": "Apache-2.0 (Open Source)",
        "github": "https://github.com/JaidedAI/EasyOCR",
        "pip_package": "easyocr",
        "available": _HAS_EASYOCR,
        "platform_supported": True
    }
}

# Determine default engine based on platform and availability
def _get_default_engine_key() -> str:
    if sys.platform == 'win32' and _HAS_WINOCR:
        return "windows_native"
    if _HAS_RAPIDOCR:
        return "rapidocr"
    if _HAS_TESSERACT:
        return "tesseract"
    if _HAS_EASYOCR:
        return "easyocr"
    return "rapidocr"

# Active settings
_cfg = load_user_config()
_saved_engine = _cfg.get("active_ocr_engine")
if _saved_engine and _saved_engine in OCR_ENGINES_INFO:
    _active_ocr_engine_key = _saved_engine
else:
    _active_ocr_engine_key = _get_default_engine_key()

_hardware_acceleration = _cfg.get("hardware_acceleration", True)


def set_hardware_acceleration(enabled: bool):
    """Toggles hardware acceleration mode."""
    global _hardware_acceleration
    _hardware_acceleration = enabled


def is_hardware_acceleration_enabled() -> bool:
    """Checks if hardware acceleration is enabled."""
    return _hardware_acceleration


def set_active_ocr_engine(engine_key: str):
    """Sets the active OCR engine to use for image and scanned PDF parsing."""
    global _active_ocr_engine_key
    if engine_key in OCR_ENGINES_INFO:
        _active_ocr_engine_key = engine_key


def get_active_ocr_engine() -> str:
    """Gets the active OCR engine key."""
    return _active_ocr_engine_key


def get_ocr_engines_status() -> Dict[str, Dict]:
    """Returns status and metadata for all supported open-source OCR engines."""
    OCR_ENGINES_INFO["windows_native"]["available"] = _HAS_WINOCR
    OCR_ENGINES_INFO["rapidocr"]["available"] = _HAS_RAPIDOCR
    OCR_ENGINES_INFO["tesseract"]["available"] = _HAS_TESSERACT
    OCR_ENGINES_INFO["easyocr"]["available"] = _HAS_EASYOCR
    return OCR_ENGINES_INFO


def run_ocr_on_bytes(img_bytes: bytes) -> List[str]:
    """
    Executes OCR on raw image bytes using the user's selected OCR engine
    with fallback logic.
    """
    if not img_bytes:
        return []

    engine = _active_ocr_engine_key
    emails: Set[str] = set()

    # 1. Windows Native OCR (Windows only)
    if engine == "windows_native" and _HAS_WINOCR and sys.platform == 'win32' and PILImage is not None:
        try:
            image = PILImage.open(io.BytesIO(img_bytes))
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(winocr.recognize_pil(image, lang='en'))
            loop.close()
            if result and result.text:
                emails.update(extract_emails_from_text(result.text))
            if emails:
                return list(emails)
        except Exception:
            pass  # Fall through to RapidOCR fallback

    # 2. RapidOCR (ONNX) - Cross-platform
    if (engine == "rapidocr" or not emails) and _HAS_RAPIDOCR and _rapidocr_engine is not None:
        try:
            ocr_result, _ = _rapidocr_engine(img_bytes)
            if ocr_result:
                all_text = " ".join([line[1] for line in ocr_result if len(line) > 1])
                emails.update(extract_emails_from_text(all_text))
            if emails:
                return list(emails)
        except Exception:
            pass

    # 3. Tesseract OCR - Cross-platform
    if (engine == "tesseract" or not emails) and _HAS_TESSERACT and pytesseract is not None and PILImage is not None:
        try:
            image = PILImage.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(image)
            emails.update(extract_emails_from_text(text))
            if emails:
                return list(emails)
        except Exception:
            pass

    return list(emails)


def run_ocr_on_image(file_path: str) -> List[str]:
    """Runs OCR on image files (.png, .jpg, .jpeg, .tiff, .bmp, .webp)."""
    with open(file_path, 'rb') as f:
        data = f.read()
    return run_ocr_on_bytes(data)

