"""Log panel with Apple-inspired design."""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QFrame
)
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QTextCursor

from core.monitor import TradeSignal
from .styles import COLORS


class LogPanel(QWidget):
    """Panel for displaying log messages and trade signals."""

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Log container
        log_container = QFrame()
        log_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)

        container_layout = QVBoxLayout(log_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_tertiary']};
                border: none;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                padding: 12px 16px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        # Terminal dots
        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(8)

        for color in ['#ff5f57', '#febc2e', '#28c840']:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent;")
            dots_layout.addWidget(dot)

        header_layout.addLayout(dots_layout)
        header_layout.addStretch()

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: {COLORS['text_primary']};
            }}
        """)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self._clear_log)
        header_layout.addWidget(self.clear_btn)

        container_layout.addWidget(header)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
                padding: 16px;
                font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.6;
            }}
        """)

        container_layout.addWidget(self.log_text, 1)

        layout.addWidget(log_container)

    def _clear_log(self) -> None:
        """Clear the log display."""
        self.log_text.clear()

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        return datetime.now().strftime("%H:%M:%S")

    def _append_html(self, html: str) -> None:
        """Append HTML content to log."""
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
        self.log_text.insertHtml(html + "<br>")
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    @pyqtSlot(str)
    def log_info(self, message: str) -> None:
        """Log an info message."""
        timestamp = self._get_timestamp()
        html = f'''
        <span style="color: {COLORS['text_tertiary']};">{timestamp}</span>
        <span style="color: {COLORS['text_secondary']};">&nbsp;&nbsp;{message}</span>
        '''
        self._append_html(html)

    @pyqtSlot(str)
    def log_success(self, message: str) -> None:
        """Log a success message."""
        timestamp = self._get_timestamp()
        html = f'''
        <span style="color: {COLORS['text_tertiary']};">{timestamp}</span>
        <span style="color: {COLORS['accent_green']};">&nbsp;&nbsp;✓ {message}</span>
        '''
        self._append_html(html)

    @pyqtSlot(str)
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        timestamp = self._get_timestamp()
        html = f'''
        <span style="color: {COLORS['text_tertiary']};">{timestamp}</span>
        <span style="color: {COLORS['accent_orange']};">&nbsp;&nbsp;⚠ {message}</span>
        '''
        self._append_html(html)

    @pyqtSlot(str)
    def log_error(self, message: str) -> None:
        """Log an error message."""
        timestamp = self._get_timestamp()
        html = f'''
        <span style="color: {COLORS['text_tertiary']};">{timestamp}</span>
        <span style="color: {COLORS['accent_red']};">&nbsp;&nbsp;✗ {message}</span>
        '''
        self._append_html(html)

    @pyqtSlot(TradeSignal)
    def log_signal(self, signal: TradeSignal) -> None:
        """Log a trade signal."""
        timestamp = self._get_timestamp()

        # Color based on action type
        if "OPEN" in signal.action.name or "ADD" in signal.action.name:
            if "LONG" in signal.action.name:
                color = COLORS['accent_green']
                icon = "▲"
            else:
                color = COLORS['accent_red']
                icon = "▼"
        else:
            color = COLORS['accent_cyan']
            icon = "◆"

        html = f'''
        <div style="margin: 8px 0; padding: 12px; background-color: {COLORS['bg_tertiary']}; border-radius: 8px;">
            <span style="color: {COLORS['text_tertiary']};">{timestamp}</span>
            <span style="color: {color}; font-weight: 600;">&nbsp;&nbsp;{icon} {signal.action.value}</span>
            <br>
            <span style="color: {COLORS['text_primary']}; font-weight: 500;">&nbsp;&nbsp;&nbsp;&nbsp;{signal.trader_name}</span>
            <span style="color: {COLORS['text_secondary']};">&nbsp;·&nbsp;{signal.inst_id}</span>
            <br>
            <span style="color: {COLORS['text_secondary']};">&nbsp;&nbsp;&nbsp;&nbsp;数量: {signal.quantity}&nbsp;&nbsp;价格: ${signal.price}</span>
        </div>
        '''
        self._append_html(html)
