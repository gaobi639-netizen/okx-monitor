"""OKX API client with signature authentication."""

import hmac
import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Optional, List, Tuple
from dataclasses import dataclass

import requests


@dataclass
class Position:
    """Represents a trading position."""
    inst_id: str
    pos_side: str
    pos: str
    avg_px: str
    upl: str
    lever: str
    margin: str
    upl_ratio: str
    trader_code: str = ""
    trader_name: str = ""

    @classmethod
    def from_dict(cls, data: dict, trader_code: str = "", trader_name: str = "") -> 'Position':
        return cls(
            inst_id=data.get('instId', ''),
            pos_side=data.get('posSide', ''),
            pos=data.get('subPos', data.get('pos', '0')),
            avg_px=data.get('openAvgPx', data.get('avgPx', '0')),
            upl=data.get('upl', '0'),
            lever=data.get('lever', '1'),
            margin=data.get('margin', '0'),
            upl_ratio=data.get('uplRatio', '0'),
            trader_code=trader_code,
            trader_name=trader_name
        )


@dataclass
class Trader:
    """Represents a copy trading lead trader."""
    unique_code: str
    nick_name: str
    portrait: str
    pnl: str
    pnl_ratio: str
    win_ratio: str
    copy_trader_num: str = "0"
    aum: str = "0"

    @classmethod
    def from_dict(cls, data: dict) -> 'Trader':
        return cls(
            unique_code=data.get('uniqueCode', ''),
            nick_name=data.get('nickName', ''),
            portrait=data.get('portrait', ''),
            pnl=data.get('pnl', '0'),
            pnl_ratio=data.get('pnlRatio', '0'),
            win_ratio=data.get('winRatio', '0'),
            copy_trader_num=data.get('copyTraderNum', data.get('accCopyTraderNum', '0')),
            aum=data.get('aum', '0')
        )


class OKXClient:
    """OKX API client with signature authentication."""

    def __init__(self, api_key: str, secret_key: str, passphrase: str, base_url: str = "https://www.okx.com"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def _sign(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        message = timestamp + method.upper() + request_path + body
        mac = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode('utf-8')

    def _request(self, method: str, endpoint: str, params: Optional[dict] = None, data: Optional[dict] = None) -> dict:
        timestamp = self._get_timestamp()

        request_path = endpoint
        if params:
            query_string = '&'.join(f"{k}={v}" for k, v in params.items())
            request_path = f"{endpoint}?{query_string}"

        body = ''
        if data:
            body = json.dumps(data)

        signature = self._sign(timestamp, method, request_path, body)

        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }

        url = f"{self.base_url}{request_path}"

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=15)
            else:
                response = self.session.post(url, headers=headers, data=body, timeout=15)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'code': '-1', 'msg': str(e), 'data': []}

    def _public_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        request_path = endpoint
        if params:
            query_string = '&'.join(f"{k}={v}" for k, v in params.items())
            request_path = f"{endpoint}?{query_string}"

        url = f"{self.base_url}{request_path}"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'code': '-1', 'msg': str(e), 'data': []}

    def resolve_short_url(self, url: str) -> Optional[str]:
        try:
            response = self.session.head(url, allow_redirects=True, timeout=10)
            final_url = response.url

            match = re.search(r'account/([A-Za-z0-9]+)', final_url)
            if match:
                return match.group(1)

            return None
        except Exception:
            return None

    def extract_unique_code(self, text: str) -> Optional[str]:
        text = text.strip()

        if 'oyidl' in text.lower() and 'http' in text.lower():
            resolved = self.resolve_short_url(text)
            if resolved:
                return resolved

        match = re.search(r'account/([A-Za-z0-9]+)', text)
        if match:
            return match.group(1)

        match = re.search(r'uniqueCode=([A-Za-z0-9]+)', text)
        if match:
            return match.group(1)

        if text.isalnum() and 12 <= len(text) <= 20:
            return text

        return None

    def get_lead_traders(self, inst_type: str = 'SWAP', limit: int = 100) -> List[Trader]:
        """Get list of public lead traders - fetch as many as possible."""
        all_traders = []
        seen_codes = set()

        # Use multiple sort types and pagination to get more traders
        sort_types = ['pnl', 'aum']  # Only these work

        for sort_type in sort_types:
            # Get multiple pages
            for page in range(5):  # Up to 5 pages per sort type
                params = {
                    'instType': inst_type,
                    'sortType': sort_type,
                    'limit': '20'  # Max is 20 per request
                }

                response = self._public_request('/api/v5/copytrading/public-lead-traders', params)

                if response.get('code') == '0':
                    data = response.get('data', [])
                    if data and isinstance(data[0], dict) and 'ranks' in data[0]:
                        ranks = data[0]['ranks']
                        new_count = 0
                        for item in ranks:
                            code = item.get('uniqueCode', '')
                            if code and code not in seen_codes:
                                seen_codes.add(code)
                                all_traders.append(Trader.from_dict(item))
                                new_count += 1

                        if new_count == 0:
                            break  # No new traders, stop pagination

                if len(all_traders) >= limit:
                    break

            if len(all_traders) >= limit:
                break

        return all_traders[:limit]

    def get_lead_positions(self, unique_code: str, inst_type: str = 'SWAP') -> List[Position]:
        response = self._public_request('/api/v5/copytrading/public-current-subpositions', {
            'instType': inst_type,
            'uniqueCode': unique_code
        })

        if response.get('code') == '0':
            return [Position.from_dict(item, unique_code) for item in response.get('data', [])]
        return []

    def get_trader_by_code(self, unique_code: str, inst_type: str = 'SWAP') -> Optional[Trader]:
        positions = self.get_lead_positions(unique_code, inst_type)

        if positions:
            return Trader(
                unique_code=unique_code,
                nick_name=f"Trader-{unique_code[:8]}",
                portrait="",
                pnl="0",
                pnl_ratio="0",
                win_ratio="0"
            )

        return None

    def test_connection(self) -> Tuple[bool, str]:
        response = self._request('GET', '/api/v5/account/balance')

        if response.get('code') == '0':
            return True, "连接成功"
        else:
            return False, response.get('msg', '未知错误')
