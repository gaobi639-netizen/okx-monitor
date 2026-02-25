#!/usr/bin/env python3
"""
OKX 交易员监控 - 服务器版（支持Telegram命令管理）
通过 Telegram 发送命令即可管理交易员，无需登录服务器
"""

import json
import time
import threading
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List

import requests
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes


# ==================== 配置文件路径 ====================
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor_config.json")

# 默认配置
DEFAULT_CONFIG = {
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
        "interval": 30,
        "traders": {
            "90BCC01689ED93F0": "炒币猛",
            "C7966D1C938416B0": "梭哈以太"
        }
    }
}


def load_config() -> dict:
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """保存配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# 全局配置
CONFIG = load_config()
save_config(CONFIG)  # 确保配置文件存在


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
    def __init__(self):
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

    def check_trader_exists(self, unique_code: str) -> bool:
        """检查交易员是否存在"""
        positions = self.get_positions(unique_code)
        # 即使没有持仓，只要API没返回错误就认为存在
        url = f"{self.base_url}/api/v5/copytrading/public-current-subpositions"
        params = {"instType": "SWAP", "uniqueCode": unique_code}
        try:
            response = self.session.get(url, params=params, timeout=15)
            data = response.json()
            return data.get('code') == '0'
        except:
            return False


# ==================== 监控器 ====================
class Monitor:
    def __init__(self, client: OKXClient, bot: Bot):
        self.client = client
        self.bot = bot
        self.cache: Dict[str, Dict[str, Position]] = {}
        self.first_run: Dict[str, bool] = {}
        self.running = False

    def get_traders(self) -> Dict[str, str]:
        return CONFIG["monitor"]["traders"]

    async def send_message(self, message: str) -> None:
        """发送Telegram消息"""
        try:
            await self.bot.send_message(chat_id=CONFIG["telegram"]["chat_id"], text=message)
        except Exception as e:
            print(f"[错误] 发送消息失败: {e}")

    async def check_all(self) -> None:
        """检查所有交易员"""
        traders = self.get_traders()
        for code, name in traders.items():
            if code not in self.first_run:
                self.first_run[code] = True
            try:
                await self._check_trader(code, name)
            except Exception as e:
                print(f"[错误] 检查 {name} 失败: {e}")

    async def _check_trader(self, code: str, name: str) -> None:
        """检查单个交易员"""
        positions = self.client.get_positions(code)
        current_map = {p.key: p for p in positions}

        if self.first_run.get(code, True):
            self.cache[code] = current_map
            self.first_run[code] = False
            print(f"[初始化] {name}: {len(positions)} 个持仓")
            return

        old_map = self.cache.get(code, {})
        now = datetime.now()
        all_keys = set(old_map.keys()) | set(current_map.keys())

        for key in all_keys:
            old_pos = old_map.get(key)
            new_pos = current_map.get(key)

            if new_pos and not old_pos:
                action = "🟢 开多" if new_pos.pos_side == "long" else "🔴 开空"
                await self._send_signal(name, action, new_pos, now)
            elif old_pos and not new_pos:
                action = "🔵 平多" if old_pos.pos_side == "long" else "🟠 平空"
                await self._send_signal(name, action, old_pos, now)
            elif old_pos and new_pos:
                try:
                    old_size = float(old_pos.pos) if old_pos.pos else 0
                    new_size = float(new_pos.pos) if new_pos.pos else 0
                    if abs(new_size - old_size) > 0.0001:
                        if new_size > old_size:
                            action = "🟢 加多" if new_pos.pos_side == "long" else "🔴 加空"
                        else:
                            action = "🔵 减多" if new_pos.pos_side == "long" else "🟠 减空"
                        await self._send_signal(name, action, new_pos, now, abs(new_size - old_size))
                except:
                    pass

        self.cache[code] = current_map

    async def _send_signal(self, trader_name: str, action: str, pos: Position, time: datetime, qty_change: float = None) -> None:
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

        print(f"\n{'='*40}\n{msg}\n{'='*40}")
        await self.send_message(msg)


# ==================== Telegram 命令 ====================
monitor: Monitor = None
okx_client: OKXClient = None


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """开始命令"""
    help_text = """🤖 OKX 交易员监控 Bot

📋 可用命令：
/list - 查看监控列表
/add <代码> <备注> - 添加交易员
/remove <代码> - 删除交易员
/status - 查看运行状态
/positions - 查看所有持仓

示例：
/add 90BCC01689ED93F0 炒币猛
/remove 90BCC01689ED93F0"""
    await update.message.reply_text(help_text)


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查看监控列表"""
    traders = CONFIG["monitor"]["traders"]
    if not traders:
        await update.message.reply_text("📋 监控列表为空\n\n使用 /add <代码> <备注> 添加交易员")
        return

    text = "📋 监控列表：\n\n"
    for code, name in traders.items():
        text += f"• {name}\n  代码: {code}\n\n"
    text += f"共 {len(traders)} 个交易员"
    await update.message.reply_text(text)


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """添加交易员"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ 格式错误\n\n用法: /add <代码> <备注>\n示例: /add 90BCC01689ED93F0 炒币猛")
        return

    code = context.args[0].upper()
    name = " ".join(context.args[1:])

    if code in CONFIG["monitor"]["traders"]:
        await update.message.reply_text(f"❌ {name} 已在监控列表中")
        return

    # 验证交易员是否存在
    await update.message.reply_text(f"🔍 正在验证交易员 {code}...")

    if not okx_client.check_trader_exists(code):
        await update.message.reply_text(f"❌ 交易员不存在或代码错误: {code}")
        return

    CONFIG["monitor"]["traders"][code] = name
    save_config(CONFIG)

    if monitor:
        monitor.first_run[code] = True

    await update.message.reply_text(f"✅ 已添加交易员\n\n名称: {name}\n代码: {code}")


async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """删除交易员"""
    if len(context.args) < 1:
        await update.message.reply_text("❌ 格式错误\n\n用法: /remove <代码>\n示例: /remove 90BCC01689ED93F0")
        return

    code = context.args[0].upper()

    if code not in CONFIG["monitor"]["traders"]:
        await update.message.reply_text(f"❌ 未找到该交易员: {code}")
        return

    name = CONFIG["monitor"]["traders"].pop(code)
    save_config(CONFIG)

    if monitor:
        monitor.cache.pop(code, None)
        monitor.first_run.pop(code, None)

    await update.message.reply_text(f"✅ 已删除交易员: {name}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查看状态"""
    traders = CONFIG["monitor"]["traders"]
    interval = CONFIG["monitor"]["interval"]

    text = f"""📊 监控状态

运行状态: ✅ 运行中
监控交易员: {len(traders)} 个
检查间隔: {interval} 秒
启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

    await update.message.reply_text(text)


async def cmd_positions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查看所有持仓"""
    traders = CONFIG["monitor"]["traders"]
    if not traders:
        await update.message.reply_text("📋 没有监控的交易员")
        return

    await update.message.reply_text("🔍 正在获取持仓信息...")

    text = "📊 所有交易员持仓\n\n"
    total_positions = 0

    for code, name in traders.items():
        positions = okx_client.get_positions(code)
        total_positions += len(positions)

        text += f"【{name}】\n"
        if positions:
            for pos in positions[:5]:  # 最多显示5个
                coin = pos.inst_id.replace('-USDT-SWAP', '') if pos.inst_id else "隐藏"
                side = "多" if pos.pos_side == "long" else "空"
                try:
                    upl = float(pos.upl)
                    upl_text = f"+${upl:,.0f}" if upl >= 0 else f"-${abs(upl):,.0f}"
                except:
                    upl_text = "-"
                text += f"  {side} {coin} | {upl_text}\n"
            if len(positions) > 5:
                text += f"  ...还有 {len(positions) - 5} 个持仓\n"
        else:
            text += "  暂无持仓\n"
        text += "\n"

    text += f"共 {total_positions} 个持仓"
    await update.message.reply_text(text)


# ==================== 主程序 ====================
async def monitor_loop(app: Application) -> None:
    """监控循环"""
    global monitor, okx_client

    okx_client = OKXClient()
    bot = app.bot
    monitor = Monitor(okx_client, bot)

    interval = CONFIG["monitor"]["interval"]

    print(f"\n监控交易员: {list(CONFIG['monitor']['traders'].values())}")
    print(f"检查间隔: {interval} 秒")
    print("开始监控...\n")

    # 发送启动通知
    await monitor.send_message(f"🚀 OKX监控已启动\n\n监控: {', '.join(CONFIG['monitor']['traders'].values()) or '无'}\n间隔: {interval}秒\n\n发送 /help 查看命令")

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查中...")
            await monitor.check_all()
            await asyncio.sleep(interval)
        except Exception as e:
            print(f"[错误] {e}")
            await asyncio.sleep(10)


def main():
    print("="*50)
    print("  OKX 交易员监控 - 服务器版")
    print("  支持 Telegram 命令管理")
    print("="*50)

    # 创建应用
    app = Application.builder().token(CONFIG["telegram"]["bot_token"]).build()

    # 添加命令处理
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("positions", cmd_positions))

    # 启动监控循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        async with app:
            await app.start()
            await app.updater.start_polling()
            await monitor_loop(app)

    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("\n监控已停止")


if __name__ == "__main__":
    main()
