"""
Dialogs: DryRunSummaryDialog, RegexSettingsDialog, OCRSettingsDialog.
Clean professional styling, cross-platform compatible.
"""

import webbrowser
import sys
from collections import Counter
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QRadioButton, QButtonGroup, QSplitter
)

from engine.email_utils import (
    PREMADE_PATTERNS, load_user_config, save_user_config,
    set_active_regex, compile_pattern, clean_candidate_email, get_email_domain
)
from engine.parsers import get_ocr_engines_status, set_active_ocr_engine, get_active_ocr_engine


class DryRunSummaryDialog(QDialog):
    def __init__(self, file_count: int, all_emails: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dry Run Summary")
        self.resize(700, 520)
        self.proceed_to_real = False

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet("background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 5px; padding: 8px;")
        hl = QVBoxLayout(hdr)
        hl.addWidget(_lbl("Dry Run Completed — No files were modified or written to disk.", bold=True, color="#15803d"))
        layout.addWidget(hdr)

        unique = list(dict.fromkeys(e.lower() for e in all_emails))
        total_hits = len(all_emails)
        total_unique = len(unique)

        # Stats row
        stats = QHBoxLayout()
        for label, val, color in [
            ("Files Scanned", str(file_count), "#2563eb"),
            ("Total Hits", f"{total_hits:,}", "#2563eb"),
            ("Unique Emails", f"{total_unique:,}", "#15803d"),
        ]:
            card = QFrame()
            card.setStyleSheet("background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 5px; padding: 6px 12px;")
            cl = QVBoxLayout(card)
            cl.setSpacing(2)
            cl.addWidget(_lbl(label, size=10, color="#6b7280"))
            cl.addWidget(_lbl(val, size=18, bold=True, color=color, mono=True))
            stats.addWidget(card)
        layout.addLayout(stats)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)

        left = QFrame()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(_lbl("Top Domains:", bold=True, size=11))
        dom_table = QTableWidget()
        dom_table.setColumnCount(3)
        dom_table.setHorizontalHeaderLabels(["Domain", "Count", "%"])
        dom_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        dom_table.verticalHeader().setVisible(False)
        dom_counts = Counter(get_email_domain(e) for e in unique)
        dom_table.setRowCount(min(15, len(dom_counts)))
        for r, (dom, cnt) in enumerate(dom_counts.most_common(15)):
            pct = cnt / total_unique * 100 if total_unique else 0
            dom_table.setItem(r, 0, QTableWidgetItem(dom))
            ci = QTableWidgetItem(str(cnt))
            ci.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            dom_table.setItem(r, 1, ci)
            pi = QTableWidgetItem(f"{pct:.1f}%")
            pi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            dom_table.setItem(r, 2, pi)
        ll.addWidget(dom_table)
        splitter.addWidget(left)

        right = QFrame()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(_lbl(f"Sample Emails (first {min(50, total_unique)}):", bold=True, size=11))
        sample = QTextEdit()
        sample.setReadOnly(True)
        sample.setFont(QFont("Consolas", 10))
        sample.setPlainText("\n".join(unique[:50]) if unique else "No emails found.")
        rl.addWidget(sample)
        splitter.addWidget(right)

        layout.addWidget(splitter, stretch=1)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btns.addWidget(close_btn)
        proceed_btn = QPushButton("Proceed with Real Extraction")
        proceed_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: 600; padding: 5px 14px; border-radius: 5px;")
        proceed_btn.clicked.connect(self._proceed)
        btns.addWidget(proceed_btn)
        layout.addLayout(btns)

    def _proceed(self):
        self.proceed_to_real = True
        self.accept()


class RegexSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Regex Pattern Settings")
        self.resize(640, 480)
        self.cfg = load_user_config()
        self.active_key = self.cfg.get("active_pattern_key", "standard_catchy")
        self.custom_pat = self.cfg.get("custom_pattern", PREMADE_PATTERNS["standard_catchy"]["pattern"])

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(_lbl("Pattern Preset:", bold=True))
        self.combo = QComboBox()
        for k, v in PREMADE_PATTERNS.items():
            self.combo.addItem(v["name"], k)
        self.combo.addItem("Custom Pattern", "custom")
        idx = self.combo.findData(self.active_key)
        self.combo.setCurrentIndex(idx if idx >= 0 else self.combo.count() - 1)
        self.combo.currentIndexChanged.connect(self._on_preset_changed)
        layout.addWidget(self.combo)

        self.desc = QLabel()
        self.desc.setStyleSheet("color: #6b7280; font-size: 11px; font-style: italic;")
        self.desc.setWordWrap(True)
        layout.addWidget(self.desc)

        layout.addWidget(_lbl("Regular Expression:", bold=True))
        self.pat_input = QLineEdit()
        self.pat_input.setFont(QFont("Consolas", 10))
        self.pat_input.textChanged.connect(self._on_pat_edited)
        layout.addWidget(self.pat_input)

        layout.addWidget(_lbl("Live Tester — paste sample text:", bold=True))
        self.test_in = QTextEdit()
        self.test_in.setFixedHeight(72)
        self.test_in.setFont(QFont("Consolas", 10))
        self.test_in.setPlainText(
            "Contact: sales@company.com, ceo@startup.io\n"
            "Obfuscated: admin[at]corp[dot]org\nFree: user@gmail.com"
        )
        self.test_in.textChanged.connect(self._run_test)
        layout.addWidget(self.test_in)

        layout.addWidget(_lbl("Matches:", bold=True))
        self.test_out = QTextEdit()
        self.test_out.setReadOnly(True)
        self.test_out.setFixedHeight(56)
        self.test_out.setFont(QFont("Consolas", 10))
        layout.addWidget(self.test_out)

        self._on_preset_changed()

        btns = QHBoxLayout()
        reset = QPushButton("Reset to Default")
        reset.clicked.connect(lambda: self.combo.setCurrentIndex(self.combo.findData("standard_catchy")))
        btns.addWidget(reset)
        btns.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        save = QPushButton("Save & Apply")
        save.setStyleSheet("background-color: #2563eb; color: white; font-weight: 600; padding: 5px 14px; border-radius: 5px;")
        save.clicked.connect(self._save)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _on_preset_changed(self):
        key = self.combo.currentData()
        if key in PREMADE_PATTERNS:
            self.pat_input.setText(PREMADE_PATTERNS[key]["pattern"])
            self.desc.setText(PREMADE_PATTERNS[key]["description"])
        else:
            self.pat_input.setText(self.custom_pat)
            self.desc.setText("User-defined custom regular expression.")
        self._run_test()

    def _on_pat_edited(self, text: str):
        key = self.combo.currentData()
        if key in PREMADE_PATTERNS and text.strip() != PREMADE_PATTERNS[key]["pattern"].strip():
            self.combo.blockSignals(True)
            self.combo.setCurrentIndex(self.combo.findData("custom"))
            self.combo.blockSignals(False)
            self.desc.setText("User-defined custom regular expression.")
        self.custom_pat = text
        self._run_test()

    def _run_test(self):
        try:
            rgx = compile_pattern(self.pat_input.text().strip())
            matches = rgx.findall(self.test_in.toPlainText())
            valid = []
            for m in matches:
                if isinstance(m, tuple):
                    m = "".join(m)
                c = clean_candidate_email(m)
                if c:
                    valid.append(c)
            self.test_out.setText(", ".join(valid) if valid else "(no matches)")
        except Exception as e:
            self.test_out.setText(f"Error: {e}")

    def _save(self):
        key = self.combo.currentData()
        pat = self.pat_input.text().strip()
        self.cfg["active_pattern_key"] = key
        self.cfg["custom_pattern"] = pat
        save_user_config(self.cfg)
        set_active_regex(pat)
        self.accept()


class OCRSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OCR Engine Settings")
        self.resize(660, 440)
        self.active_engine = get_active_ocr_engine()

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(_lbl("Select OCR engine for scanned documents and images:", bold=True))
        info = QLabel(
            "All engines are open-source. Windows Native OCR is only available on Windows 10/11.\n"
            "RapidOCR works on all platforms and requires no system binary."
        )
        info.setStyleSheet("color: #6b7280; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["", "Engine", "Status", "GitHub"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, stretch=1)

        self.radio_group = QButtonGroup(self)
        self._populate()

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)
        self._update_desc()

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        apply = QPushButton("Apply")
        apply.setStyleSheet("background-color: #2563eb; color: white; font-weight: 600; padding: 5px 14px; border-radius: 5px;")
        apply.clicked.connect(self._apply)
        btns.addWidget(apply)
        layout.addLayout(btns)

    def _populate(self):
        engines = get_ocr_engines_status()
        self.table.setRowCount(len(engines))
        for row, (key, info) in enumerate(engines.items()):
            radio = QRadioButton()
            radio.setChecked(key == self.active_engine)
            self.radio_group.addButton(radio, row)
            radio.toggled.connect(lambda chk, k=key: chk and setattr(self, 'active_engine', k) or self._update_desc())
            container = QFrame()
            hl = QHBoxLayout(container)
            hl.setAlignment(Qt.AlignCenter)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.addWidget(radio)
            self.table.setCellWidget(row, 0, container)

            name_item = QTableWidgetItem(f"{info['name']}\n{info.get('platform', '')}")
            self.table.setItem(row, 1, name_item)

            avail = info.get("available", False)
            status = QLabel("Available" if avail else "Not installed")
            status.setStyleSheet(f"color: {'#15803d' if avail else '#b91c1c'}; font-size: 11px; font-weight: 600;")
            self.table.setCellWidget(row, 2, status)

            url = info.get("github") or info.get("windows_installer", "")
            gh_btn = QPushButton("GitHub")
            gh_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
            gh_btn.clicked.connect(lambda _, u=url: webbrowser.open(u))
            self.table.setCellWidget(row, 3, gh_btn)
        self.table.setColumnWidth(0, 36)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 70)

    def _update_desc(self):
        info = get_ocr_engines_status().get(self.active_engine, {})
        self.desc_label.setText(
            f"{info.get('name')} — {info.get('description', '')}\n"
            f"Install: pip install {info.get('pip_package', '')}"
        )

    def _apply(self):
        set_active_ocr_engine(self.active_engine)
        cfg = load_user_config()
        cfg["active_ocr_engine"] = self.active_engine
        save_user_config(cfg)
        self.accept()


def _lbl(text: str, bold: bool = False, size: int = 12,
         color: str = "", mono: bool = False) -> QLabel:
    lbl = QLabel(text)
    style = f"font-size: {size}px;"
    if bold:
        style += " font-weight: 700;"
    if color:
        style += f" color: {color};"
    if mono:
        style += " font-family: 'Consolas', monospace;"
    lbl.setStyleSheet(style)
    return lbl
