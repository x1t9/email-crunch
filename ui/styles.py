"""
Email Crunch UI Stylesheets — Professional flat design.
Clean neutral palette, no neon/glow effects. Full dark/light support.
"""

# System font stack — cross-platform
_FONT_STACK = "'Segoe UI', 'SF Pro Text', 'Helvetica Neue', 'Inter', Arial, sans-serif"
_MONO_STACK = "'Consolas', 'SF Mono', 'JetBrains Mono', 'Courier New', monospace"

DARK_THEME = f"""
QMainWindow, QDialog, QWidget#centralWidget {{
    background-color: #1a1d23;
    color: #d1d5db;
    font-family: {_FONT_STACK};
    font-size: 12px;
}}
QToolTip {{
    background-color: #2d3139;
    color: #e5e7eb;
    border: 1px solid #3f4451;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
}}
QFrame#windowHeader {{
    background-color: #13151a;
    border-bottom: 1px solid #2d3139;
    min-height: 36px;
    max-height: 36px;
}}
QLabel#appTitleLabel {{
    color: #f3f4f6;
    font-weight: 700;
    font-size: 13px;
}}
QLabel#appBadgeLabel {{
    background-color: #2d3139;
    color: #9ca3af;
    border: 1px solid #3f4451;
    border-radius: 3px;
    padding: 1px 6px;
    font-family: {_MONO_STACK};
    font-size: 10px;
}}
QLabel#engineIndicatorLabel {{
    color: #6b7280;
    font-size: 11px;
    font-family: {_MONO_STACK};
}}
QFrame#actionToolbar {{
    background-color: #13151a;
    border-bottom: 1px solid #2d3139;
}}
QPushButton {{
    background-color: #2d3139;
    color: #d1d5db;
    border: 1px solid #3f4451;
    border-radius: 5px;
    padding: 4px 11px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: #383d47;
    border-color: #52596a;
    color: #f3f4f6;
}}
QPushButton:pressed {{
    background-color: #1f2229;
}}
QPushButton:disabled {{
    background-color: #1f2229;
    color: #4b5563;
    border-color: #2d3139;
}}
QPushButton#primaryActionBtn {{
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    font-size: 11px;
    border: 1px solid #1d4ed8;
    border-radius: 5px;
    padding: 5px 16px;
}}
QPushButton#primaryActionBtn:hover {{
    background-color: #1d4ed8;
}}
QPushButton#primaryActionBtn:pressed {{
    background-color: #1e40af;
}}
QPushButton#dryRunBtn {{
    background-color: #0f766e;
    color: #ffffff;
    font-weight: 600;
    font-size: 11px;
    border: 1px solid #0d6b63;
    border-radius: 5px;
    padding: 5px 12px;
}}
QPushButton#dryRunBtn:hover {{
    background-color: #0d6b63;
}}
QPushButton#stopActionBtn {{
    background-color: #b91c1c;
    color: #ffffff;
    font-weight: 600;
    font-size: 11px;
    border: 1px solid #991b1b;
    border-radius: 5px;
    padding: 5px 16px;
}}
QPushButton#stopActionBtn:hover {{
    background-color: #991b1b;
}}
QPushButton#removeBtn:hover {{
    background-color: #3b1f1f;
    border-color: #b91c1c;
    color: #fca5a5;
}}
QTableWidget {{
    background-color: #1a1d23;
    alternate-background-color: #1f2229;
    color: #c9cdd4;
    gridline-color: #2d3139;
    border: 1px solid #2d3139;
    selection-background-color: #2d3139;
    selection-color: #e5e7eb;
    font-size: 11px;
}}
QHeaderView::section {{
    background-color: #13151a;
    color: #6b7280;
    padding: 5px 8px;
    border: none;
    border-bottom: 1px solid #2d3139;
    font-weight: 600;
    font-size: 11px;
}}
QTableWidget::item {{ padding: 3px 6px; color: #c9cdd4; }}
QTableWidget::item:selected {{ color: #e5e7eb; background-color: #2d3139; }}
QLabel {{ color: #d1d5db; }}
QFrame#tableHintBar {{
    background-color: #13151a;
    border: 1px solid #2d3139;
    border-top: none;
}}
QFrame#bottomPanelsContainer {{
    background-color: #13151a;
    border-top: 1px solid #2d3139;
}}
QFrame.configCard {{
    background-color: #1f2229;
    border: 1px solid #2d3139;
    border-radius: 6px;
}}
QLabel.cardHeaderLabel {{
    color: #9ca3af;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 0.5px;
}}
QLineEdit, QSpinBox, QComboBox, QTextEdit {{
    background-color: #13151a;
    color: #e5e7eb;
    border: 1px solid #3f4451;
    border-radius: 4px;
    padding: 3px 7px;
    font-size: 11px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
    border: 1px solid #4b6bbd;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background-color: #1f2229;
    color: #d1d5db;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    border: 1px solid #3f4451;
}}
QRadioButton, QCheckBox {{
    color: #c9cdd4;
    spacing: 6px;
    font-size: 11px;
}}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    border: 1px solid #4b5563;
    background-color: #13151a;
    border-radius: 2px;
}}
QRadioButton::indicator {{ border-radius: 7px; }}
QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
    background-color: #2563eb;
    border-color: #2563eb;
}}
QFrame#footerStatusBar {{
    background-color: #13151a;
    border-top: 1px solid #2d3139;
    font-family: {_MONO_STACK};
    font-size: 10px;
    color: #6b7280;
}}
QProgressBar {{
    background-color: #2d3139;
    border: none;
    border-radius: 2px;
    height: 5px;
}}
QProgressBar::chunk {{
    background-color: #2563eb;
    border-radius: 2px;
}}
QScrollBar:vertical {{
    border: none;
    background: #1a1d23;
    width: 7px;
}}
QScrollBar::handle:vertical {{
    background: #3f4451;
    min-height: 20px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{ background: #52596a; }}
QScrollBar::horizontal {{
    border: none;
    background: #1a1d23;
    height: 7px;
}}
QScrollBar::handle:horizontal {{
    background: #3f4451;
    min-width: 20px;
    border-radius: 3px;
}}
QSplitter::handle {{ background-color: #2d3139; }}
"""

LIGHT_THEME = f"""
QMainWindow, QDialog, QWidget#centralWidget {{
    background-color: #f9fafb;
    color: #111827;
    font-family: {_FONT_STACK};
    font-size: 12px;
}}
QToolTip {{
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #d1d5db;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
}}
QFrame#windowHeader {{
    background-color: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    min-height: 36px;
    max-height: 36px;
}}
QLabel#appTitleLabel {{
    color: #111827;
    font-weight: 700;
    font-size: 13px;
}}
QLabel#appBadgeLabel {{
    background-color: #f3f4f6;
    color: #6b7280;
    border: 1px solid #d1d5db;
    border-radius: 3px;
    padding: 1px 6px;
    font-family: {_MONO_STACK};
    font-size: 10px;
}}
QLabel#engineIndicatorLabel {{
    color: #9ca3af;
    font-size: 11px;
    font-family: {_MONO_STACK};
}}
QFrame#actionToolbar {{
    background-color: #ffffff;
    border-bottom: 1px solid #e5e7eb;
}}
QPushButton {{
    background-color: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 5px;
    padding: 4px 11px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: #e5e7eb;
    border-color: #9ca3af;
    color: #111827;
}}
QPushButton:pressed {{ background-color: #d1d5db; }}
QPushButton:disabled {{
    background-color: #f9fafb;
    color: #9ca3af;
    border-color: #e5e7eb;
}}
QPushButton#primaryActionBtn {{
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    font-size: 11px;
    border: 1px solid #1d4ed8;
    border-radius: 5px;
    padding: 5px 16px;
}}
QPushButton#primaryActionBtn:hover {{ background-color: #1d4ed8; }}
QPushButton#primaryActionBtn:pressed {{ background-color: #1e40af; }}
QPushButton#dryRunBtn {{
    background-color: #0f766e;
    color: #ffffff;
    font-weight: 600;
    font-size: 11px;
    border: 1px solid #0d6b63;
    border-radius: 5px;
    padding: 5px 12px;
}}
QPushButton#dryRunBtn:hover {{ background-color: #0d6b63; }}
QPushButton#stopActionBtn {{
    background-color: #b91c1c;
    color: #ffffff;
    font-weight: 600;
    font-size: 11px;
    border: 1px solid #991b1b;
    border-radius: 5px;
    padding: 5px 16px;
}}
QPushButton#stopActionBtn:hover {{ background-color: #991b1b; }}
QPushButton#removeBtn:hover {{
    background-color: #fef2f2;
    border-color: #b91c1c;
    color: #b91c1c;
}}
QTableWidget {{
    background-color: #ffffff;
    alternate-background-color: #f9fafb;
    color: #374151;
    gridline-color: #e5e7eb;
    border: 1px solid #d1d5db;
    selection-background-color: #eff6ff;
    selection-color: #1d4ed8;
    font-size: 11px;
}}
QHeaderView::section {{
    background-color: #f3f4f6;
    color: #6b7280;
    padding: 5px 8px;
    border: none;
    border-bottom: 1px solid #d1d5db;
    font-weight: 600;
    font-size: 11px;
}}
QTableWidget::item {{ padding: 3px 6px; color: #374151; }}
QTableWidget::item:selected {{ color: #1d4ed8; background-color: #eff6ff; }}
QLabel {{ color: #111827; }}
QFrame#tableHintBar {{
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-top: none;
}}
QFrame#bottomPanelsContainer {{
    background-color: #f3f4f6;
    border-top: 1px solid #e5e7eb;
}}
QFrame.configCard {{
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
}}
QLabel.cardHeaderLabel {{
    color: #6b7280;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 0.5px;
}}
QLineEdit, QSpinBox, QComboBox, QTextEdit {{
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 3px 7px;
    font-size: 11px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
    border: 1px solid #2563eb;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background-color: #ffffff;
    color: #111827;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    border: 1px solid #d1d5db;
}}
QRadioButton, QCheckBox {{
    color: #374151;
    spacing: 6px;
    font-size: 11px;
}}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    border: 1px solid #9ca3af;
    background-color: #ffffff;
    border-radius: 2px;
}}
QRadioButton::indicator {{ border-radius: 7px; }}
QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
    background-color: #2563eb;
    border-color: #2563eb;
}}
QFrame#footerStatusBar {{
    background-color: #ffffff;
    border-top: 1px solid #e5e7eb;
    font-family: {_MONO_STACK};
    font-size: 10px;
    color: #9ca3af;
}}
QProgressBar {{
    background-color: #e5e7eb;
    border: none;
    border-radius: 2px;
    height: 5px;
}}
QProgressBar::chunk {{
    background-color: #2563eb;
    border-radius: 2px;
}}
QScrollBar:vertical {{
    border: none;
    background: #f9fafb;
    width: 7px;
}}
QScrollBar::handle:vertical {{
    background: #d1d5db;
    min-height: 20px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{ background: #9ca3af; }}
QScrollBar::horizontal {{
    border: none;
    background: #f9fafb;
    height: 7px;
}}
QScrollBar::handle:horizontal {{
    background: #d1d5db;
    min-width: 20px;
    border-radius: 3px;
}}
QSplitter::handle {{ background-color: #e5e7eb; }}
"""
