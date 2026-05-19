"""
styles.py - Apple HIG-inspired Qt stylesheet (light + dark)
"""

LIGHT_PALETTE = {
    "bg": "#F2F2F7", "surface": "#FFFFFF", "surface2": "#F2F2F7",
    "divider": "#C6C6C8", "border": "#D1D1D6",
    "text": "#000000", "text_secondary": "#3C3C43", "text_tertiary": "#8E8E93",
    "accent": "#007AFF", "accent_hover": "#0066D6", "accent_pressed": "#004FAD",
    "run_btn": "#34C759", "run_btn_hover": "#28A745",
    "stop_btn": "#FF3B30", "stop_btn_hover": "#D32F2F",
    "error": "#FF3B30", "code_bg": "#F8F8F2",
}

DARK_PALETTE = {
    "bg": "#1C1C1E", "surface": "#2C2C2E", "surface2": "#3A3A3C",
    "divider": "#38383A", "border": "#48484A",
    "text": "#FFFFFF", "text_secondary": "#EBEBF5CC", "text_tertiary": "#EBEBF599",
    "accent": "#0A84FF", "accent_hover": "#409CFF", "accent_pressed": "#0071E3",
    "run_btn": "#30D158", "run_btn_hover": "#25A244",
    "stop_btn": "#FF453A", "stop_btn_hover": "#D32F2F",
    "error": "#FF453A", "code_bg": "#1E1E2E",
}


def build_stylesheet(dark: bool = False) -> str:
    p = DARK_PALETTE if dark else LIGHT_PALETTE
    return f"""
QWidget {{
    background-color: {p['bg']};
    color: {p['text']};
    font-family: -apple-system, "SF Pro Text", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    selection-background-color: {p['accent']};
    selection-color: #FFFFFF;
}}
QMainWindow, QDialog {{ background-color: {p['bg']}; }}

QGroupBox {{
    background-color: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 12px;
    margin-top: 22px;
    padding: 8px 12px 12px 12px;
    font-size: 11px; font-weight: 600;
    color: {p['text_tertiary']};
    text-transform: uppercase; letter-spacing: 0.06em;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 12px; top: 4px; padding: 0 4px;
    background-color: {p['surface']};
}}

QLabel {{ background: transparent; color: {p['text']}; }}
QLabel[class="headline"]    {{ font-size: 17px; font-weight: 600; }}
QLabel[class="subheadline"] {{ font-size: 15px; font-weight: 500; }}
QLabel[class="caption"]     {{ font-size: 11px; color: {p['text_tertiary']}; }}

QPushButton {{
    background-color: {p['accent']}; color: #FFFFFF;
    border: none; border-radius: 8px;
    padding: 0 20px; min-height: 36px; min-width: 80px;
    font-size: 14px; font-weight: 600;
}}
QPushButton:hover    {{ background-color: {p['accent_hover']}; }}
QPushButton:pressed  {{ background-color: {p['accent_pressed']}; }}
QPushButton:disabled {{ background-color: {p['border']}; color: {p['text_tertiary']}; }}

QPushButton[class="secondary"] {{
    background-color: {p['surface2']}; color: {p['accent']};
    border: 1px solid {p['border']};
}}
QPushButton[class="secondary"]:hover {{ background-color: {p['border']}; }}

QPushButton[class="run"] {{
    background-color: {p['run_btn']}; color: #FFFFFF;
    min-height: 44px; font-size: 15px;
}}
QPushButton[class="run"]:hover {{ background-color: {p['run_btn_hover']}; }}

QPushButton[class="stop"] {{
    background-color: {p['stop_btn']}; color: #FFFFFF;
    min-height: 44px; font-size: 15px;
}}
QPushButton[class="stop"]:hover {{ background-color: {p['stop_btn_hover']}; }}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {p['surface']}; color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 8px; padding: 6px 10px; font-size: 13px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {p['accent']};
}}
QPlainTextEdit[class="code"] {{
    font-family: "SF Mono","JetBrains Mono","Cascadia Code",Consolas,monospace;
    font-size: 12px; background-color: {p['code_bg']}; border-radius: 8px;
}}

QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {p['border']}; border-radius: 4px; min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 8px; }}
QScrollBar::handle:horizontal {{
    background: {p['border']}; border-radius: 4px; min-width: 24px;
}}

QTabWidget::pane {{
    background-color: {p['surface']}; border: 1px solid {p['border']};
    border-radius: 0 8px 8px 8px;
}}
QTabBar::tab {{
    background-color: {p['surface2']}; color: {p['text_tertiary']};
    border: 1px solid {p['border']}; border-bottom: none;
    padding: 8px 18px; border-radius: 8px 8px 0 0;
    font-size: 13px; font-weight: 500; min-width: 80px;
}}
QTabBar::tab:selected {{ background-color: {p['surface']}; color: {p['text']}; font-weight: 600; }}
QTabBar::tab:hover:!selected {{ color: {p['text']}; }}

QTableWidget {{
    background-color: {p['surface']}; gridline-color: {p['divider']};
    border: none; border-radius: 8px; font-size: 12px;
}}
QTableWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {p['divider']}; }}
QTableWidget::item:selected {{ background-color: {p['accent']}; color: #FFFFFF; }}
QHeaderView::section {{
    background-color: {p['surface2']}; color: {p['text_tertiary']};
    border: none; border-bottom: 1px solid {p['divider']};
    padding: 6px 10px; font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em;
}}
QStatusBar {{
    background-color: {p['surface']}; color: {p['text_secondary']};
    border-top: 1px solid {p['divider']}; font-size: 11px;
}}
QToolTip {{
    background-color: {p['surface']}; color: {p['text']};
    border: 1px solid {p['border']}; border-radius: 6px;
    padding: 4px 8px; font-size: 12px;
}}
"""
