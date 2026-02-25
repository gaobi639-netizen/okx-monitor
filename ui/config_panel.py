"""Configuration panel with Apple-inspired design."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QMessageBox,
    QFrame, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt

from config import ConfigManager
from .styles import COLORS


class ConfigCard(QFrame):
    """A styled card container for configuration sections."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)
        self.layout.addWidget(title_label)

    def add_widget(self, widget):
        self.layout.addWidget(widget)

    def add_layout(self, layout):
        self.layout.addLayout(layout)


class ConfigPanel(QWidget):
    """Panel for configuring API credentials and settings."""

    config_changed = pyqtSignal()
    test_okx_requested = pyqtSignal()
    test_telegram_requested = pyqtSignal()

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self._init_ui()
        self._load_config()

    def _create_input_field(self, placeholder: str, password: bool = False) -> QLineEdit:
        """Create a styled input field."""
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(44)
        if password:
            field.setEchoMode(QLineEdit.EchoMode.Password)
        return field

    def _create_field_row(self, label: str, widget: QWidget) -> QVBoxLayout:
        """Create a labeled field row."""
        layout = QVBoxLayout()
        layout.setSpacing(8)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        layout.addWidget(label_widget)
        layout.addWidget(widget)

        return layout

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 4, 4)
        scroll_layout.setSpacing(20)

        # OKX Configuration Card
        okx_card = ConfigCard("OKX API")

        self.api_key_input = self._create_input_field("输入 API Key")
        okx_card.add_layout(self._create_field_row("API Key", self.api_key_input))

        self.secret_key_input = self._create_input_field("输入 Secret Key", password=True)
        okx_card.add_layout(self._create_field_row("Secret Key", self.secret_key_input))

        self.passphrase_input = self._create_input_field("输入 Passphrase", password=True)
        okx_card.add_layout(self._create_field_row("Passphrase", self.passphrase_input))

        self.test_okx_btn = QPushButton("测试连接")
        self.test_okx_btn.setProperty("class", "small")
        self.test_okx_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_okx_btn.clicked.connect(self.test_okx_requested.emit)
        okx_card.add_widget(self.test_okx_btn)

        scroll_layout.addWidget(okx_card)

        # Telegram Configuration Card
        telegram_card = ConfigCard("TELEGRAM")

        self.bot_token_input = self._create_input_field("输入 Bot Token", password=True)
        telegram_card.add_layout(self._create_field_row("Bot Token", self.bot_token_input))

        self.chat_id_input = self._create_input_field("输入 Chat ID")
        telegram_card.add_layout(self._create_field_row("Chat ID", self.chat_id_input))

        self.test_telegram_btn = QPushButton("测试连接")
        self.test_telegram_btn.setProperty("class", "small")
        self.test_telegram_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_telegram_btn.clicked.connect(self.test_telegram_requested.emit)
        telegram_card.add_widget(self.test_telegram_btn)

        scroll_layout.addWidget(telegram_card)

        # Monitor Settings Card
        monitor_card = ConfigCard("监控设置")

        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(12)

        interval_label = QLabel("轮询间隔")
        interval_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        interval_layout.addWidget(interval_label)

        interval_layout.addStretch()

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 60)
        self.interval_spin.setValue(10)
        self.interval_spin.setSuffix(" 秒")
        self.interval_spin.setMinimumWidth(100)
        self.interval_spin.setMinimumHeight(40)
        interval_layout.addWidget(self.interval_spin)

        monitor_card.add_layout(interval_layout)

        scroll_layout.addWidget(monitor_card)

        # Save button
        self.save_btn = QPushButton("保存配置")
        self.save_btn.setProperty("class", "primary")
        self.save_btn.setMinimumHeight(48)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._save_config)
        scroll_layout.addWidget(self.save_btn)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _load_config(self) -> None:
        """Load configuration into UI."""
        config = self.config_manager.config

        self.api_key_input.setText(config.okx.api_key)
        self.secret_key_input.setText(config.okx.secret_key)
        self.passphrase_input.setText(config.okx.passphrase)

        self.bot_token_input.setText(config.telegram.bot_token)
        self.chat_id_input.setText(config.telegram.chat_id)

        self.interval_spin.setValue(config.monitor.poll_interval)

    def _save_config(self) -> None:
        """Save configuration from UI."""
        self.config_manager.update_okx(
            self.api_key_input.text().strip(),
            self.secret_key_input.text().strip(),
            self.passphrase_input.text().strip()
        )

        self.config_manager.update_telegram(
            self.bot_token_input.text().strip(),
            self.chat_id_input.text().strip()
        )

        self.config_manager.update_monitor(
            self.interval_spin.value(),
            self.config_manager.config.monitor.enabled
        )

        self.config_changed.emit()
        QMessageBox.information(self, "成功", "配置已保存")

    def get_okx_credentials(self) -> tuple:
        """Get current OKX credentials from UI."""
        return (
            self.api_key_input.text().strip(),
            self.secret_key_input.text().strip(),
            self.passphrase_input.text().strip()
        )

    def get_telegram_credentials(self) -> tuple:
        """Get current Telegram credentials from UI."""
        return (
            self.bot_token_input.text().strip(),
            self.chat_id_input.text().strip()
        )

    def get_poll_interval(self) -> int:
        """Get current poll interval setting."""
        return self.interval_spin.value()
