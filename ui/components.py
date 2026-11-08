"""
Custom UI Components — DropZoneTable, StatusBadge, FileTypeBadge.
Cross-platform font stack, no neon colors.
"""

import os
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QTableWidget, QLabel, QProgressBar,
    QAbstractItemView, QHeaderView
)

_BADGE_MAP = {
    'PDF':  ('#dc2626', '#fef2f2', '#fecaca'),
    'DOCX': ('#2563eb', '#eff6ff', '#bfdbfe'),
    'DOC':  ('#1d4ed8', '#eff6ff', '#bfdbfe'),
    'XLSX': ('#16a34a', '#f0fdf4', '#bbf7d0'),
    'XLS':  ('#15803d', '#f0fdf4', '#bbf7d0'),
    'PPTX': ('#ea580c', '#fff7ed', '#fed7aa'),
    'PPT':  ('#c2410c', '#fff7ed', '#fed7aa'),
    'PNG':  ('#7c3aed', '#f5f3ff', '#ddd6fe'),
    'JPG':  ('#6d28d9', '#f5f3ff', '#ddd6fe'),
    'JPEG': ('#6d28d9', '#f5f3ff', '#ddd6fe'),
    'TIFF': ('#b45309', '#fffbeb', '#fde68a'),
    'TIF':  ('#b45309', '#fffbeb', '#fde68a'),
    'TXT':  ('#374151', '#f9fafb', '#e5e7eb'),
    'MHT':  ('#0f766e', '#f0fdfa', '#99f6e4'),
    'EML':  ('#0369a1', '#f0f9ff', '#bae6fd'),
}
_DEFAULT_BADGE = ('#6b7280', '#f9fafb', '#e5e7eb')


class FileTypeBadge(QLabel):
    def __init__(self, ext_str: str, parent=None):
        super().__init__(parent)
        key = ext_str.lstrip('.').upper()
        text_c, bg_c, border_c = _BADGE_MAP.get(key, _DEFAULT_BADGE)
        self.setText(key)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_c};
                background-color: {bg_c};
                border: 1px solid {border_c};
                border-radius: 3px;
                padding: 1px 5px;
                font-size: 10px;
                font-weight: 700;
            }}
        """)


class StatusBadge(QLabel):
    _STYLES = {
        'done':       ('#15803d', '#f0fdf4', '#bbf7d0', ''),
        'processing': ('#1d4ed8', '#eff6ff', '#bfdbfe', ''),
        'error':      ('#b91c1c', '#fef2f2', '#fecaca', ''),
        'cancelled':  ('#6b7280', '#f9fafb', '#e5e7eb', ''),
        'pending':    ('#92400e', '#fffbeb', '#fde68a', ''),
    }

    def __init__(self, status: str = "Pending", tooltip: str = "", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.update_status(status, tooltip)

    def update_status(self, status: str, tooltip: str = ""):
        if tooltip:
            self.setToolTip(tooltip)
        sl = status.lower()
        key = next((k for k in self._STYLES if k in sl), 'pending')
        text_c, bg_c, border_c, _ = self._STYLES[key]
        self.setText(status)
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_c};
                background-color: {bg_c};
                border: 1px solid {border_c};
                border-radius: 3px;
                padding: 1px 7px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)


class DropZoneTable(QTableWidget):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(False)
        self.setDropIndicatorShown(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(False)

        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(
            ["#", "File Name", "Type", "Size", "OCR", "Emails", "Status", "Progress"]
        )
        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)
        hdr.setSectionResizeMode(5, QHeaderView.Fixed)
        hdr.setSectionResizeMode(6, QHeaderView.Fixed)
        hdr.setSectionResizeMode(7, QHeaderView.Fixed)
        self.setColumnWidth(0, 38)
        self.setColumnWidth(2, 60)
        self.setColumnWidth(3, 78)
        self.setColumnWidth(4, 50)
        self.setColumnWidth(5, 72)
        self.setColumnWidth(6, 110)
        self.setColumnWidth(7, 150)
        self.verticalHeader().setDefaultSectionSize(26)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls() if os.path.exists(u.toLocalFile())]
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rowCount() == 0:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.Antialiasing)
            rect = self.viewport().rect()
            pen = QPen(QColor(107, 114, 128, 80), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRoundedRect(rect.adjusted(24, 24, -24, -24), 6, 6)
            painter.setFont(QFont("Segoe UI", 11))
            painter.setPen(QColor(107, 114, 128, 160))
            painter.drawText(
                QRect(rect.left(), rect.center().y() - 22, rect.width(), 28),
                Qt.AlignCenter, "Drop files or folders here"
            )
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(107, 114, 128, 110))
            painter.drawText(
                QRect(rect.left(), rect.center().y() + 8, rect.width(), 22),
                Qt.AlignCenter, "PDF · DOCX · XLSX · PPTX · TXT · HTML · EML · Images"
            )
