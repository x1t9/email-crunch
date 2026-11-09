"""
Email Crunch v0.1-alpha — Main Window
Cross-platform PySide6 desktop UI. Clean professional flat design.
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional

import psutil
from PySide6.QtCore import Qt, QTimer, QThreadPool
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QFrame,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QRadioButton,
    QButtonGroup, QProgressBar, QTableWidgetItem
)

from engine.worker import get_auto_worker_count, FileParseTask, WorkerSignals
from engine.output_manager import OutputManager
from engine.email_utils import (
    load_user_config, save_user_config,
    set_active_regex, PREMADE_PATTERNS
)
from engine.parsers import (
    set_hardware_acceleration, is_hardware_acceleration_enabled,
    get_active_ocr_engine, get_supported_extensions
)
from ui.components import DropZoneTable, StatusBadge, FileTypeBadge
from ui.styles import DARK_THEME, LIGHT_THEME
from ui.dialogs import DryRunSummaryDialog, RegexSettingsDialog, OCRSettingsDialog

APP_VERSION = "0.1-alpha"


def _fmt_size(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024 ** 2:
        return f"{b/1024:.1f} KB"
    elif b < 1024 ** 3:
        return f"{b/1024**2:.1f} MB"
    return f"{b/1024**3:.2f} GB"


class MainWindow(QMainWindow):
    @property
    def SUPPORTED_EXTENSIONS(self):
        return get_supported_extensions()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Email Crunch {APP_VERSION}")
        self.resize(1200, 820)
        self.setMinimumSize(900, 640)

        self.cfg = load_user_config()
        self.is_dark_mode = True
        self.is_extracting = False
        self.is_dry_run = False
        self.stop_flag_ref = [False]
        self.file_items: List[Dict[str, Any]] = []
        self.total_unique_emails = 0
        self.dry_run_emails: List[str] = []
        self.start_time: Optional[float] = None
        self.output_manager: Optional[OutputManager] = None

        pat_key = self.cfg.get("active_pattern_key", "standard_catchy")
        if pat_key == "custom":
            set_active_regex(self.cfg.get("custom_pattern", PREMADE_PATTERNS["standard_catchy"]["pattern"]))
        elif pat_key in PREMADE_PATTERNS:
            set_active_regex(PREMADE_PATTERNS[pat_key]["pattern"])

        self.thread_pool = QThreadPool.globalInstance()
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self._update_telemetry)
        self.telemetry_timer.start(1500)

        self._setup_ui()
        self.apply_theme()

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_table_area(), stretch=1)
        root.addWidget(self._build_config_panels())
        root.addWidget(self._build_footer())

    def _build_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setObjectName("windowHeader")
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(8)

        icon = QLabel("@")
        icon.setFixedSize(20, 20)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            "background-color: #2563eb; color: white; border-radius: 4px;"
            "font-weight: 700; font-size: 11px;"
        )
        lay.addWidget(icon)

        title = QLabel("Email Crunch")
        title.setObjectName("appTitleLabel")
        lay.addWidget(title)

        badge = QLabel(f"v{APP_VERSION}")
        badge.setObjectName("appBadgeLabel")
        lay.addWidget(badge)

        lay.addStretch()

        self.engine_status_label = QLabel("Ready")
        self.engine_status_label.setObjectName("engineIndicatorLabel")
        lay.addWidget(self.engine_status_label)

        lay.addStretch()

        self.theme_btn = QPushButton("Light")
        self.theme_btn.setFixedHeight(22)
        self.theme_btn.setFixedWidth(52)
        self.theme_btn.clicked.connect(self.toggle_theme)
        lay.addWidget(self.theme_btn)
        return hdr

    def _build_toolbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("actionToolbar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(6)

        for label, slot in [("Add Files", self._action_add_files),
                             ("Add Folder", self._action_add_folder)]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        lay.addWidget(sep)

        self.btn_remove = QPushButton("Remove")
        self.btn_remove.setObjectName("removeBtn")
        self.btn_remove.clicked.connect(self._action_remove_selected)
        lay.addWidget(self.btn_remove)

        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self._action_clear_all)
        lay.addWidget(btn_clear)

        btn_regex = QPushButton("Regex Patterns")
        btn_regex.clicked.connect(self._show_regex_dialog)
        lay.addWidget(btn_regex)

        lay.addStretch()

        self.queue_label = QLabel("0 files")
        self.queue_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        lay.addWidget(self.queue_label)

        self.btn_dry_run = QPushButton("Dry Run")
        self.btn_dry_run.setObjectName("dryRunBtn")
        self.btn_dry_run.setToolTip("Simulate extraction — no files modified, no CSV written")
        self.btn_dry_run.setMinimumHeight(28)
        self.btn_dry_run.clicked.connect(self._start_dry_run)
        lay.addWidget(self.btn_dry_run)

        self.btn_start = QPushButton("Start Extraction")
        self.btn_start.setObjectName("primaryActionBtn")
        self.btn_start.setMinimumHeight(28)
        self.btn_start.clicked.connect(self.toggle_extraction)
        lay.addWidget(self.btn_start)
        return bar

    def _build_table_area(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(10, 8, 10, 4)
        lay.setSpacing(0)

        self.table = DropZoneTable()
        self.table.files_dropped.connect(self.add_paths)
        lay.addWidget(self.table, stretch=1)

        hint = QFrame()
        hint.setObjectName("tableHintBar")
        hl = QHBoxLayout(hint)
        hl.setContentsMargins(8, 3, 8, 3)
        hl.addWidget(QLabel("Drag & drop files or folders into the table above"))
        hl.addStretch()
        self.hw_label = QLabel()
        self.hw_label.setStyleSheet("font-size: 10px; color: #6b7280;")
        self._refresh_hw_label()
        hl.addWidget(self.hw_label)
        lay.addWidget(hint)
        return container

    def _refresh_hw_label(self):
        hw = "HW Accel: ON" if is_hardware_acceleration_enabled() else "HW Accel: OFF"
        ocr = f"OCR: {get_active_ocr_engine()}"
        self.hw_label.setText(f"{hw}  |  {ocr}")

    def _build_config_panels(self) -> QFrame:
        container = QFrame()
        container.setObjectName("bottomPanelsContainer")
        lay = QGridLayout(container)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)
        lay.setColumnStretch(0, 1)
        lay.setColumnStretch(1, 1)
        lay.setColumnStretch(2, 1)
        lay.addWidget(self._card_performance(), 0, 0)
        lay.addWidget(self._card_output(), 0, 1)
        lay.addWidget(self._card_postprocess(), 0, 2)
        return container

    def _card_header(self, title: str) -> QLabel:
        lbl = QLabel(title.upper())
        lbl.setProperty("class", "cardHeaderLabel")
        return lbl

    def _card_performance(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "configCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)
        lay.addWidget(self._card_header("Engine & Performance"))

        lay.addWidget(QLabel("Concurrency:"))
        auto_n = get_auto_worker_count()
        cpu_n = os.cpu_count() or 4
        self.concurrency_combo = QComboBox()
        self.concurrency_combo.addItem(f"Auto — {auto_n} threads (80% CPU)", auto_n)
        self.concurrency_combo.addItem(f"Max — {cpu_n} threads (100% CPU)", cpu_n)
        self.concurrency_combo.addItem("Balanced — 5 threads", 5)
        self.concurrency_combo.addItem("Single thread (safe)", 1)
        lay.addWidget(self.concurrency_combo)

        hw_on = self.cfg.get("hardware_acceleration", True)
        self.hw_accel_check = QCheckBox("Hardware Acceleration (AVX / ONNX)")
        self.hw_accel_check.setChecked(hw_on)
        self.hw_accel_check.toggled.connect(self._on_hw_toggled)
        lay.addWidget(self.hw_accel_check)

        ocr_row = QHBoxLayout()
        self.ocr_checkbox = QCheckBox("Enable OCR")
        self.ocr_checkbox.setChecked(True)
        ocr_row.addWidget(self.ocr_checkbox)
        btn_ocr = QPushButton("OCR Settings")
        btn_ocr.setStyleSheet("font-size: 10px; padding: 2px 7px;")
        btn_ocr.clicked.connect(self._show_ocr_dialog)
        ocr_row.addWidget(btn_ocr)
        lay.addLayout(ocr_row)
        lay.addStretch()
        return card

    def _card_output(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "configCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(5)
        lay.addWidget(self._card_header("Output & Export"))

        self.radio_group = QButtonGroup(self)
        self.radio_same = QRadioButton("Same folder as source")
        self.radio_custom = QRadioButton("Custom folder")
        self.radio_merge = QRadioButton("Merge all into one CSV")
        self.radio_group.addButton(self.radio_same, 1)
        self.radio_group.addButton(self.radio_custom, 2)
        self.radio_group.addButton(self.radio_merge, 3)
        self.radio_custom.setChecked(True)
        self.radio_same.toggled.connect(self._on_dest_mode_changed)
        self.radio_custom.toggled.connect(self._on_dest_mode_changed)
        self.radio_merge.toggled.connect(self._on_dest_mode_changed)
        lay.addWidget(self.radio_same)
        lay.addWidget(self.radio_custom)

        # Destination folder row (shown for custom + merge)
        dest_row = QHBoxLayout()
        dest_row.setContentsMargins(14, 0, 0, 0)
        default_dir = os.path.join(os.path.expanduser("~"), "Documents", "EmailCrunch")
        self.dest_input = QLineEdit(default_dir)
        dest_row.addWidget(self.dest_input)
        self.btn_browse_dest = QPushButton("Browse")
        self.btn_browse_dest.setFixedWidth(58)
        self.btn_browse_dest.clicked.connect(self._browse_dest)
        dest_row.addWidget(self.btn_browse_dest)
        lay.addLayout(dest_row)

        lay.addWidget(self.radio_merge)

        # Prefix + split rows (always visible)
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        prefix_col = QVBoxLayout()
        prefix_col.addWidget(QLabel("Prefix:"))
        self.prefix_input = QLineEdit("emails_")
        prefix_col.addWidget(self.prefix_input)
        row2.addLayout(prefix_col)
        split_col = QVBoxLayout()
        split_col.addWidget(QLabel("Split rows:"))
        self.split_spin = QSpinBox()
        self.split_spin.setRange(100, 1000000)
        self.split_spin.setValue(20000)
        self.split_spin.setSingleStep(5000)
        split_col.addWidget(self.split_spin)
        row2.addLayout(split_col)
        lay.addLayout(row2)

        self.dedupe_check = QCheckBox("Deduplicate emails globally")
        self.dedupe_check.setChecked(True)
        lay.addWidget(self.dedupe_check)
        return card

    def _card_postprocess(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "configCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)
        lay.addWidget(self._card_header("Post-Processing"))

        lay.addWidget(QLabel("After successful extraction:"))
        self.post_combo = QComboBox()
        self.post_combo.addItem("Keep original file", "keep")
        self.post_combo.addItem("Rename file (add prefix)", "rename")
        self.post_combo.addItem("Move to archive folder", "move")
        self.post_combo.addItem("Delete source file", "delete")
        self.post_combo.currentIndexChanged.connect(self._on_post_changed)
        lay.addWidget(self.post_combo)

        self.rename_frame = QWidget()
        rl = QHBoxLayout(self.rename_frame)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(QLabel("Prefix:"))
        self.rename_input = QLineEdit("Scraped_")
        rl.addWidget(self.rename_input)
        lay.addWidget(self.rename_frame)

        self.archive_frame = QWidget()
        al = QHBoxLayout(self.archive_frame)
        al.setContentsMargins(0, 0, 0, 0)
        self.archive_input = QLineEdit(
            os.path.join(os.path.expanduser("~"), "Documents", "Processed")
        )
        al.addWidget(self.archive_input)
        btn_arch = QPushButton("Browse")
        btn_arch.setFixedWidth(58)
        btn_arch.clicked.connect(self._browse_archive)
        al.addWidget(btn_arch)
        self.archive_frame.setVisible(False)
        lay.addWidget(self.archive_frame)

        self.notify_check = QCheckBox("Show summary when batch completes")
        self.notify_check.setChecked(True)
        lay.addWidget(self.notify_check)
        lay.addStretch()
        return card

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("footerStatusBar")
        lay = QHBoxLayout(footer)
        lay.setContentsMargins(10, 3, 10, 3)
        lay.setSpacing(12)

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setFixedSize(48, 6)
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setValue(0)
        self.cpu_bar.setTextVisible(False)
        self.cpu_text = QLabel("CPU 0%")
        lay.addWidget(self.cpu_bar)
        lay.addWidget(self.cpu_text)

        lay.addWidget(_vsep())

        self.ram_text = QLabel("RAM —")
        lay.addWidget(self.ram_text)

        lay.addWidget(_vsep())

        self.queue_breakdown = QLabel("0 files")
        lay.addWidget(self.queue_breakdown)

        lay.addStretch()

        lay.addWidget(QLabel("Emails:"))
        self.emails_counter = QLabel("0")
        self.emails_counter.setStyleSheet(
            "color: #2563eb; font-weight: 700; font-size: 12px; font-family: monospace;"
        )
        lay.addWidget(self.emails_counter)

        lay.addWidget(_vsep())

        self.elapsed_label = QLabel("00:00:00")
        lay.addWidget(self.elapsed_label)
        return footer

    # ── Theme ──────────────────────────────────────────────────────────────

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet(DARK_THEME if self.is_dark_mode else LIGHT_THEME)
        self.theme_btn.setText("Light" if self.is_dark_mode else "Dark")

    # ── Settings callbacks ─────────────────────────────────────────────────

    def _on_hw_toggled(self, checked: bool):
        set_hardware_acceleration(checked)
        self.cfg["hardware_acceleration"] = checked
        save_user_config(self.cfg)
        self._refresh_hw_label()

    def _on_post_changed(self):
        action = self.post_combo.currentData()
        self.rename_frame.setVisible(action == "rename")
        self.archive_frame.setVisible(action == "move")

    def _on_dest_mode_changed(self):
        """Show/hide destination folder row based on selected output mode."""
        show = self.radio_custom.isChecked() or self.radio_merge.isChecked()
        self.dest_input.setVisible(show)
        self.btn_browse_dest.setVisible(show)

    def _browse_dest(self):
        # Start from current input value, or last added file's folder, or home
        start = self.dest_input.text().strip()
        if not os.path.isdir(start) and self.file_items:
            start = os.path.dirname(self.file_items[-1]['path'])
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        d = QFileDialog.getExistingDirectory(self, "Select Export Folder", start)
        if d:
            self.dest_input.setText(d)

    def _browse_archive(self):
        d = QFileDialog.getExistingDirectory(self, "Select Archive Folder", self.archive_input.text())
        if d:
            self.archive_input.setText(d)

    def _show_regex_dialog(self):
        RegexSettingsDialog(self).exec()

    def _show_ocr_dialog(self):
        OCRSettingsDialog(self).exec()
        self._refresh_hw_label()

    # ── File management ────────────────────────────────────────────────────

    def _action_add_files(self):
        all_exts = " ".join(f"*{ext}" for ext in sorted(get_supported_extensions()))
        filters = (
            f"All Supported Files ({all_exts});;"
            "PDF Documents (*.pdf);;"
            "Word Documents (*.docx *.doc *.odt *.rtf);;"
            "Excel Spreadsheets (*.xlsx *.xls *.ods *.csv *.tsv);;"
            "PowerPoint (*.pptx *.ppt *.odp);;"
            "Text & Web (*.txt *.md *.tex *.html *.mhtml *.mht *.xml *.json *.log *.eml);;"
            "Apple iWork (*.pages *.numbers *.key);;"
            "E-Books (*.epub);;"
            "Images (*.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp);;"
            "All Files (*.*)"
        )
        files, _ = QFileDialog.getOpenFileNames(self, "Add Files", "", filters)
        if files:
            self.add_paths(files)

    def _action_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Add Folder")
        if folder:
            found = []
            for root, _, files in os.walk(folder):
                for f in files:
                    if os.path.splitext(f)[1].lower() in self.SUPPORTED_EXTENSIONS:
                        found.append(os.path.join(root, f))
            if found:
                self.add_paths(found)
            else:
                QMessageBox.information(self, "No Files Found",
                                        "No supported files found in the selected folder.")

    def add_paths(self, paths: List[str]):
        existing = {it['path'] for it in self.file_items}
        for path in paths:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        if os.path.splitext(f)[1].lower() in self.SUPPORTED_EXTENSIONS:
                            fp = os.path.join(root, f)
                            if fp not in existing:
                                self._insert_row(fp)
                                existing.add(fp)
            elif os.path.isfile(path) and path not in existing:
                self._insert_row(path)
                existing.add(path)
        self._update_queue_labels()

    def _insert_row(self, file_path: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        name = os.path.basename(file_path)
        ext = os.path.splitext(name)[1].lower()
        size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        num = QTableWidgetItem(str(row + 1))
        num.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, num)

        name_item = QTableWidgetItem(name)
        name_item.setToolTip(file_path)
        self.table.setItem(row, 1, name_item)

        self.table.setCellWidget(row, 2, FileTypeBadge(ext))

        sz = QTableWidgetItem(_fmt_size(size))
        sz.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 3, sz)

        is_img = ext in {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp', '.pdf'}
        ocr_item = QTableWidgetItem("On" if (is_img and self.ocr_checkbox.isChecked()) else "—")
        ocr_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, ocr_item)

        emails_item = QTableWidgetItem("0")
        emails_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 5, emails_item)

        self.table.setCellWidget(row, 6, StatusBadge("Pending"))

        pbar = QProgressBar()
        pbar.setRange(0, 100)
        pbar.setValue(0)
        pbar.setTextVisible(False)
        self.table.setCellWidget(row, 7, pbar)

        self.file_items.append({
            'row': row, 'path': file_path, 'name': name,
            'ext': ext, 'size': size, 'status': 'Pending',
            'emails': 0, 'error': None
        })

    def _action_remove_selected(self):
        if self.is_extracting:
            return
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)
            if r < len(self.file_items):
                del self.file_items[r]
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if item:
                item.setText(str(i + 1))
            if i < len(self.file_items):
                self.file_items[i]['row'] = i
        self._update_queue_labels()

    def _action_clear_all(self):
        if self.is_extracting:
            return
        self.table.setRowCount(0)
        self.file_items.clear()
        self.total_unique_emails = 0
        self.emails_counter.setText("0")
        self._update_queue_labels()

    def _update_queue_labels(self):
        total = len(self.file_items)
        done = sum(1 for it in self.file_items if 'done' in it['status'].lower())
        active = sum(1 for it in self.file_items if it['status'] == 'Processing')
        pending = sum(1 for it in self.file_items if it['status'] == 'Pending')
        errors = sum(1 for it in self.file_items if it['status'] == 'Error')
        self.queue_label.setText(f"{total} files")
        self.queue_breakdown.setText(
            f"{total} files — {done} done, {active} active, {pending} pending, {errors} errors"
        )

    # ── Extraction ─────────────────────────────────────────────────────────

    def _start_dry_run(self):
        self._start_processing(is_dry_run=True)

    def toggle_extraction(self):
        if self.is_extracting:
            self._stop_extraction()
        else:
            self._start_processing(is_dry_run=False)

    def _start_processing(self, is_dry_run: bool = False):
        if not self.file_items:
            QMessageBox.information(self, "Queue Empty", "Add files or folders first.")
            return

        self.is_dry_run = is_dry_run
        self.dry_run_emails.clear()

        dest_mode = "same_folder"
        if self.radio_custom.isChecked():
            dest_mode = "custom_folder"
        elif self.radio_merge.isChecked():
            dest_mode = "merge_all"

        self.output_manager = OutputManager(
            destination_mode=dest_mode,
            custom_folder=self.dest_input.text().strip(),
            file_prefix=self.prefix_input.text().strip(),
            auto_split=True,
            split_limit=self.split_spin.value(),
            global_dedupe=self.dedupe_check.isChecked(),
            post_action=self.post_combo.currentData(),
            archive_folder=self.archive_input.text().strip(),
            rename_prefix=self.rename_input.text(),
        )

        self.thread_pool.setMaxThreadCount(self.concurrency_combo.currentData())
        self.is_extracting = True
        self.stop_flag_ref[0] = False
        self.start_time = time.time()
        self.total_unique_emails = 0
        self.emails_counter.setText("0")

        self.btn_dry_run.setEnabled(False)
        self.btn_start.setObjectName("stopActionBtn")
        self.btn_start.setText("Stop")
        self.apply_theme()

        status_txt = "Dry run active — simulating..." if is_dry_run else "Extracting..."
        self.engine_status_label.setText(status_txt)

        enable_ocr = self.ocr_checkbox.isChecked()
        for idx, item in enumerate(self.file_items):
            item['status'] = 'Processing'
            badge = self.table.cellWidget(idx, 6)
            if isinstance(badge, StatusBadge):
                badge.update_status("Processing")

            signals = WorkerSignals()
            signals.progress.connect(self._on_progress)
            signals.file_finished.connect(self._on_finished)

            task = FileParseTask(
                row_index=idx,
                file_path=item['path'],
                enable_ocr=enable_ocr,
                output_manager=self.output_manager if not is_dry_run else None,
                signals=signals,
                stop_flag_ref=self.stop_flag_ref,
                is_dry_run=is_dry_run,
            )
            self.thread_pool.start(task)

    def _stop_extraction(self):
        self.stop_flag_ref[0] = True
        self.is_extracting = False
        self.btn_dry_run.setEnabled(True)
        self.btn_start.setObjectName("primaryActionBtn")
        self.btn_start.setText("Start Extraction")
        self.apply_theme()
        self.engine_status_label.setText("Stopped")
        self._update_queue_labels()

    def _on_progress(self, row_idx: int, pct: int):
        pbar = self.table.cellWidget(row_idx, 7)
        if isinstance(pbar, QProgressBar):
            pbar.setValue(pct)

    def _on_finished(self, row_idx: int, emails_found: int, status: str,
                     info_msg: str, emails_list: list):
        if row_idx < len(self.file_items):
            self.file_items[row_idx]['status'] = status
            self.file_items[row_idx]['emails'] = emails_found

        if self.is_dry_run:
            self.dry_run_emails.extend(emails_list)

        item = self.table.item(row_idx, 5)
        if item:
            item.setText(f"{emails_found:,}")
            if emails_found > 0:
                item.setForeground(QColor("#15803d"))

        badge = self.table.cellWidget(row_idx, 6)
        if isinstance(badge, StatusBadge):
            badge.update_status(status, tooltip=info_msg)

        pbar = self.table.cellWidget(row_idx, 7)
        if isinstance(pbar, QProgressBar):
            pbar.setValue(100)

        if not self.is_dry_run and self.output_manager and self.output_manager.global_dedupe:
            self.total_unique_emails = len(self.output_manager.global_seen_emails)
        elif self.is_dry_run:
            self.total_unique_emails = len(set(self.dry_run_emails))
        else:
            self.total_unique_emails += emails_found

        self.emails_counter.setText(f"{self.total_unique_emails:,}")
        self._update_queue_labels()

        all_done = all(
            it['status'] in {'Done', 'Done (Dry Run)', 'Error', 'Cancelled'}
            for it in self.file_items
        )
        if all_done and self.is_extracting:
            self._finish_batch()

    def _finish_batch(self):
        self.is_extracting = False
        self.btn_dry_run.setEnabled(True)
        self.btn_start.setObjectName("primaryActionBtn")
        self.btn_start.setText("Start Extraction")
        self.apply_theme()
        self.engine_status_label.setText("Ready")

        if self.is_dry_run:
            dlg = DryRunSummaryDialog(len(self.file_items), self.dry_run_emails, self)
            dlg.exec()
            if dlg.proceed_to_real:
                self._start_processing(is_dry_run=False)
            return

        if self.output_manager and self.radio_merge.isChecked():
            saved = self.output_manager.finalize_merged_export()
            if saved and self.notify_check.isChecked():
                QMessageBox.information(
                    self, "Batch Complete",
                    f"Files processed: {len(self.file_items)}\n"
                    f"Unique emails found: {self.total_unique_emails:,}\n\n"
                    f"Merged CSV saved to:\n" + "\n".join(saved)
                )
                return

        if self.notify_check.isChecked():
            QMessageBox.information(
                self, "Batch Complete",
                f"Files processed: {len(self.file_items)}\n"
                f"Unique emails found: {self.total_unique_emails:,}"
            )

    # ── Telemetry ──────────────────────────────────────────────────────────

    def _update_telemetry(self):
        try:
            cpu = int(psutil.cpu_percent(interval=None))
            self.cpu_bar.setValue(cpu)
            self.cpu_text.setText(f"CPU {cpu}%")
            mem = psutil.virtual_memory()
            used = mem.used / 1024 ** 3
            total = mem.total / 1024 ** 3
            self.ram_text.setText(f"RAM {used:.1f}/{total:.1f} GB")
        except Exception:
            pass

        if self.is_extracting and self.start_time:
            s = int(time.time() - self.start_time)
            self.elapsed_label.setText(f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}")


def _vsep() -> QLabel:
    sep = QLabel("|")
    sep.setStyleSheet("color: #3f4451;")
    return sep
