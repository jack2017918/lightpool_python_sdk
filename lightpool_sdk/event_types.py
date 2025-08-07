"""
事件类型定义，与Rust端的事件结构保持一致
"""

from dataclasses import dataclass
from typing import Optional
from .types import ObjectID, Address


@dataclass
class MarketCreatedEvent:
    """市场创建事件"""
    market_id: ObjectID
    market_address: Address
    name: str
    base_token: Address
    quote_token: Address
    base_balance: ObjectID
    quote_balance: ObjectID
    price_index_id: ObjectID
    min_order_size: int
    tick_size: int
    maker_fee_bps: int
    taker_fee_bps: int
    allow_market_orders: bool
    state: int
    creator: Address


@dataclass
class TokenCreatedEvent:
    """代币创建事件"""
    token_id: ObjectID
    token_address: Address
    name: str
    symbol: str
    total_supply: int
    creator: Address
    mintable: bool
    to: Address
    balance_id: ObjectID
