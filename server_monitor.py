#!/usr/bin/env python3
"""
OKX 交易员监控 - 服务器/手机版（无GUI）
可在 Termux (Android) 或任何 Linux 服务器上运行
"""

import json
import time
import hmac
import base64
import hashlib
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
import telegram
from telegram.error import TelegramError


# ==================== 配置 ====================
CONFIG = {
    "okx": {
        "api_key": "d465b033-1498-4512-8bc3-a2b276509e41",
        "secret_key": "3843286B20276375229C15B946CA07BE",
        "passphrase": "You520520@"
    },
    "telegram": {
        "bot_token": "8524544854:AAH-Emfnea1fFv0qY7KbQ68w7OPrKVltIGU",
        "chat_id": "7550827764"
    },
    "monitor": {
        "interval": 30,  # 检查间隔（秒）
        "traders": {
            "90BCC01689ED93F0": "炒币猛",
            "C7966D1C938416B0": "梭哈以太"
        }
    }
}


# ==================== 数据类 ====================
@dataclass
class Position:
    inst_id: str
    pos_side: str
    pos: str
    avg_px: str
    upl: str
    lever: str

    @classmethod
    def from_dict(cls, data: dict) -> 'Position':
        return cls(
            inst_id=data.get('instId', ''),
            pos_side=data.get('posSide', ''),
            pos=data.get('subPos', data.get('pos', '0')),
            avg_px=data.get('openAvgPx', data.get('avgPx', '0')),
            upl=data.get('upl', '0'),
            lever=data.get('lever', '1')
        )

    @property
    def key(self) -> str:
        return f"{self.inst_id}_{self.pos_side}"


# ==================== OKX客户端 ====================
class OKXClient:
    def __init__(self, api_key: str, secret_key: str, passphrase: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = "https://www.okx.com"
        self.session = requests.Session()

    def get_positions(self, unique_code: str) -> List[Position]:
        """获取交易员持仓"""
        url = f"{self.base_url}/api/v5/copytrading/public-current-subpositions"
        params = {"instType": "SWAP", "uniqueCode": unique_code}

        try:
            response = self.session.get(url, params=params, timeout=15)
            data = response.json()
            if data.get('code') == '0':
                return [Position.from_dict(item) for item in data.get('data', [])]
        except Exception as e:
            print(f"[错误] 获取持仓失败: {e}")
        return []


# ==================== Telegram通知 ====================
class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=bot_token)

    async def send_async(self, message: str) -> bool:
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except TelegramError as e:
            print(f"[错误] Telegram发送失败: {e}")
            return False

    def send(self, message: str) -> bool:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_async(message))
            loop.close()
            return result
        except Exception as e:
            print(f"[错误] 发送异常: {e}")
            return False


# ==================== 监控器 ====================
class Monitor:
    def __init__(self, client: OKXClient, notifier: TelegramNotifier, traders: Dict[str, str]):
        self.client = client
        self.notifier = notifier
        self.traders = traders  # {unique_code: nickname}
        self.cache: Dict[str, Dict[str, Position]] = {}
        self.first_run: Dict[str, bool] = {code: True for code in traders}

    def check_all(self) -> None:
        """检查所有交易员"""
        for code, name in self.traders.items():
            try:
                self._check_trader(code, name)
            except Exception as e:
                print(f"[错误] 检查 {name} 失败: {e}")

    def _check_trader(self, code: str, name: str) -> None:
        """检查单个交易员"""
        positions = self.client.get_positions(code)
        current_map = {p.key: p for p in positions}

        # 首次运行只缓存，不发通知
        if self.first_run.get(code, True):
            self.cache[code] = current_map
            self.first_run[code] = False
            print(f"[初始化] {name}: {len(positions)} 个持仓")
            return

        old_map = self.cache.get(code, {})
        now = datetime.now()

        # 检测变化
        all_keys = set(old_map.keys()) | set(current_map.keys())

        for key in all_keys:
            old_pos = old_map.get(key)
            new_pos = current_map.get(key)

            if new_pos and not old_pos:
                # 新开仓
                action = "🟢 开多" if new_pos.pos_side == "long" else "🔴 开空"
                self._send_signal(name, action, new_pos, now)

            elif old_pos and not new_pos:
                # 平仓
                action = "🔵 平多" if old_pos.pos_side == "long" else "🟠 平空"
                self._send_signal(name, action, old_pos, now)

            elif old_pos and new_pos:
                # 检查仓位变化
                try:
                    old_size = float(old_pos.pos) if old_pos.pos else 0
                    new_size = float(new_pos.pos) if new_pos.pos else 0

                    if abs(new_size - old_size) > 0.0001:
                        if new_size > old_size:
                            action = "🟢 加多" if new_pos.pos_side == "long" else "🔴 加空"
                        else:
                            action = "🔵 减多" if new_pos.pos_side == "long" else "🟠 减空"
                        self._send_signal(name, action, new_pos, now, abs(new_size - old_size))
                except:
                    pass

        # 更新缓存
        self.cache[code] = current_map

    def _send_signal(self, trader_name: str, action: str, pos: Position, time: datetime, qty_change: float = None) -> None:
        """发送交易信号"""
        coin = pos.inst_id.replace('-USDT-SWAP', '').replace('-SWAP', '') if pos.inst_id else "未知"
        direction = "做多" if pos.pos_side == "long" else "做空"

        qty = qty_change if qty_change else (float(pos.pos) if pos.pos else 0)
        try:
            price = f"${float(pos.avg_px):,.2f}" if pos.avg_px else "-"
        except:
            price = "-"

        msg = f"""🔔 交易员动态提醒

交易员: {trader_name}
操作: {action}
币种: {pos.inst_id or '隐藏'}
方向: {direction}
数量: {qty:,.2f} {coin}
价格: {price}

时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"""

        print(f"\n{'='*40}")
        print(msg)
        print('='*40)

        # 发送Telegram
        if self.notifier.send(msg):
            print("[通知] Telegram 发送成功")
        else:
            print("[通知] Telegram 发送失败")


# ==================== 主程序 ====================
def main():
    print("="*50)
    print("  OKX 交易员监控 - 服务器版")
    print("="*50)

    # 初始化
    client = OKXClient(
        CONFIG["okx"]["api_key"],
        CONFIG["okx"]["secret_key"],
        CONFIG["okx"]["passphrase"]
    )

    notifier = TelegramNotifier(
        CONFIG["telegram"]["bot_token"],
        CONFIG["telegram"]["chat_id"]
    )

    monitor = Monitor(client, notifier, CONFIG["monitor"]["traders"])

    interval = CONFIG["monitor"]["interval"]

    print(f"\n监控交易员: {list(CONFIG['monitor']['traders'].values())}")
    print(f"检查间隔: {interval} 秒")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n开始监控...\n")

    # 发送启动通知
    notifier.send(f"🚀 OKX监控已启动\n\n监控交易员: {', '.join(CONFIG['monitor']['traders'].values())}\n检查间隔: {interval}秒")

    # 主循环
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查中...")
            monitor.check_all()
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n监控已停止")
            notifier.send("⏹️ OKX监控已停止")
            break
        except Exception as e:
            print(f"[错误] {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
