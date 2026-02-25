"""Telegram notification service."""

import asyncio
from typing import Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QThread

import telegram
from telegram.error import TelegramError


class TelegramNotifier(QObject):
    """Sends notifications via Telegram bot."""

    message_sent = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, bot_token: str = "", chat_id: str = ""):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._bot: Optional[telegram.Bot] = None

    def configure(self, bot_token: str, chat_id: str) -> None:
        """Update configuration."""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._bot = None  # Reset bot instance

    def _get_bot(self) -> telegram.Bot:
        """Get or create bot instance."""
        if self._bot is None and self.bot_token:
            self._bot = telegram.Bot(token=self.bot_token)
        return self._bot

    async def _send_message_async(self, message: str) -> bool:
        """Send message asynchronously."""
        if not self.bot_token or not self.chat_id:
            self.error_occurred.emit("Telegram 未配置")
            return False

        try:
            bot = self._get_bot()
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            self.message_sent.emit(f"消息已发送到 Telegram")
            return True
        except TelegramError as e:
            self.error_occurred.emit(f"Telegram 发送失败: {str(e)}")
            return False
        except Exception as e:
            self.error_occurred.emit(f"发送异常: {str(e)}")
            return False

    def send_message(self, message: str) -> bool:
        """Send message synchronously (blocking)."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._send_message_async(message))
            loop.close()
            return result
        except Exception as e:
            self.error_occurred.emit(f"发送异常: {str(e)}")
            return False

    async def _test_connection_async(self) -> Tuple[bool, str]:
        """Test bot connection asynchronously."""
        if not self.bot_token:
            return False, "Bot Token 未配置"

        try:
            bot = self._get_bot()
            me = await bot.get_me()
            return True, f"连接成功: @{me.username}"
        except TelegramError as e:
            return False, f"连接失败: {str(e)}"
        except Exception as e:
            return False, f"异常: {str(e)}"

    def test_connection(self) -> Tuple[bool, str]:
        """Test bot connection synchronously."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._test_connection_async())
            loop.close()
            return result
        except Exception as e:
            return False, f"异常: {str(e)}"


class NotifierThread(QThread):
    """Background thread for sending notifications."""

    finished_sending = pyqtSignal(bool, str)

    def __init__(self, notifier: TelegramNotifier, message: str):
        super().__init__()
        self.notifier = notifier
        self.message = message

    def run(self) -> None:
        """Send notification in background."""
        success = self.notifier.send_message(self.message)
        self.finished_sending.emit(success, self.message[:50] + "..." if len(self.message) > 50 else self.message)
