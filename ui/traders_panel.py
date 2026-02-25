"""Traders panel with Apple-inspired design."""

from typing import Optional, Dict, List, Set
import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QLabel, QLineEdit, QSplitter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

from core.okx_client import Trader
from .styles import COLORS


class TradersPanel(QWidget):
    """Panel for displaying monitored traders."""

    trader_added = pyqtSignal(Trader)
    trader_removed = pyqtSignal(str)
    refresh_requested = pyqtSignal()
    search_requested = pyqtSignal(str)
    add_by_code_requested = pyqtSignal(str)  # Add by uniqueCode or URL

    def __init__(self):
        super().__init__()
        self.traders: Dict[str, Trader] = {}
        self.monitored_traders: Dict[str, Trader] = {}  # Track monitored traders
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # Create splitter for two panels
        splitter = QSplitter(Qt.Orientation.Vertical)

        # === Top Panel: Monitored Traders ===
        monitored_panel = QFrame()
        monitored_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        monitored_layout = QVBoxLayout(monitored_panel)
        monitored_layout.setContentsMargins(16, 16, 16, 16)
        monitored_layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        monitored_title = QLabel("已监控的交易员")
        monitored_title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(monitored_title)

        self.monitored_count = QLabel("0 个")
        self.monitored_count.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        header_layout.addWidget(self.monitored_count)
        header_layout.addStretch()

        self.remove_monitored_btn = QPushButton("移除选中")
        self.remove_monitored_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['accent_red']};
                border: none;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {COLORS['text_primary']};
            }}
        """)
        self.remove_monitored_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_monitored_btn.clicked.connect(self._remove_monitored_selected)
        header_layout.addWidget(self.remove_monitored_btn)

        monitored_layout.addLayout(header_layout)

        # Monitored list
        self.monitored_list = QListWidget()
        self.monitored_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border-radius: 6px;
                padding: 10px 12px;
                margin: 2px 4px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_blue']};
            }}
        """)
        self.monitored_list.setMinimumHeight(80)
        monitored_layout.addWidget(self.monitored_list)

        splitter.addWidget(monitored_panel)

        # === Bottom Panel: Add Traders ===
        add_panel = QFrame()
        add_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        add_layout = QVBoxLayout(add_panel)
        add_layout.setContentsMargins(16, 16, 16, 16)
        add_layout.setSpacing(12)

        # Title
        add_title = QLabel("添加交易员")
        add_title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        add_layout.addWidget(add_title)

        # Input for URL or code
        input_hint = QLabel("粘贴交易员主页链接或输入交易员 ID")
        input_hint.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        add_layout.addWidget(input_hint)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("https://www.okx.com/copy-trading/account/xxx 或 交易员ID")
        self.add_input.setMinimumHeight(44)
        self.add_input.returnPressed.connect(self._on_add_by_input)
        input_layout.addWidget(self.add_input, 1)

        self.add_btn = QPushButton("添加")
        self.add_btn.setProperty("class", "primary")
        self.add_btn.setMinimumHeight(44)
        self.add_btn.setMinimumWidth(80)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._on_add_by_input)
        input_layout.addWidget(self.add_btn)

        add_layout.addLayout(input_layout)

        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {COLORS['border']};")
        add_layout.addWidget(divider)

        # Hot traders button
        hot_layout = QHBoxLayout()
        hot_hint = QLabel("或从热门交易员中选择")
        hot_hint.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        hot_layout.addWidget(hot_hint)
        hot_layout.addStretch()

        self.refresh_btn = QPushButton("查看热门交易员")
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        hot_layout.addWidget(self.refresh_btn)

        add_layout.addLayout(hot_layout)

        # Table for search results
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["交易员", "收益", "收益率", "操作"])
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(60)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 80)

        self.table.setVisible(False)
        self.table.setMaximumHeight(200)
        add_layout.addWidget(self.table)

        splitter.addWidget(add_panel)

        # Set splitter sizes
        splitter.setSizes([150, 350])

        layout.addWidget(splitter)

    def _extract_unique_code(self, text: str) -> Optional[str]:
        """Extract uniqueCode from URL or return as-is if it's a code."""
        text = text.strip()

        # Try to extract from OKX URL
        # Format: https://www.okx.com/copy-trading/account/XXXXX
        patterns = [
            r'okx\.com/copy-trading/account/([A-Za-z0-9]+)',
            r'okx\.com/.*uniqueCode=([A-Za-z0-9]+)',
            r'^([A-Za-z0-9]{10,})$'  # Assume it's a code if alphanumeric and long enough
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        # If short text, assume it's a code or nickname
        if len(text) > 0:
            return text

        return None

    def _on_add_by_input(self) -> None:
        """Handle add by URL/code input."""
        text = self.add_input.text().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入交易员链接或ID")
            return

        code = self._extract_unique_code(text)
        if code:
            self.add_by_code_requested.emit(code)
        else:
            QMessageBox.warning(self, "提示", "无法识别的链接或ID格式")

    def add_monitored_trader(self, trader: Trader) -> None:
        """Add a trader to the monitored list."""
        if trader.unique_code in self.monitored_traders:
            return  # Already monitored

        self.monitored_traders[trader.unique_code] = trader

        item = QListWidgetItem(f"{trader.nick_name}  •  收益率 {float(trader.pnl_ratio)*100:.1f}%")
        item.setData(Qt.ItemDataRole.UserRole, trader.unique_code)
        self.monitored_list.addItem(item)

        self._update_monitored_count()

    def remove_monitored_trader(self, unique_code: str) -> None:
        """Remove a trader from the monitored list."""
        if unique_code in self.monitored_traders:
            del self.monitored_traders[unique_code]

        # Remove from list widget
        for i in range(self.monitored_list.count()):
            item = self.monitored_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == unique_code:
                self.monitored_list.takeItem(i)
                break

        self._update_monitored_count()

    def _remove_monitored_selected(self) -> None:
        """Remove selected trader from monitoring."""
        current = self.monitored_list.currentItem()
        if current:
            code = current.data(Qt.ItemDataRole.UserRole)
            self.trader_removed.emit(code)
            self.remove_monitored_trader(code)
        else:
            QMessageBox.warning(self, "提示", "请先选择要移除的交易员")

    def _update_monitored_count(self) -> None:
        """Update the monitored count label."""
        count = len(self.monitored_traders)
        self.monitored_count.setText(f"{count} 个")

    def set_traders(self, traders: List[Trader], monitored_codes: Optional[Set[str]] = None) -> None:
        """Update the traders list display."""
        monitored_codes = monitored_codes or set()
        self.traders.clear()

        if not traders:
            self.table.setVisible(False)
            return

        self.table.setVisible(True)
        self.table.setRowCount(len(traders))

        for row, trader in enumerate(traders):
            self.traders[trader.unique_code] = trader
            self.table.setRowHeight(row, 50)

            # Nickname
            name_item = QTableWidgetItem(trader.nick_name)
            name_item.setData(Qt.ItemDataRole.UserRole, trader.unique_code)
            name_item.setForeground(QColor(COLORS['text_primary']))
            self.table.setItem(row, 0, name_item)

            # PnL
            pnl = float(trader.pnl) if trader.pnl else 0
            pnl_text = f"${pnl:,.0f}"
            pnl_item = QTableWidgetItem(pnl_text)
            pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            pnl_item.setForeground(QColor(COLORS['accent_green']) if pnl >= 0 else QColor(COLORS['accent_red']))
            self.table.setItem(row, 1, pnl_item)

            # PnL Ratio
            pnl_ratio = float(trader.pnl_ratio) * 100 if trader.pnl_ratio else 0
            ratio_text = f"+{pnl_ratio:.0f}%" if pnl_ratio >= 0 else f"{pnl_ratio:.0f}%"
            ratio_item = QTableWidgetItem(ratio_text)
            ratio_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            ratio_item.setForeground(QColor(COLORS['accent_green']) if pnl_ratio >= 0 else QColor(COLORS['accent_red']))
            self.table.setItem(row, 2, ratio_item)

            # Add button
            if trader.unique_code in monitored_codes:
                btn_item = QTableWidgetItem("已添加")
                btn_item.setForeground(QColor(COLORS['text_tertiary']))
            else:
                btn_item = QTableWidgetItem("+ 添加")
                btn_item.setForeground(QColor(COLORS['accent_blue']))
            btn_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, btn_item)

        # Connect double click to add
        self.table.cellDoubleClicked.connect(self._on_table_double_click)

    def _on_table_double_click(self, row: int, col: int) -> None:
        """Handle double click on table row."""
        item = self.table.item(row, 0)
        if item:
            code = item.data(Qt.ItemDataRole.UserRole)
            trader = self.traders.get(code)
            if trader and code not in self.monitored_traders:
                self.trader_added.emit(trader)
                self.add_monitored_trader(trader)
                # Update button text
                btn_item = QTableWidgetItem("已添加")
                btn_item.setForeground(QColor(COLORS['text_tertiary']))
                btn_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, btn_item)

    def clear_input(self) -> None:
        """Clear the input field."""
        self.add_input.clear()
