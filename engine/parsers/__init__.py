"""
=============================================================================
EMAIL CRUNCH - MODULAR PARSER ENGINE & AUTO-DISCOVERY SYSTEM
=============================================================================
Automatically discovers, inspects, and registers all document format parsers
located in the engine/parsers/ folder.

HOW TO ADD A NEW CUSTOM PARSER:
1. Create a Python file in engine/parsers/ (e.g. `engine/parsers/custom_markdown_parser.py`).
2. Subclass BaseParser, define SUPPORTED_EXTENSIONS = {'.xyz', '.abc'}.
3. Implement `parse(self, file_path, enable_ocr, progress_callback) -> List[str]`.
4. Drop it into this folder. Email Crunch will automatically detect, load,
   and route documents of that format on launch without changing any core code!
=============================================================================
"""

import os
import sys
import inspect
import importlib
from typing import Dict, List, Set, Tuple, Optional, Type

from engine.parsers.base_parser import BaseParser
from engine.ocr_manager import (
    set_hardware_acceleration,
    is_hardware_acceleration_enabled,
    set_active_ocr_engine,
    get_active_ocr_engine,
    get_ocr_engines_status,
    run_ocr_on_bytes,
    run_ocr_on_image,
    OCR_ENGINES_INFO
)

# Registry mapping extension -> parser instance
_PARSER_REGISTRY: Dict[str, BaseParser] = {}
_INSTANTIATED_PARSERS: List[BaseParser] = []
_FALLBACK_PARSER: Optional[BaseParser] = None


def discover_and_register_parsers() -> Dict[str, BaseParser]:
    """
    Scans the engine/parsers/ directory (and optional custom_parsers/ folders)
    for Python modules, finds all BaseParser subclasses, instantiates them,
    and maps each supported extension to its respective parser.
    """
    global _PARSER_REGISTRY, _INSTANTIATED_PARSERS, _FALLBACK_PARSER
    _PARSER_REGISTRY.clear()
    _INSTANTIATED_PARSERS.clear()

    # Determine directories to scan
    search_dirs = [os.path.dirname(os.path.abspath(__file__))]

    # If running as bundled app or script, also check external 'parsers/' directory next to executable
    app_root = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
    external_custom = os.path.join(app_root, "parsers")
    if os.path.isdir(external_custom) and external_custom not in search_dirs:
        search_dirs.append(external_custom)
        if external_custom not in sys.path:
            sys.path.insert(0, external_custom)

    for p_dir in search_dirs:
        if not os.path.isdir(p_dir):
            continue
        for item in sorted(os.listdir(p_dir)):
            if not item.endswith('.py'):
                continue
            if item in {'__init__.py', 'base_parser.py'}:
                continue

            mod_stem = item[:-3]
            # Try importing as package or standalone module
            mod = None
            try:
                mod = importlib.import_module(f"engine.parsers.{mod_stem}")
            except Exception:
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(mod_stem, os.path.join(p_dir, item))
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                except Exception as e:
                    print(f"[Email Crunch] Warning: Failed to load parser {item}: {e}")
                    continue

            if mod is None:
                continue

            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (
                    inspect.isclass(attr)
                    and issubclass(attr, BaseParser)
                    and attr is not BaseParser
                ):
                    try:
                        parser_instance = attr()
                        _INSTANTIATED_PARSERS.append(parser_instance)

                        for ext in parser_instance.SUPPORTED_EXTENSIONS:
                            clean_ext = ext.lower().strip()
                            if not clean_ext.startswith('.'):
                                clean_ext = '.' + clean_ext
                            _PARSER_REGISTRY[clean_ext] = parser_instance

                        if '.txt' in parser_instance.SUPPORTED_EXTENSIONS:
                            _FALLBACK_PARSER = parser_instance
                    except Exception as e:
                        print(f"[Email Crunch] Warning: Failed to instantiate parser {attr_name}: {e}")

    return _PARSER_REGISTRY


# Initialize parser registry on import
discover_and_register_parsers()


def get_registered_parsers() -> List[BaseParser]:
    """Returns a list of all active discovered parser instances."""
    return list(_INSTANTIATED_PARSERS)


def get_supported_extensions() -> Set[str]:
    """Returns a set of all currently supported file extensions (with leading dot)."""
    return set(_PARSER_REGISTRY.keys())


def get_extension_parser(extension: str) -> Optional[BaseParser]:
    """Retrieves the parser instance mapped to the given extension."""
    return _PARSER_REGISTRY.get(extension.lower())


def parse_document(
    file_path: str,
    enable_ocr: bool = False,
    progress_callback = None
) -> Tuple[List[str], Optional[str]]:
    """
    Main dispatcher function to parse any supported document, spreadsheet, or image.
    Automatically routes to the registered format parser based on file extension.

    Returns:
        (emails_list, error_message_or_None)
    """
    if not os.path.exists(file_path):
        return [], f"File not found: {file_path}"

    ext = os.path.splitext(file_path)[1].lower()

    # Check for image files with OCR disabled
    image_exts = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp'}
    if ext in image_exts and not enable_ocr:
        return [], "OCR disabled for image"

    try:
        parser = _PARSER_REGISTRY.get(ext)
        if parser is not None:
            emails = parser.parse(
                file_path=file_path,
                enable_ocr=enable_ocr,
                progress_callback=progress_callback
            )
            return emails, None
        elif _FALLBACK_PARSER is not None:
            # Fallback to plain text / byte scan
            emails = _FALLBACK_PARSER.parse(
                file_path=file_path,
                enable_ocr=enable_ocr,
                progress_callback=progress_callback
            )
            return emails, None
        else:
            return [], f"Unsupported format: {ext}"

    except Exception as e:
        return [], str(e)


__all__ = [
    "BaseParser",
    "discover_and_register_parsers",
    "get_registered_parsers",
    "get_supported_extensions",
    "get_extension_parser",
    "parse_document",
    "set_hardware_acceleration",
    "is_hardware_acceleration_enabled",
    "set_active_ocr_engine",
    "get_active_ocr_engine",
    "get_ocr_engines_status",
    "run_ocr_on_bytes",
    "run_ocr_on_image",
    "OCR_ENGINES_INFO",
]
