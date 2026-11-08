"""
Background Worker and Concurrency Manager for Email Crunch.
Uses PySide6 QThreadPool and QRunnable to execute parsing tasks asynchronously
with CPU throttling, Hardware Acceleration toggle, and Dry Run support.
"""

import os
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool

from engine.parsers import parse_document
from engine.output_manager import OutputManager


def get_auto_worker_count() -> int:
    """Calculates auto worker count: max(1, int(os.cpu_count() * 0.80))."""
    cpu_cores = os.cpu_count() or 4
    return max(1, int(cpu_cores * 0.80))


class WorkerSignals(QObject):
    """Signals emitted from file parsing tasks to the PySide6 UI."""
    progress = Signal(int, int)  # (row_index, percentage)
    file_finished = Signal(int, int, str, str, list)  # (row_index, emails_count, status_str, error_msg, emails_list)


class FileParseTask(QRunnable):
    """QRunnable task that processes a single file item in the thread pool."""
    def __init__(
        self,
        row_index: int,
        file_path: str,
        enable_ocr: bool,
        output_manager: Optional[OutputManager],
        signals: WorkerSignals,
        stop_flag_ref: list,
        is_dry_run: bool = False
    ):
        super().__init__()
        self.row_index = row_index
        self.file_path = file_path
        self.enable_ocr = enable_ocr
        self.output_manager = output_manager
        self.signals = signals
        self.stop_flag_ref = stop_flag_ref
        self.is_dry_run = is_dry_run

    def run(self):
        if self.stop_flag_ref and self.stop_flag_ref[0]:
            self.signals.file_finished.emit(self.row_index, 0, "Cancelled", "Extraction stopped", [])
            return

        def on_page_progress(pct: int):
            if not self.stop_flag_ref[0]:
                self.signals.progress.emit(self.row_index, pct)

        self.signals.progress.emit(self.row_index, 15)

        try:
            # 1. Parse document
            emails, error_msg = parse_document(
                self.file_path,
                enable_ocr=self.enable_ocr,
                progress_callback=on_page_progress
            )
            
            if error_msg:
                self.signals.progress.emit(self.row_index, 100)
                self.signals.file_finished.emit(self.row_index, 0, "Error", error_msg, [])
                return

            self.signals.progress.emit(self.row_index, 85)

            post_msg = "Dry Run (Simulated - No Files Changed)"

            # If NOT dry run, write to output manager and apply post-processing
            if not self.is_dry_run and self.output_manager:
                self.output_manager.add_results_for_file(self.file_path, emails)
                _, post_msg = self.output_manager.apply_post_processing(self.file_path)

            self.signals.progress.emit(self.row_index, 100)
            status_text = "Done (Dry Run)" if self.is_dry_run else "Done"
            self.signals.file_finished.emit(self.row_index, len(emails), status_text, post_msg, emails)

        except Exception as exc:
            self.signals.progress.emit(self.row_index, 100)
            self.signals.file_finished.emit(self.row_index, 0, "Error", str(exc), [])
