"""Configuration management for OKX Monitor."""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict


@dataclass
class OKXConfig:
    """OKX API configuration."""
    api_key: str = ""
    secret_key: str = ""
    passphrase: str = ""
    base_url: str = "https://www.okx.com"


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    bot_token: str = ""
    chat_id: str = ""


@dataclass
class MonitorConfig:
    """Monitor settings."""
    poll_interval: int = 10  # seconds
    enabled: bool = False


@dataclass
class AppConfig:
    """Application configuration."""
    okx: OKXConfig
    telegram: TelegramConfig
    monitor: MonitorConfig
    trader_nicknames: Dict[str, str]  # uniqueCode -> nickname

    def __init__(
        self,
        okx: Optional[OKXConfig] = None,
        telegram: Optional[TelegramConfig] = None,
        monitor: Optional[MonitorConfig] = None,
        trader_nicknames: Optional[Dict[str, str]] = None
    ):
        self.okx = okx or OKXConfig()
        self.telegram = telegram or TelegramConfig()
        self.monitor = monitor or MonitorConfig()
        self.trader_nicknames = trader_nicknames or {}


class ConfigManager:
    """Manages application configuration persistence."""

    CONFIG_FILE = "config.json"

    def __init__(self, config_dir: str = ""):
        self.config_dir = config_dir or os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.config_dir, self.CONFIG_FILE)
        self.config = self.load()

    def load(self) -> AppConfig:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return AppConfig(
                    okx=OKXConfig(**data.get('okx', {})),
                    telegram=TelegramConfig(**data.get('telegram', {})),
                    monitor=MonitorConfig(**data.get('monitor', {})),
                    trader_nicknames=data.get('trader_nicknames', {})
                )
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return AppConfig()

    def save(self) -> None:
        """Save configuration to file."""
        data = {
            'okx': asdict(self.config.okx),
            'telegram': asdict(self.config.telegram),
            'monitor': asdict(self.config.monitor),
            'trader_nicknames': self.config.trader_nicknames
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_okx(self, api_key: str, secret_key: str, passphrase: str) -> None:
        """Update OKX configuration."""
        self.config.okx.api_key = api_key
        self.config.okx.secret_key = secret_key
        self.config.okx.passphrase = passphrase
        self.save()

    def update_telegram(self, bot_token: str, chat_id: str) -> None:
        """Update Telegram configuration."""
        self.config.telegram.bot_token = bot_token
        self.config.telegram.chat_id = chat_id
        self.save()

    def update_monitor(self, poll_interval: int, enabled: bool) -> None:
        """Update monitor configuration."""
        self.config.monitor.poll_interval = poll_interval
        self.config.monitor.enabled = enabled
        self.save()

    def set_trader_nickname(self, unique_code: str, nickname: str) -> None:
        """Set a nickname for a trader."""
        if nickname:
            self.config.trader_nicknames[unique_code] = nickname
        elif unique_code in self.config.trader_nicknames:
            del self.config.trader_nicknames[unique_code]
        self.save()

    def get_trader_nickname(self, unique_code: str) -> Optional[str]:
        """Get nickname for a trader."""
        return self.config.trader_nicknames.get(unique_code)

    def remove_trader_nickname(self, unique_code: str) -> None:
        """Remove nickname for a trader."""
        if unique_code in self.config.trader_nicknames:
            del self.config.trader_nicknames[unique_code]
            self.save()
