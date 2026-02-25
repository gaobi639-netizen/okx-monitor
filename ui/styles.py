"""Apple-inspired modern UI styles for OKX Monitor."""

# Color palette - Apple-inspired
COLORS = {
    # Background colors
    'bg_primary': '#1c1c1e',      # Main background
    'bg_secondary': '#2c2c2e',    # Card background
    'bg_tertiary': '#3a3a3c',     # Elevated elements
    'bg_hover': '#48484a',        # Hover state

    # Accent colors
    'accent_blue': '#0a84ff',     # Primary action
    'accent_green': '#30d158',    # Success/Long
    'accent_red': '#ff453a',      # Error/Short
    'accent_orange': '#ff9f0a',   # Warning
    'accent_purple': '#bf5af2',   # Special
    'accent_cyan': '#64d2ff',     # Info

    # Text colors
    'text_primary': '#ffffff',
    'text_secondary': '#98989d',
    'text_tertiary': '#636366',

    # Border colors
    'border': '#38383a',
    'border_light': '#48484a',

    # Status colors
    'status_active': '#30d158',
    'status_inactive': '#636366',
}

# Main application stylesheet
STYLESHEET = f"""
/* ===== Global Styles ===== */
QMainWindow, QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    font-size: 13px;
}}

/* ===== Labels ===== */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}

QLabel[class="title"] {{
    font-size: 24px;
    font-weight: 600;
    letter-spacing: -0.5px;
}}

QLabel[class="subtitle"] {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
}}

QLabel[class="section-title"] {{
    font-size: 11px;
    font-weight: 600;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ===== Buttons ===== */
QPushButton {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_secondary']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_tertiary']};
}}

QPushButton[class="primary"] {{
    background-color: {COLORS['accent_blue']};
    color: white;
}}

QPushButton[class="primary"]:hover {{
    background-color: #0077ed;
}}

QPushButton[class="primary"]:pressed {{
    background-color: #006adc;
}}

QPushButton[class="success"] {{
    background-color: {COLORS['accent_green']};
    color: white;
}}

QPushButton[class="success"]:hover {{
    background-color: #28c04d;
}}

QPushButton[class="danger"] {{
    background-color: {COLORS['accent_red']};
    color: white;
}}

QPushButton[class="danger"]:hover {{
    background-color: #e63e35;
}}

QPushButton[class="small"] {{
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 6px;
}}

/* ===== Input Fields ===== */
QLineEdit {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    selection-background-color: {COLORS['accent_blue']};
}}

QLineEdit:focus {{
    border-color: {COLORS['accent_blue']};
}}

QLineEdit:disabled {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_tertiary']};
}}

QLineEdit::placeholder {{
    color: {COLORS['text_tertiary']};
}}

/* ===== SpinBox ===== */
QSpinBox {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}}

QSpinBox:focus {{
    border-color: {COLORS['accent_blue']};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    border: none;
    background: transparent;
    width: 20px;
}}

QSpinBox::up-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 5px solid {COLORS['text_secondary']};
}}

QSpinBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS['text_secondary']};
}}

/* ===== Tab Widget ===== */
QTabWidget::pane {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: -1px;
}}

QTabBar {{
    background: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    padding: 10px 20px;
    margin-right: 4px;
    border-radius: 8px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
}}

/* ===== Table Widget ===== */
QTableWidget {{
    background-color: {COLORS['bg_secondary']};
    alternate-background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 12px;
    gridline-color: {COLORS['border']};
    selection-background-color: {COLORS['accent_blue']};
    selection-color: white;
}}

QTableWidget::item {{
    padding: 12px 16px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['accent_blue']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_secondary']};
    padding: 12px 16px;
    border: none;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QHeaderView::section:first {{
    border-top-left-radius: 12px;
}}

QHeaderView::section:last {{
    border-top-right-radius: 12px;
}}

/* ===== Text Edit (Log) ===== */
QTextEdit {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 12px;
    padding: 16px;
    font-family: 'Monaco', 'Menlo', 'SF Mono', 'Courier New';
    font-size: 12px;
    line-height: 1.5;
}}

/* ===== Scrollbar ===== */
QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    margin: 4px 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['bg_hover']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_tertiary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 8px;
    margin: 2px 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['bg_hover']};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['text_tertiary']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ===== Group Box ===== */
QGroupBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: 16px;
    padding: 20px;
    padding-top: 36px;
    font-weight: 500;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 20px;
    top: 8px;
    color: {COLORS['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ===== Splitter ===== */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

/* ===== Message Box ===== */
QMessageBox {{
    background-color: {COLORS['bg_secondary']};
}}

QMessageBox QLabel {{
    color: {COLORS['text_primary']};
}}

/* ===== Tooltips ===== */
QToolTip {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""

# Card widget style
CARD_STYLE = f"""
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
    padding: 20px;
"""

# Status indicator styles
STATUS_ACTIVE_STYLE = f"""
    color: {COLORS['status_active']};
    font-weight: 600;
"""

STATUS_INACTIVE_STYLE = f"""
    color: {COLORS['status_inactive']};
    font-weight: 500;
"""
