"""Position monitoring for lead traders."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .okx_client import OKXClient, Trader, Position


class TradeAction(Enum):
    """Types of trading actions."""
    OPEN_LONG = "开多"
    OPEN_SHORT = "开空"
    CLOSE_LONG = "平多"
    CLOSE_SHORT = "平空"
    ADD_LONG = "加多"
    ADD_SHORT = "加空"
    REDUCE_LONG = "减多"
    REDUCE_SHORT = "减空"


@dataclass
class TradeSignal:
    """Represents a detected trade signal."""
    trader_code: str
    trader_name: str
    action: TradeAction
    inst_id: str
    pos_side: str
    quantity: str
    price: str
    timestamp: datetime
    prev_quantity: str = "0"

    def to_message(self) -> str:
        """Format signal as notification message."""
        action_emoji = {
            TradeAction.OPEN_LONG: "🟢 开多",
            TradeAction.OPEN_SHORT: "🔴 开空",
            TradeAction.CLOSE_LONG: "🔵 平多",
            TradeAction.CLOSE_SHORT: "🟠 平空",
            TradeAction.ADD_LONG: "🟢 加多",
            TradeAction.ADD_SHORT: "🔴 加空",
            TradeAction.REDUCE_LONG: "🔵 减多",
            TradeAction.REDUCE_SHORT: "🟠 减空",
        }

        direction = "做多" if self.pos_side == "long" else "做空"
        coin = self.inst_id.split('-')[0] if self.inst_id else "Unknown"

        msg = f"""🔔 交易员动态提醒

交易员: {self.trader_name}
操作: {action_emoji.get(self.action, self.action.value)}
币种: {self.inst_id}
方向: {direction}
数量: {self.quantity} {coin}
价格: ${self.price}

时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"""

        return msg


@dataclass
class TraderPosition:
    """Represents a trader's position for tracking."""
    inst_id: str
    pos_side: str
    pos: str
    avg_px: str

    @classmethod
    def from_position(cls, pos: Position) -> 'TraderPosition':
        return cls(
            inst_id=pos.inst_id,
            pos_side=pos.pos_side,
            pos=pos.pos,
            avg_px=pos.avg_px
        )

    @property
    def key(self) -> str:
        """Unique key for this position."""
        return f"{self.inst_id}_{self.pos_side}"


class LeadTraderMonitor(QObject):
    """Monitor lead traders' positions for changes."""

    signal_detected = pyqtSignal(TradeSignal)
    log_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    positions_updated = pyqtSignal(str, list)  # trader_code, positions

    def __init__(self, client: OKXClient):
        super().__init__()
        self.client = client
        self._cache: Dict[str, Dict[str, TraderPosition]] = {}
        self._traders: Dict[str, Trader] = {}
        self._first_run: Dict[str, bool] = {}

    def add_trader(self, trader: Trader) -> None:
        """Add a trader to monitor."""
        self._traders[trader.unique_code] = trader
        self._first_run[trader.unique_code] = True
        self._cache[trader.unique_code] = {}
        self.log_message.emit(f"已添加: {trader.nick_name}")

    def remove_trader(self, unique_code: str) -> None:
        """Remove a trader from monitoring."""
        if unique_code in self._traders:
            name = self._traders[unique_code].nick_name
            del self._traders[unique_code]
            self._first_run.pop(unique_code, None)
            self._cache.pop(unique_code, None)
            self.log_message.emit(f"已移除: {name}")

    def get_trader_name(self, unique_code: str) -> str:
        """Get trader name."""
        trader = self._traders.get(unique_code)
        return trader.nick_name if trader else unique_code[:8] + "..."

    def get_monitored_traders(self) -> List[Trader]:
        """Get list of monitored traders."""
        return list(self._traders.values())

    def check_positions(self) -> List[TradeSignal]:
        """Check for position changes across all traders."""
        signals = []

        for trader_code, trader in self._traders.items():
            try:
                trader_signals = self._check_trader_positions(trader_code)
                signals.extend(trader_signals)
            except Exception as e:
                self.error_occurred.emit(f"检查 {trader.nick_name} 失败: {str(e)}")

        return signals

    def _check_trader_positions(self, trader_code: str) -> List[TradeSignal]:
        """Check positions for a specific trader."""
        signals = []
        trader = self._traders.get(trader_code)
        if not trader:
            return signals

        # Get current positions
        positions = self.client.get_lead_positions(trader_code)

        # Set trader info on positions
        for pos in positions:
            pos.trader_code = trader_code
            pos.trader_name = trader.nick_name

        current_map: Dict[str, TraderPosition] = {}
        for pos in positions:
            tp = TraderPosition.from_position(pos)
            current_map[tp.key] = tp

        # Emit positions for UI
        self.positions_updated.emit(trader_code, positions)

        # Skip signal detection on first run
        if self._first_run.get(trader_code, True):
            self._cache[trader_code] = current_map
            self._first_run[trader_code] = False
            self.log_message.emit(f"{trader.nick_name}: {len(positions)} 个持仓")
            return signals

        now = datetime.now()
        old_map = self._cache.get(trader_code, {})

        # Detect changes
        all_keys = set(old_map.keys()) | set(current_map.keys())

        for key in all_keys:
            old_pos = old_map.get(key)
            new_pos = current_map.get(key)

            if new_pos and not old_pos:
                # New position opened
                action = TradeAction.OPEN_LONG if new_pos.pos_side == 'long' else TradeAction.OPEN_SHORT
                signal = TradeSignal(
                    trader_code=trader_code,
                    trader_name=trader.nick_name,
                    action=action,
                    inst_id=new_pos.inst_id,
                    pos_side=new_pos.pos_side,
                    quantity=new_pos.pos,
                    price=new_pos.avg_px,
                    timestamp=now
                )
                signals.append(signal)

            elif old_pos and not new_pos:
                # Position closed
                action = TradeAction.CLOSE_LONG if old_pos.pos_side == 'long' else TradeAction.CLOSE_SHORT
                signal = TradeSignal(
                    trader_code=trader_code,
                    trader_name=trader.nick_name,
                    action=action,
                    inst_id=old_pos.inst_id,
                    pos_side=old_pos.pos_side,
                    quantity=old_pos.pos,
                    price=old_pos.avg_px,
                    timestamp=now,
                    prev_quantity=old_pos.pos
                )
                signals.append(signal)

            elif old_pos and new_pos:
                # Check for size changes
                old_size = float(old_pos.pos)
                new_size = float(new_pos.pos)

                if abs(new_size - old_size) > 0.0001:
                    if new_size > old_size:
                        action = TradeAction.ADD_LONG if new_pos.pos_side == 'long' else TradeAction.ADD_SHORT
                    else:
                        action = TradeAction.REDUCE_LONG if new_pos.pos_side == 'long' else TradeAction.REDUCE_SHORT

                    signal = TradeSignal(
                        trader_code=trader_code,
                        trader_name=trader.nick_name,
                        action=action,
                        inst_id=new_pos.inst_id,
                        pos_side=new_pos.pos_side,
                        quantity=str(abs(new_size - old_size)),
                        price=new_pos.avg_px,
                        timestamp=now,
                        prev_quantity=old_pos.pos
                    )
                    signals.append(signal)

        # Update cache
        self._cache[trader_code] = current_map

        return signals

    def reset(self) -> None:
        """Reset monitor state."""
        self._cache.clear()
        for code in self._traders:
            self._first_run[code] = True


class MonitorThread(QThread):
    """Background thread for monitoring."""

    signal_detected = pyqtSignal(TradeSignal)
    log_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    positions_updated = pyqtSignal(str, list)

    def __init__(self, monitor: LeadTraderMonitor, interval: int = 10):
        super().__init__()
        self.monitor = monitor
        self.interval = interval
        self._running = False

    def run(self) -> None:
        """Main monitoring loop."""
        self._running = True
        self.log_message.emit(f"监控启动，间隔 {self.interval}s")

        # Connect signals
        self.monitor.signal_detected.connect(self.signal_detected.emit)
        self.monitor.log_message.connect(self.log_message.emit)
        self.monitor.error_occurred.connect(self.error_occurred.emit)
        self.monitor.positions_updated.connect(self.positions_updated.emit)

        while self._running:
            try:
                signals = self.monitor.check_positions()
                for signal in signals:
                    self.signal_detected.emit(signal)
            except Exception as e:
                self.error_occurred.emit(f"异常: {str(e)}")

            # Sleep in intervals for responsive stopping
            for _ in range(self.interval * 10):
                if not self._running:
                    break
                self.msleep(100)

        self.log_message.emit("监控已停止")

    def stop(self) -> None:
        """Stop the monitoring thread."""
        self._running = False
