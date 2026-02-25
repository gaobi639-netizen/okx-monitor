"""Main application window - lead trader monitor."""

import re
from typing import Optional, List, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QFrame,
    QLineEdit, QListWidget, QListWidgetItem, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QDialog, QDialogButtonBox, QFormLayout, QInputDialog, QMenu,
    QTabWidget, QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from config import ConfigManager
from core.okx_client import OKXClient, Trader, Position
from core.monitor import LeadTraderMonitor, MonitorThread, TradeSignal
from core.notifier import TelegramNotifier, NotifierThread

from .styles import STYLESHEET, COLORS


class LoadTradersThread(QThread):
    """Thread for loading traders from API."""
    finished_loading = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, client: OKXClient):
        super().__init__()
        self.client = client

    def run(self):
        try:
            traders = self.client.get_lead_traders(limit=200)
            self.finished_loading.emit(traders)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main window for monitoring lead traders."""

    def __init__(self):
        super().__init__()

        self.config_manager = ConfigManager()
        self.okx_client: Optional[OKXClient] = None
        self.notifier = TelegramNotifier()
        self.monitor: Optional[LeadTraderMonitor] = None
        self.monitor_thread: Optional[MonitorThread] = None
        self._notifier_threads: List[NotifierThread] = []
        self._trader_positions: Dict[str, List[Position]] = {}
        self._trader_info: Dict[str, Trader] = {}
        self._load_thread: Optional[LoadTradersThread] = None
        self._hot_traders: List[Trader] = []

        self._init_ui()
        self._apply_config()

    def _init_ui(self) -> None:
        """Initialize UI."""
        self.setWindowTitle("OKX 交易员监控")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # Header
        header = self._create_header()
        main_layout.addLayout(header)

        # Log area (collapsible)
        log_area = self._create_log_area()
        main_layout.addWidget(log_area)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_secondary']};
                padding: 10px 20px;
                margin-right: 4px;
                border-radius: 6px 6px 0 0;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
            }}
        """)

        # Tab 1: 交易员管理
        tab1 = self._create_traders_tab()
        self.tabs.addTab(tab1, "📋 交易员管理")

        # Tab 2: 实时监控
        tab2 = self._create_monitor_tab()
        self.tabs.addTab(tab2, "📊 实时监控")

        # Refresh positions when switching to monitor tab
        self.tabs.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tabs, 1)

    def _create_header(self) -> QHBoxLayout:
        """Create header."""
        header = QHBoxLayout()
        header.setSpacing(12)

        # Title
        title = QLabel("OKX 交易员监控")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)

        header.addStretch()

        # Status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {COLORS['status_inactive']}; font-size: 14px;")
        header.addWidget(self.status_dot)

        self.status_label = QLabel("未运行")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header.addWidget(self.status_label)

        # Start button
        self.start_btn = QPushButton("▶ 开始监控")
        self.start_btn.setProperty("class", "primary")
        self.start_btn.setFixedHeight(36)
        self.start_btn.setMinimumWidth(100)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._toggle_monitoring)
        header.addWidget(self.start_btn)

        # Settings button with text
        settings_btn = QPushButton("⚙ 设置")
        settings_btn.setFixedHeight(36)
        settings_btn.setMinimumWidth(70)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._show_settings)
        header.addWidget(settings_btn)

        return header

    def _create_log_area(self) -> QFrame:
        """Create log area."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)
        frame.setMaximumHeight(80)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        # Header row
        header_row = QHBoxLayout()
        label = QLabel("📝 系统日志")
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;")
        header_row.addWidget(label)
        header_row.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setStyleSheet(f"background: transparent; color: {COLORS['text_tertiary']}; border: none; font-size: 10px;")
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        header_row.addWidget(clear_btn)
        layout.addLayout(header_row)

        # Log text area with scroll
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_primary']};
                border: none;
                border-radius: 4px;
                color: {COLORS['text_secondary']};
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 10px;
                padding: 4px;
            }}
        """)
        self.log_text.setMaximumHeight(45)
        layout.addWidget(self.log_text)

        return frame

    def _create_traders_tab(self) -> QWidget:
        """Create traders management tab."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        # Left: Add + List
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        add_card = self._create_add_card()
        left_layout.addWidget(add_card)

        traders_card = self._create_traders_list_card()
        left_layout.addWidget(traders_card, 1)

        layout.addWidget(left, 1)

        # Right: Hot traders
        right_card = self._create_hot_traders_card()
        layout.addWidget(right_card, 1)

        return tab

    def _create_monitor_tab(self) -> QWidget:
        """Create monitoring tab."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        # Left: All positions table
        positions_card = self._create_all_positions_card()
        layout.addWidget(positions_card, 3)

        # Right: Signals
        signals_card = self._create_signals_card()
        layout.addWidget(signals_card, 1)

        return tab

    def _create_card(self, title: str) -> tuple:
        """Create a card widget."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title_label)

        return card, layout

    def _create_add_card(self) -> QFrame:
        """Create add trader card."""
        card, layout = self._create_card("添加交易员")

        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("粘贴OKX链接或uniqueCode")
        self.add_input.setMinimumHeight(36)
        self.add_input.returnPressed.connect(self._add_trader)
        input_row.addWidget(self.add_input, 1)

        add_btn = QPushButton("添加")
        add_btn.setProperty("class", "primary")
        add_btn.setMinimumHeight(36)
        add_btn.setMinimumWidth(60)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_trader)
        input_row.addWidget(add_btn)

        layout.addLayout(input_row)

        hint = QLabel("支持: OKX链接、短链接(oyidl.net)、uniqueCode")
        hint.setStyleSheet(f"color: {COLORS['text_tertiary']}; font-size: 10px; background: transparent;")
        layout.addWidget(hint)

        return card

    def _create_traders_list_card(self) -> QFrame:
        """Create monitored traders list card."""
        card, layout = self._create_card("监控列表")

        header_row = QHBoxLayout()
        self.traders_count = QLabel("0 个交易员")
        self.traders_count.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;")
        header_row.addWidget(self.traders_count)
        header_row.addStretch()

        hint = QLabel("双击修改备注")
        hint.setStyleSheet(f"color: {COLORS['text_tertiary']}; font-size: 10px; background: transparent;")
        header_row.addWidget(hint)
        layout.addLayout(header_row)

        self.traders_list = QListWidget()
        self.traders_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {COLORS['border']};
                color: {COLORS['text_primary']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_blue']};
            }}
        """)
        self.traders_list.itemDoubleClicked.connect(self._edit_trader_nickname)
        self.traders_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.traders_list.customContextMenuRequested.connect(self._show_trader_context_menu)
        layout.addWidget(self.traders_list, 1)

        remove_btn = QPushButton("移除选中")
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['accent_red']};
                border: 1px solid {COLORS['accent_red']};
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_red']};
                color: white;
            }}
        """)
        remove_btn.clicked.connect(self._remove_trader)
        layout.addWidget(remove_btn)

        return card

    def _create_hot_traders_card(self) -> QFrame:
        """Create hot traders card."""
        card, layout = self._create_card("🔥 热门交易员")

        refresh_row = QHBoxLayout()
        self.hot_status = QLabel("")
        self.hot_status.setStyleSheet(f"color: {COLORS['text_tertiary']}; font-size: 10px; background: transparent;")
        refresh_row.addWidget(self.hot_status)
        refresh_row.addStretch()

        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: #0077ed;
            }}
        """)
        refresh_btn.clicked.connect(self._load_hot_traders)
        refresh_row.addWidget(refresh_btn)
        layout.addLayout(refresh_row)

        self.hot_table = QTableWidget()
        self.hot_table.setColumnCount(4)
        self.hot_table.setHorizontalHeaderLabels(["交易员", "收益率", "胜率", ""])
        self.hot_table.setShowGrid(False)
        self.hot_table.verticalHeader().setVisible(False)
        self.hot_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hot_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)

        header = self.hot_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.hot_table.setColumnWidth(1, 120)  # 收益率 - wider for "+1234.5%"
        self.hot_table.setColumnWidth(2, 80)   # 胜率
        self.hot_table.setColumnWidth(3, 40)

        self.hot_table.cellDoubleClicked.connect(self._on_hot_trader_double_click)
        layout.addWidget(self.hot_table, 1)

        return card

    def _create_all_positions_card(self) -> QFrame:
        """Create all positions card."""
        card, layout = self._create_card("所有交易员持仓")

        self.all_positions_info = QLabel("添加交易员后开始监控")
        self.all_positions_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; background: transparent;")
        layout.addWidget(self.all_positions_info)

        self.all_positions_table = QTableWidget()
        self.all_positions_table.setColumnCount(7)
        self.all_positions_table.setHorizontalHeaderLabels(["交易员", "币种", "方向", "数量", "均价", "盈亏", "杠杆"])
        self.all_positions_table.setShowGrid(False)
        self.all_positions_table.setAlternatingRowColors(True)
        self.all_positions_table.verticalHeader().setVisible(False)
        self.all_positions_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
        """)

        header = self.all_positions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 交易员 - 自动填充
        self.all_positions_table.setColumnWidth(1, 100)   # 币种 - BTC-USDT等
        self.all_positions_table.setColumnWidth(2, 55)    # 方向
        self.all_positions_table.setColumnWidth(3, 110)   # 数量 - 10,000.00
        self.all_positions_table.setColumnWidth(4, 120)   # 均价 - $95,000.00
        self.all_positions_table.setColumnWidth(5, 120)   # 盈亏 - +$10,000
        self.all_positions_table.setColumnWidth(6, 55)    # 杠杆

        layout.addWidget(self.all_positions_table, 1)

        return card

    def _create_signals_card(self) -> QFrame:
        """Create signals card."""
        card, layout = self._create_card("交易信号")

        self.signals_list = QListWidget()
        self.signals_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        layout.addWidget(self.signals_list, 1)

        clear_btn = QPushButton("清空信号")
        clear_btn.setStyleSheet(f"background: transparent; color: {COLORS['text_tertiary']}; border: none; font-size: 10px;")
        clear_btn.clicked.connect(lambda: self.signals_list.clear())
        layout.addWidget(clear_btn)

        return card

    def _load_hot_traders(self) -> None:
        """Load hot traders."""
        if not self.okx_client:
            QMessageBox.warning(self, "提示", "请先配置 OKX API")
            return

        self.hot_status.setText("加载中...")
        self._load_thread = LoadTradersThread(self.okx_client)
        self._load_thread.finished_loading.connect(self._on_hot_traders_loaded)
        self._load_thread.error.connect(lambda e: self.hot_status.setText(f"失败: {e[:20]}"))
        self._load_thread.start()

    def _on_hot_traders_loaded(self, traders: List[Trader]) -> None:
        """Handle hot traders loaded."""
        self._hot_traders = traders
        self.hot_status.setText(f"共 {len(traders)} 个，双击添加")
        self.hot_table.setRowCount(len(traders))

        for row, trader in enumerate(traders):
            self.hot_table.setRowHeight(row, 34)

            name_item = QTableWidgetItem(trader.nick_name)
            name_item.setData(Qt.ItemDataRole.UserRole, trader.unique_code)
            self.hot_table.setItem(row, 0, name_item)

            try:
                ratio = float(trader.pnl_ratio) * 100
                ratio_text = f"+{ratio:.1f}%" if ratio >= 0 else f"{ratio:.1f}%"
                ratio_item = QTableWidgetItem(ratio_text)
                ratio_item.setForeground(QColor(COLORS['accent_green'] if ratio >= 0 else COLORS['accent_red']))
                ratio_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            except:
                ratio_item = QTableWidgetItem("-")
            self.hot_table.setItem(row, 1, ratio_item)

            try:
                win = float(trader.win_ratio) * 100
                win_item = QTableWidgetItem(f"{win:.1f}%")
                win_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            except:
                win_item = QTableWidgetItem("-")
            self.hot_table.setItem(row, 2, win_item)

            add_item = QTableWidgetItem("+")
            add_item.setForeground(QColor(COLORS['accent_blue']))
            add_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.hot_table.setItem(row, 3, add_item)

        self._log(f"已加载 {len(traders)} 个热门交易员")

    def _on_hot_trader_double_click(self, row: int, col: int) -> None:
        """Handle hot trader double click."""
        if row < len(self._hot_traders):
            trader = self._hot_traders[row]
            self._add_trader_object(trader)

            added_item = QTableWidgetItem("✓")
            added_item.setForeground(QColor(COLORS['text_tertiary']))
            added_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.hot_table.setItem(row, 3, added_item)

    def _get_display_name(self, unique_code: str) -> str:
        """Get display name for a trader."""
        nickname = self.config_manager.get_trader_nickname(unique_code)
        if nickname:
            return nickname
        trader = self._trader_info.get(unique_code)
        if trader:
            return trader.nick_name
        return f"Trader-{unique_code[:8]}"

    def _edit_trader_nickname(self, item: QListWidgetItem) -> None:
        """Edit trader nickname."""
        code = item.data(Qt.ItemDataRole.UserRole)
        current_nickname = self.config_manager.get_trader_nickname(code) or ""
        trader = self._trader_info.get(code)
        original_name = trader.nick_name if trader else code[:8]

        nickname, ok = QInputDialog.getText(
            self, "设置备注",
            f"为 {original_name} 设置备注：",
            QLineEdit.EchoMode.Normal, current_nickname
        )

        if ok:
            self.config_manager.set_trader_nickname(code, nickname.strip())
            self._update_trader_list_item(item, code)
            if self.monitor:
                for t in self.monitor.get_monitored_traders():
                    if t.unique_code == code:
                        t.nick_name = self._get_display_name(code)
                        break
            self._log(f"备注已更新: {self._get_display_name(code)}")

    def _update_trader_list_item(self, item: QListWidgetItem, code: str) -> None:
        """Update trader list item display."""
        nickname = self.config_manager.get_trader_nickname(code)
        trader = self._trader_info.get(code)
        original_name = trader.nick_name if trader else code[:8]

        if nickname:
            item.setText(f"📝 {nickname}  ({original_name})")
        else:
            item.setText(original_name)

    def _show_trader_context_menu(self, pos) -> None:
        """Show context menu for trader list."""
        item = self.traders_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 12px;
                color: {COLORS['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['bg_hover']};
            }}
        """)

        edit_action = menu.addAction("✏️ 修改备注")
        edit_action.triggered.connect(lambda: self._edit_trader_nickname(item))

        remove_action = menu.addAction("🗑️ 移除")
        remove_action.triggered.connect(self._remove_trader)

        menu.exec(self.traders_list.mapToGlobal(pos))

    def _add_trader(self) -> None:
        """Add a trader to monitor."""
        text = self.add_input.text().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入链接或uniqueCode")
            return

        if not self.okx_client:
            QMessageBox.warning(self, "提示", "请先配置 OKX API")
            return

        self._log(f"解析: {text[:40]}...")

        code = self.okx_client.extract_unique_code(text)
        if not code:
            QMessageBox.warning(self, "提示", "无法识别格式")
            return

        self._log(f"uniqueCode: {code}")

        if self.monitor:
            if any(t.unique_code == code for t in self.monitor.get_monitored_traders()):
                QMessageBox.warning(self, "提示", "已在列表中")
                return

        positions = self.okx_client.get_lead_positions(code)

        trader = Trader(
            unique_code=code,
            nick_name=f"Trader-{code[:8]}",
            portrait="",
            pnl="0",
            pnl_ratio="0",
            win_ratio="0"
        )

        self._add_trader_object(trader, positions)

        nickname, ok = QInputDialog.getText(
            self, "设置备注",
            "为交易员设置备注（可跳过）：",
            QLineEdit.EchoMode.Normal, ""
        )

        if ok and nickname.strip():
            self.config_manager.set_trader_nickname(code, nickname.strip())
            for i in range(self.traders_list.count()):
                item = self.traders_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == code:
                    self._update_trader_list_item(item, code)
                    break
            if self.monitor:
                for t in self.monitor.get_monitored_traders():
                    if t.unique_code == code:
                        t.nick_name = self._get_display_name(code)
                        break
            self._refresh_all_positions()

    def _add_trader_object(self, trader: Trader, positions: Optional[List[Position]] = None) -> None:
        """Add a trader object to monitor."""
        if not self.monitor:
            if not self.okx_client:
                QMessageBox.warning(self, "提示", "请先配置 OKX API")
                return
            self.monitor = LeadTraderMonitor(self.okx_client)
            # Connect monitor signals for position updates
            self.monitor.positions_updated.connect(self._on_positions_updated)
            self.monitor.log_message.connect(self._log)

        if any(t.unique_code == trader.unique_code for t in self.monitor.get_monitored_traders()):
            self._log(f"{trader.nick_name} 已在列表中")
            return

        self._trader_info[trader.unique_code] = trader
        display_name = self._get_display_name(trader.unique_code)

        trader_copy = Trader(
            unique_code=trader.unique_code,
            nick_name=display_name,
            portrait=trader.portrait,
            pnl=trader.pnl,
            pnl_ratio=trader.pnl_ratio,
            win_ratio=trader.win_ratio
        )

        self.monitor.add_trader(trader_copy)

        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, trader.unique_code)
        self._update_trader_list_item(item, trader.unique_code)
        self.traders_list.addItem(item)
        self._update_traders_count()

        self.add_input.clear()

        # Always fetch positions from API
        final_positions = []
        if self.okx_client:
            self._log(f"正在获取 {display_name} 的持仓...")
            fetched_positions = self.okx_client.get_lead_positions(trader.unique_code)
            self._log(f"API返回: {len(fetched_positions)} 个持仓")
            if fetched_positions:
                final_positions = fetched_positions
        elif positions:
            final_positions = positions

        # Store positions with trader info
        for pos in final_positions:
            pos.trader_code = trader.unique_code
            pos.trader_name = display_name

        self._trader_positions[trader.unique_code] = final_positions
        self._log(f"已添加: {display_name}，存储 {len(final_positions)} 个持仓")
        self._log(f"当前共监控 {len(self._trader_positions)} 个交易员")

        # 同步到云服务器
        self._sync_add_trader(trader.unique_code, display_name)

        # Force refresh the positions table
        self._refresh_all_positions()

    def _remove_trader(self) -> None:
        """Remove selected trader."""
        current = self.traders_list.currentItem()
        if not current:
            QMessageBox.warning(self, "提示", "请先选择交易员")
            return

        code = current.data(Qt.ItemDataRole.UserRole)
        display_name = self._get_display_name(code)

        if self.monitor:
            self.monitor.remove_trader(code)

        self.traders_list.takeItem(self.traders_list.currentRow())
        self._trader_positions.pop(code, None)
        self._trader_info.pop(code, None)
        self.config_manager.remove_trader_nickname(code)
        self._update_traders_count()

        self._log(f"已移除: {display_name}")

        # 同步到云服务器
        self._sync_remove_trader(code)
        self._refresh_all_positions()

    def _update_traders_count(self) -> None:
        """Update traders count label."""
        count = self.traders_list.count()
        self.traders_count.setText(f"{count} 个交易员")

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        if index == 1:  # Monitor tab
            self._refresh_all_positions()

    def _refresh_all_positions(self) -> None:
        """Refresh all positions table."""
        all_positions = []
        trader_count = len(self._trader_positions)

        for code, positions in self._trader_positions.items():
            display_name = self._get_display_name(code)
            for pos in positions:
                pos.trader_name = display_name
                pos.trader_code = code
                all_positions.append(pos)

        self._log(f"刷新持仓表: {trader_count}个交易员, {len(all_positions)}个持仓")
        self._show_all_positions(all_positions)

    def _show_all_positions(self, all_positions: List[Position]) -> None:
        """Display all positions in one table."""
        self.all_positions_info.setText(f"共 {len(all_positions)} 个持仓")
        self.all_positions_table.setRowCount(len(all_positions))

        for row, pos in enumerate(all_positions):
            self.all_positions_table.setRowHeight(row, 36)

            # 交易员名称
            trader_name = pos.trader_name or self._get_display_name(pos.trader_code)
            name_item = QTableWidgetItem(trader_name)
            name_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.all_positions_table.setItem(row, 0, name_item)

            # 币种 - 处理空值
            if pos.inst_id:
                coin = pos.inst_id.replace('-USDT-SWAP', '').replace('-SWAP', '')
            else:
                coin = "隐藏"
            coin_item = QTableWidgetItem(coin)
            if not pos.inst_id:
                coin_item.setForeground(QColor(COLORS['text_tertiary']))
            self.all_positions_table.setItem(row, 1, coin_item)

            # 方向
            side_text = "🟢多" if pos.pos_side == "long" else "🔴空"
            self.all_positions_table.setItem(row, 2, QTableWidgetItem(side_text))

            # 数量 - 处理空值
            if pos.pos and pos.pos != '0':
                try:
                    size = float(pos.pos)
                    size_text = f"{size:,.2f}"
                except:
                    size_text = pos.pos
            else:
                size_text = "-"
            size_item = QTableWidgetItem(size_text)
            if size_text == "-":
                size_item.setForeground(QColor(COLORS['text_tertiary']))
            self.all_positions_table.setItem(row, 3, size_item)

            # 均价 - 处理空值
            if pos.avg_px and pos.avg_px != '0':
                try:
                    price = float(pos.avg_px)
                    price_text = f"${price:,.2f}"
                except:
                    price_text = pos.avg_px
            else:
                price_text = "-"
            price_item = QTableWidgetItem(price_text)
            if price_text == "-":
                price_item.setForeground(QColor(COLORS['text_tertiary']))
            self.all_positions_table.setItem(row, 4, price_item)

            # 盈亏
            try:
                upl = float(pos.upl)
                pnl_text = f"+${upl:,.0f}" if upl >= 0 else f"-${abs(upl):,.0f}"
                pnl_item = QTableWidgetItem(pnl_text)
                pnl_item.setForeground(QColor(COLORS['accent_green'] if upl >= 0 else COLORS['accent_red']))
            except:
                pnl_item = QTableWidgetItem("-")
                pnl_item.setForeground(QColor(COLORS['text_tertiary']))
            self.all_positions_table.setItem(row, 5, pnl_item)

            # 杠杆
            lever_text = f"{pos.lever}x" if pos.lever else "-"
            self.all_positions_table.setItem(row, 6, QTableWidgetItem(lever_text))

    def _apply_config(self) -> None:
        """Apply config."""
        config = self.config_manager.config

        if config.okx.api_key and config.okx.secret_key:
            self.okx_client = OKXClient(
                config.okx.api_key, config.okx.secret_key,
                config.okx.passphrase, config.okx.base_url
            )
            self._log("OKX 已配置")

        if config.telegram.bot_token and config.telegram.chat_id:
            self.notifier.configure(config.telegram.bot_token, config.telegram.chat_id)
            self._log("Telegram 已配置")

    def _log(self, message: str) -> None:
        """Add log message."""
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{time_str}] {message}")
        # Auto scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _show_settings(self) -> None:
        """Show settings dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙ 设置")
        dialog.setMinimumWidth(420)
        dialog.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("应用设置")
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['text_primary']}; margin-bottom: 10px;")
        layout.addWidget(title)

        form = QFormLayout()

        # OKX section
        okx_label = QLabel("OKX API 配置")
        okx_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['accent_blue']}; margin-top: 10px;")
        layout.addWidget(okx_label)

        self.api_key_input = QLineEdit(self.config_manager.config.okx.api_key)
        self.api_key_input.setMinimumHeight(34)
        form.addRow("API Key:", self.api_key_input)

        self.secret_key_input = QLineEdit(self.config_manager.config.okx.secret_key)
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.secret_key_input.setMinimumHeight(34)
        form.addRow("Secret Key:", self.secret_key_input)

        self.passphrase_input = QLineEdit(self.config_manager.config.okx.passphrase)
        self.passphrase_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.passphrase_input.setMinimumHeight(34)
        form.addRow("Passphrase:", self.passphrase_input)

        layout.addLayout(form)

        # Telegram section
        tg_label = QLabel("Telegram 配置")
        tg_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['accent_green']}; margin-top: 15px;")
        layout.addWidget(tg_label)

        form2 = QFormLayout()
        self.bot_token_input = QLineEdit(self.config_manager.config.telegram.bot_token)
        self.bot_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.bot_token_input.setMinimumHeight(34)
        form2.addRow("Bot Token:", self.bot_token_input)

        self.chat_id_input = QLineEdit(self.config_manager.config.telegram.chat_id)
        self.chat_id_input.setMinimumHeight(34)
        form2.addRow("Chat ID:", self.chat_id_input)

        layout.addLayout(form2)

        # Monitor section
        mon_label = QLabel("监控配置")
        mon_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['accent_orange']}; margin-top: 15px;")
        layout.addWidget(mon_label)

        form3 = QFormLayout()
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 60)
        self.interval_spin.setValue(self.config_manager.config.monitor.poll_interval)
        self.interval_spin.setSuffix(" 秒")
        self.interval_spin.setMinimumHeight(34)
        form3.addRow("轮询间隔:", self.interval_spin)

        layout.addLayout(form3)

        layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self._save_settings(dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec()

    def _save_settings(self, dialog) -> None:
        """Save settings."""
        self.config_manager.update_okx(
            self.api_key_input.text().strip(),
            self.secret_key_input.text().strip(),
            self.passphrase_input.text().strip()
        )
        self.config_manager.update_telegram(
            self.bot_token_input.text().strip(),
            self.chat_id_input.text().strip()
        )
        self.config_manager.update_monitor(self.interval_spin.value(), True)

        self._apply_config()
        dialog.accept()
        QMessageBox.information(self, "成功", "设置已保存")

    def _toggle_monitoring(self) -> None:
        """Toggle monitoring."""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self) -> None:
        """Start monitoring."""
        if not self.okx_client:
            QMessageBox.warning(self, "提示", "请先配置 OKX API")
            return

        if not self.monitor or not self.monitor.get_monitored_traders():
            QMessageBox.warning(self, "提示", "请先添加交易员")
            return

        interval = self.config_manager.config.monitor.poll_interval
        self.monitor_thread = MonitorThread(self.monitor, interval)

        self.monitor_thread.signal_detected.connect(self._on_signal)
        self.monitor_thread.log_message.connect(self._log)
        self.monitor_thread.error_occurred.connect(self._log)
        self.monitor_thread.positions_updated.connect(self._on_positions_updated)

        self.monitor_thread.start()

        self.status_dot.setStyleSheet(f"color: {COLORS['status_active']}; font-size: 14px;")
        self.status_label.setText("监控中")
        self.status_label.setStyleSheet(f"color: {COLORS['status_active']};")
        self.start_btn.setText("⏹ 停止")
        self.start_btn.setProperty("class", "danger")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

        self.tabs.setCurrentIndex(1)
        self._log("监控已启动")

    def _stop_monitoring(self) -> None:
        """Stop monitoring."""
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            self.monitor_thread = None

        self.status_dot.setStyleSheet(f"color: {COLORS['status_inactive']}; font-size: 14px;")
        self.status_label.setText("未运行")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.start_btn.setText("▶ 开始监控")
        self.start_btn.setProperty("class", "primary")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

        self._log("监控已停止")

    @pyqtSlot(str, list)
    def _on_positions_updated(self, trader_code: str, positions: List[Position]) -> None:
        """Handle positions update."""
        display_name = self._get_display_name(trader_code)
        for pos in positions:
            pos.trader_code = trader_code
            pos.trader_name = display_name

        self._trader_positions[trader_code] = positions
        self._refresh_all_positions()

    @pyqtSlot(TradeSignal)
    def _on_signal(self, signal: TradeSignal) -> None:
        """Handle trade signal."""
        action_colors = {
            "开多": COLORS['accent_green'],
            "开空": COLORS['accent_red'],
            "平多": COLORS['accent_cyan'],
            "平空": COLORS['accent_orange'],
            "加多": COLORS['accent_green'],
            "加空": COLORS['accent_red'],
            "减多": COLORS['accent_cyan'],
            "减空": COLORS['accent_orange'],
        }

        color = action_colors.get(signal.action.value, COLORS['text_primary'])
        coin = signal.inst_id.split('-')[0]
        display_name = self._get_display_name(signal.trader_code)

        try:
            qty = float(signal.quantity)
            qty_str = f"{qty:,.2f}"
        except:
            qty_str = signal.quantity

        text = f"【{display_name}】{signal.action.value} {coin} | 数量:{qty_str}"

        item = QListWidgetItem(text)
        item.setForeground(QColor(color))
        self.signals_list.insertItem(0, item)

        self._log(f"🔔 {display_name} {signal.action.value} {coin}")

        if self.notifier.bot_token and self.notifier.chat_id:
            msg = signal.to_message().replace(signal.trader_name, display_name)
            thread = NotifierThread(self.notifier, msg)
            thread.finished_sending.connect(
                lambda ok, _: self._log("Telegram 已发送" if ok else "发送失败")
            )
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self._notifier_threads.append(thread)
            thread.start()

    def _cleanup_thread(self, thread) -> None:
        if thread in self._notifier_threads:
            self._notifier_threads.remove(thread)

    def _sync_add_trader(self, code: str, name: str) -> None:
        """同步添加交易员到云服务器"""
        if not self.notifier.bot_token or not self.notifier.chat_id:
            return

        try:
            import requests
            url = f"https://api.telegram.org/bot{self.notifier.bot_token}/sendMessage"
            data = {
                "chat_id": self.notifier.chat_id,
                "text": f"/sync_add {code} {name}"
            }
            requests.post(url, data=data, timeout=5)
            self._log(f"已同步到云服务器: 添加 {name}")
        except Exception as e:
            self._log(f"同步失败: {e}")

    def _sync_remove_trader(self, code: str) -> None:
        """同步删除交易员到云服务器"""
        if not self.notifier.bot_token or not self.notifier.chat_id:
            return

        try:
            import requests
            url = f"https://api.telegram.org/bot{self.notifier.bot_token}/sendMessage"
            data = {
                "chat_id": self.notifier.chat_id,
                "text": f"/sync_remove {code}"
            }
            requests.post(url, data=data, timeout=5)
            self._log(f"已同步到云服务器: 删除")
        except Exception as e:
            self._log(f"同步失败: {e}")

    def closeEvent(self, event) -> None:
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()
        for t in self._notifier_threads:
            t.wait()
        event.accept()
