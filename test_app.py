"""
Test suite for Email Crunch v0.1-alpha.
Tests email utils, modular parsers, output manager, and GUI.
"""

import os
import sys
import tempfile
import zipfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.email_utils import (
    extract_emails_from_text, clean_candidate_email,
    deduplicate_email_list, PREMADE_PATTERNS,
    compile_pattern, set_active_regex, get_email_domain
)
from engine.parsers import (
    parse_document, get_ocr_engines_status,
    set_hardware_acceleration, is_hardware_acceleration_enabled
)
from engine.output_manager import OutputManager


class TestEmailUtils(unittest.TestCase):
    def test_standard_extraction(self):
        text = (
            "Contact info@example.com or support@sub.domain.co.uk. "
            "Jane <jane.doe+tag@company.org>. "
            "Asset: icon@2x.png (ignored). Broken: bad@.com"
        )
        emails = extract_emails_from_text(text)
        self.assertIn("info@example.com", emails)
        self.assertIn("support@sub.domain.co.uk", emails)
        self.assertIn("jane.doe+tag@company.org", emails)
        self.assertNotIn("icon@2x.png", emails)
        self.assertNotIn("bad@.com", emails)

    def test_obfuscated_pattern(self):
        text = "admin[at]security[dot]org and help (at) service.co"
        rgx = compile_pattern(PREMADE_PATTERNS["obfuscated"]["pattern"])
        emails = extract_emails_from_text(text, custom_regex=rgx)
        self.assertIn("admin@security.org", emails)
        self.assertIn("help@service.co", emails)

    def test_corporate_only_pattern(self):
        text = "personal@gmail.com, work@enterprise.com, old@yahoo.com, ceo@techcorp.io"
        rgx = compile_pattern(PREMADE_PATTERNS["corporate_only"]["pattern"])
        emails = extract_emails_from_text(text, custom_regex=rgx)
        self.assertIn("work@enterprise.com", emails)
        self.assertIn("ceo@techcorp.io", emails)
        self.assertNotIn("personal@gmail.com", emails)
        self.assertNotIn("old@yahoo.com", emails)

    def test_domain_helper(self):
        self.assertEqual(get_email_domain("test@example.com"), "@example.com")
        self.assertEqual(get_email_domain("user@corp.co.uk"), "@corp.co.uk")


class TestParsers(unittest.TestCase):
    def test_plain_text(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Email: parser@crunch.net and ceo@crunch.net")
            path = f.name
        try:
            emails, err = parse_document(path)
            self.assertIsNone(err)
            self.assertIn("parser@crunch.net", emails)
            self.assertIn("ceo@crunch.net", emails)
        finally:
            os.remove(path)

    def test_docx_parser(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            with zipfile.ZipFile(path, "w") as z:
                z.writestr(
                    "word/document.xml",
                    b'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    b'<w:body><w:p><w:t>Contact docx@enterprise.com</w:t></w:p></w:body></w:document>'
                )
            emails, err = parse_document(path)
            self.assertIsNone(err)
            self.assertIn("docx@enterprise.com", emails)
        finally:
            os.remove(path)

    def test_parser_autodiscovery(self):
        """Verify engine/parsers/ auto-discovery loads all built-in format parsers."""
        from engine.parsers import get_supported_extensions, get_registered_parsers
        supported = get_supported_extensions()
        for ext in ['.docx', '.doc', '.odt', '.rtf', '.xlsx', '.xls', '.ods', '.csv', '.tsv',
                    '.pptx', '.ppt', '.odp', '.pdf', '.txt', '.md', '.html', '.eml',
                    '.epub', '.pages', '.numbers', '.key', '.png', '.jpg']:
            self.assertIn(ext, supported, f"Parser for {ext} not discovered")
        parsers = get_registered_parsers()
        self.assertGreaterEqual(len(parsers), 7)

    def test_custom_parser_dynamic_drop(self):
        """Verify dropping a custom parser file in engine/parsers/ is auto-detected."""
        import importlib
        from engine.parsers import discover_and_register_parsers, get_supported_extensions
        parsers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine", "parsers")
        custom_file = os.path.join(parsers_dir, "custom_dummy_parser.py")
        custom_code = (
            "from engine.parsers.base_parser import BaseParser\n"
            "class CustomDummyParser(BaseParser):\n"
            "    SUPPORTED_EXTENSIONS = {'.dummyformat'}\n"
            "    PARSER_NAME = 'Dummy Custom Parser'\n"
            "    def parse(self, file_path, enable_ocr=False, progress_callback=None):\n"
            "        return ['custom@dummy.org']\n"
        )
        try:
            with open(custom_file, "w") as f:
                f.write(custom_code)
            discover_and_register_parsers()
            supported = get_supported_extensions()
            self.assertIn('.dummyformat', supported)
            emails, err = parse_document("test.dummyformat")
            # If file doesn't exist, parse_document returns file not found, but we can create a dummy file
            with tempfile.NamedTemporaryFile(suffix=".dummyformat", delete=False) as df:
                df.write(b"content")
                df_path = df.name
            try:
                emails, err = parse_document(df_path)
                self.assertIsNone(err)
                self.assertEqual(emails, ['custom@dummy.org'])
            finally:
                if os.path.exists(df_path):
                    os.remove(df_path)
        finally:
            if os.path.exists(custom_file):
                os.remove(custom_file)
            discover_and_register_parsers()

    def test_ocr_engine_status(self):
        status = get_ocr_engines_status()
        for key in ["windows_native", "rapidocr", "tesseract", "easyocr"]:
            self.assertIn(key, status)
            self.assertIn("available", status[key])

    def test_hardware_acceleration_toggle(self):
        set_hardware_acceleration(False)
        self.assertFalse(is_hardware_acceleration_enabled())
        set_hardware_acceleration(True)
        self.assertTrue(is_hardware_acceleration_enabled())


class TestOutputManager(unittest.TestCase):
    def test_csv_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "sample.txt")
            open(src, "w").close()
            mgr = OutputManager(
                destination_mode="custom_folder",
                custom_folder=tmp,
                file_prefix="test_",
                auto_split=True,
                split_limit=3,
                global_dedupe=True,
                post_action="keep",
            )
            mgr.add_results_for_file(src, [f"u{i}@test.com" for i in range(7)])
            files = [f for f in os.listdir(tmp) if f.startswith("test_sample_")]
            self.assertGreater(len(files), 1)

    def test_post_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "doc.txt")
            open(src, "w").close()
            mgr = OutputManager(post_action="rename", rename_prefix="Done_")
            ok, _ = mgr.apply_post_processing(src)
            self.assertTrue(ok)
            self.assertFalse(os.path.exists(src))
            self.assertTrue(os.path.exists(os.path.join(tmp, "Done_doc.txt")))


class TestGUI(unittest.TestCase):
    def test_window_init(self):
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        app = QApplication.instance() or QApplication(sys.argv)
        win = MainWindow()
        self.assertIn("Email Crunch", win.windowTitle())
        self.assertEqual(win.table.columnCount(), 8)
        self.assertIsNotNone(win.btn_dry_run)
        win.close()


if __name__ == "__main__":
    unittest.main()
