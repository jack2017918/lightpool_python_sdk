"""
LightPool Trading Client - 高级交易接口

为 Hummingbot 等交易机器人提供用户友好的交易接口，
自动处理市场发现、余额管理和参数映射。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from decimal import Decimal
import json
import time

from .client import LightPoolClient
from .crypto import Signer
from .transaction import TransactionBuilder, ActionBuilder
from .types import (
    Address,
    ObjectID,
    OrderSide,
    TimeInForce,
    MarketState,
    PlaceOrderParams,
    CancelOrderParams,
    CreateMarketParams,
    create_limit_order_params,
    SPOT_CONTRACT_ADDRESS,
    OrderId,
)
from .exceptions import LightPoolError, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class MarketInfo:
    """市场信息"""

    market_id: ObjectID
    market_address: Address
    name: str
    base_token: Address
    quote_token: Address
    base_symbol: str  # e.g., "BTC"
    quote_symbol: str  # e.g., "USDT"
    trading_pair: str  # e.g., "BTC/USDT"
    base_balance_id: ObjectID
    quote_balance_id: ObjectID
    min_order_size: int
    tick_size: int
    maker_fee_bps: int
    taker_fee_bps: int
    state: MarketState


@dataclass
class UserBalance:
    """用户余额信息"""

    token_address: Address
    symbol: str
    balance_id: ObjectID
    amount: int  # 原始整数金额
    decimals: int = 6  # 默认6位小数


@dataclass
class OrderResult:
    """下单结果"""

    success: bool
    order_id: Optional[str] = None
    transaction_hash: Optional[str] = None
    error: Optional[str] = None


class LightPoolTradingClient:
    """LightPool 高级交易客户端

    提供面向交易机器人的高级接口，自动处理：
    - 市场发现和缓存
    - 交易对名称到参数的映射
    - 用户余额查询和管理
    - 订单提交和状态跟踪
    """

    def __init__(self, rpc_url: str, private_key_hex: str, timeout: int = 30):
        """
        初始化交易客户端

        Args:
            rpc_url: LightPool RPC 服务器地址
            private_key_hex: 用户私钥（十六进制）
            timeout: 请求超时时间
        """
        self.client = LightPoolClient(rpc_url, timeout)
        self.signer = Signer.from_hex(private_key_hex)
        self.user_address = self.signer.address()

        # 缓存
        self._markets_cache: Dict[str, MarketInfo] = {}
        self._token_cache: Dict[str, Address] = {}  # symbol -> address
        self._balance_cache: Dict[str, UserBalance] = {}  # symbol -> balance
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5分钟缓存

        logger.info(
            f"LightPool Trading Client initialized for address: {self.user_address}"
        )

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def discover_markets(self, force_refresh: bool = False) -> List[MarketInfo]:
        """
        发现并缓存所有可用市场

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            市场信息列表
        """
        current_time = time.time()

        # 检查缓存是否有效
        if (
            not force_refresh
            and self._markets_cache
            and current_time - self._cache_timestamp < self._cache_ttl
        ):
            return list(self._markets_cache.values())

        logger.info("Discovering markets from LightPool network...")

        try:
            # 方法1: 通过链信息获取市场对象
            # 注意：这是一个概念性实现，实际需要根据 LightPool 的具体实现调整
            chain_info = await self.client.get_chain_info()

            markets = []

            # 方法2: 扫描已知的市场对象类型
            # 这里我们需要实现一个市场扫描逻辑
            # 由于当前 LightPool RPC 没有直接的 "list all markets" 接口
            # 我们采用事件驱动的方式，从创建市场的事件中提取信息

            # 临时方案：使用预定义的市场信息进行测试
            # 在生产环境中，这应该通过扫描区块链事件或专门的索引服务实现
            test_markets = await self._discover_markets_from_events()

            for market_data in test_markets:
                market_info = await self._parse_market_info(market_data)
                if market_info:
                    markets.append(market_info)
                    self._markets_cache[market_info.trading_pair] = market_info

            self._cache_timestamp = current_time
            logger.info(f"Discovered {len(markets)} markets")

            return markets

        except Exception as e:
            logger.error(f"Failed to discover markets: {e}")
            # 如果发现失败，返回缓存的数据（如果有）
            return list(self._markets_cache.values())

    async def _discover_markets_from_events(self) -> List[Dict[str, Any]]:
        """
        从区块链事件中发现市场

        这是一个概念性实现，实际应该：
        1. 扫描 CreateMarket 事件
        2. 提取市场参数
        3. 构建市场信息
        """
        # 临时测试数据 - 在生产环境中应该从事件日志中提取
        return [
            {
                "market_id": "0x00000000000000000000000000000014",
                "market_address": "0x0293bf349be83acc5f190017341b7b119c326f206ca6ed33f2cc89be82f044d0",
                "name": "BTC/USDT",
                "base_token": "0x1000000000000000000000000000000000000000000000000000000000000000",
                "quote_token": "0x2000000000000000000000000000000000000000000000000000000000000000",
                "base_symbol": "BTC",
                "quote_symbol": "USDT",
                "base_balance_id": "0xfbed38a241cb29000000010000000000",
                "quote_balance_id": "0x00000000000014000000020000000000",
                "min_order_size": 1000000,  # 0.01 BTC
                "tick_size": 100000,  # 0.1 USDT
                "maker_fee_bps": 10,  # 0.1%
                "taker_fee_bps": 20,  # 0.2%
                "state": "Active",
            }
        ]

    async def _parse_market_info(
        self, market_data: Dict[str, Any]
    ) -> Optional[MarketInfo]:
        """解析市场数据为 MarketInfo 对象"""
        try:
            return MarketInfo(
                market_id=ObjectID(market_data["market_id"]),
                market_address=Address(market_data["market_address"]),
                name=market_data["name"],
                base_token=Address(market_data["base_token"]),
                quote_token=Address(market_data["quote_token"]),
                base_symbol=market_data["base_symbol"],
                quote_symbol=market_data["quote_symbol"],
                trading_pair=market_data["name"],  # e.g., "BTC/USDT"
                base_balance_id=ObjectID(market_data["base_balance_id"]),
                quote_balance_id=ObjectID(market_data["quote_balance_id"]),
                min_order_size=market_data["min_order_size"],
                tick_size=market_data["tick_size"],
                maker_fee_bps=market_data["maker_fee_bps"],
                taker_fee_bps=market_data["taker_fee_bps"],
                state=MarketState.ACTIVE,  # 简化处理
            )
        except Exception as e:
            logger.error(f"Failed to parse market info: {e}")
            return None

    async def get_market_info(self, trading_pair: str) -> Optional[MarketInfo]:
        """
        获取指定交易对的市场信息

        Args:
            trading_pair: 交易对名称，如 "BTC/USDT" 或 "BTC-USDT"

        Returns:
            市场信息，如果未找到返回 None
        """
        # 标准化交易对名称
        normalized_pair = trading_pair.replace("-", "/").upper()

        # 检查缓存
        if normalized_pair in self._markets_cache:
            return self._markets_cache[normalized_pair]

        # 刷新市场信息
        await self.discover_markets()

        return self._markets_cache.get(normalized_pair)

    async def get_user_balance(
        self, symbol: str, force_refresh: bool = False
    ) -> Optional[UserBalance]:
        """
        获取用户指定代币的余额

        Args:
            symbol: 代币符号，如 "BTC", "USDT"
            force_refresh: 是否强制刷新

        Returns:
            余额信息
        """
        current_time = time.time()
        cache_key = f"{symbol}_{self.user_address}"

        # 检查缓存
        if (
            not force_refresh
            and cache_key in self._balance_cache
            and current_time - self._cache_timestamp < self._cache_ttl
        ):
            return self._balance_cache[cache_key]

        try:
            # 首先需要获取代币地址
            token_address = await self._get_token_address(symbol)
            if not token_address:
                logger.warning(f"Token address not found for symbol: {symbol}")
                return None

            # 获取用户所有代币余额
            all_balances = await self.client.get_all_balance(self.user_address)
            if not all_balances:
                return None

            # 查找匹配的代币余额
            for balance_info in all_balances.get("balances", []):
                if Address(balance_info["token_address"]) == token_address:
                    # 需要获取具体的余额对象ID
                    # 这里需要更详细的实现来获取用户的具体余额对象
                    balance = UserBalance(
                        token_address=token_address,
                        symbol=symbol,
                        balance_id=ObjectID.random(),  # TODO 临时使用随机ID
                        amount=balance_info["balance"],
                        decimals=6,
                    )
                    self._balance_cache[cache_key] = balance
                    return balance

            return None

        except Exception as e:
            logger.error(f"Failed to get user balance for {symbol}: {e}")
            return None

    async def _get_token_address(self, symbol: str) -> Optional[Address]:
        """获取代币地址"""
        # 这里应该有一个符号到地址的映射
        # 可以通过扫描代币创建事件或维护一个注册表来实现
        token_mappings = {
            "BTC": "0x1000000000000000000000000000000000000000000000000000000000000000",
            "USDT": "0x2000000000000000000000000000000000000000000000000000000000000000",
        }

        address_hex = token_mappings.get(symbol.upper())
        return Address(address_hex) if address_hex else None

    async def place_order(
        self,
        trading_pair: str,
        side: str,  # "BUY" or "SELL"
        amount: Decimal,
        price: Decimal,
        order_type: str = "LIMIT",
    ) -> OrderResult:
        """
        下单

        Args:
            trading_pair: 交易对，如 "BTC/USDT"
            side: 买卖方向 "BUY" 或 "SELL"
            amount: 下单数量（基础代币）
            price: 限价（报价代币）
            order_type: 订单类型（目前支持 "LIMIT"）

        Returns:
            下单结果
        """
        try:
            # 1. 获取市场信息
            market_info = await self.get_market_info(trading_pair)
            if not market_info:
                return OrderResult(
                    success=False, error=f"Market not found: {trading_pair}"
                )

            # 2. 验证参数
            if side.upper() not in ["BUY", "SELL"]:
                return OrderResult(
                    success=False, error=f"Invalid side: {side}. Must be BUY or SELL"
                )

            # 3. 转换为 LightPool 格式
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL

            # 转换金额和价格为整数（假设6位小数）
            amount_int = int(amount * 1_000_000)
            price_int = int(price * 1_000_000)

            # 4. 确定使用的余额ID
            balance_id = (
                market_info.quote_balance_id
                if order_side == OrderSide.BUY
                else market_info.base_balance_id
            )

            # 5. 构建订单参数
            order_params = create_limit_order_params(
                side=order_side,
                amount=amount_int,
                limit_price=price_int,
                tif=TimeInForce.GTC,
            )

            # 6. 构建交易
            action = ActionBuilder.place_order(
                market_info.market_address,
                market_info.market_id,
                balance_id,
                order_params,
            )

            tx = (
                TransactionBuilder.new()
                .sender(self.user_address)
                .expiration(0xFFFFFFFFFFFFFFFF)
                .add_action(action)
                .build_and_sign(self.signer)
            )

            # 7. 提交交易
            response = await self.client.submit_transaction(tx)

            if response["receipt"].is_success():
                logger.info(
                    f"Order placed successfully: {side} {amount} {trading_pair} @ {price}"
                )
                return OrderResult(success=True, transaction_hash=response["digest"])
            else:
                error_msg = f"Order failed: {response['receipt'].status}"
                logger.error(error_msg)
                return OrderResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Failed to place order: {e}"
            logger.error(error_msg)
            return OrderResult(success=False, error=error_msg)

    async def cancel_order(self, order_id: str, trading_pair: str) -> OrderResult:
        """
        撤单

        Args:
            order_id: 订单ID
            trading_pair: 交易对

        Returns:
            撤单结果
        """
        try:
            # 获取市场信息
            market_info = await self.get_market_info(trading_pair)
            if not market_info:
                return OrderResult(
                    success=False, error=f"Market not found: {trading_pair}"
                )

            # 构建撤单参数
            # 注意：这里需要将 order_id 转换为正确的 OrderId 类型
            # 具体实现取决于 OrderId 的格式

            # 临时实现 - 需要根据实际的 OrderId 格式调整

            lightpool_order_id = OrderId.from_string(order_id)

            cancel_params = CancelOrderParams(order_id=lightpool_order_id)

            action = ActionBuilder.cancel_order(
                market_info.market_address, market_info.market_id, cancel_params
            )

            tx = (
                TransactionBuilder.new()
                .sender(self.user_address)
                .expiration(0xFFFFFFFFFFFFFFFF)
                .add_action(action)
                .build_and_sign(self.signer)
            )

            response = await self.client.submit_transaction(tx)

            if response["receipt"].is_success():
                logger.info(f"Order cancelled successfully: {order_id}")
                return OrderResult(success=True, transaction_hash=response["digest"])
            else:
                error_msg = f"Cancel failed: {response['receipt'].status}"
                logger.error(error_msg)
                return OrderResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Failed to cancel order: {e}"
            logger.error(error_msg)
            return OrderResult(success=False, error=error_msg)

    async def get_order_book(
        self, trading_pair: str, depth: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        获取订单簿

        Args:
            trading_pair: 交易对
            depth: 深度

        Returns:
            订单簿数据
        """
        market_info = await self.get_market_info(trading_pair)
        if not market_info:
            return None

        return await self.client.get_order_book(market_info.market_id, depth)

    async def get_user_orders(
        self, trading_pair: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户订单

        Args:
            trading_pair: 交易对（可选）

        Returns:
            订单列表
        """
        market_id = None
        if trading_pair:
            market_info = await self.get_market_info(trading_pair)
            if market_info:
                market_id = market_info.market_id

        return await self.client.get_orders(self.user_address, market_id)

    async def list_available_markets(self) -> List[str]:
        """
        列出所有可用的交易对

        Returns:
            交易对名称列表
        """
        markets = await self.discover_markets()
        return [market.trading_pair for market in markets]

    async def get_market_summary(self, trading_pair: str) -> Optional[Dict[str, Any]]:
        """
        获取市场摘要信息

        Args:
            trading_pair: 交易对

        Returns:
            市场摘要
        """
        market_info = await self.get_market_info(trading_pair)
        if not market_info:
            return None

        # 获取订单簿和交易历史
        order_book = await self.get_order_book(trading_pair, 1)
        trades = await self.client.get_trades(market_info.market_id, 1)

        # 计算市场摘要
        summary = {
            "trading_pair": trading_pair,
            "base_symbol": market_info.base_symbol,
            "quote_symbol": market_info.quote_symbol,
            "min_order_size": market_info.min_order_size / 1_000_000,  # 转换为小数
            "tick_size": market_info.tick_size / 1_000_000,
            "maker_fee_bps": market_info.maker_fee_bps,
            "taker_fee_bps": market_info.taker_fee_bps,
            "state": market_info.state,
        }

        # 添加价格信息
        if order_book and "bids" in order_book and order_book["bids"]:
            summary["best_bid"] = order_book["bids"][0][0] / 1_000_000
        if order_book and "asks" in order_book and order_book["asks"]:
            summary["best_ask"] = order_book["asks"][0][0] / 1_000_000

        # 添加最新交易信息
        if trades:
            latest_trade = trades[0]
            summary["last_price"] = latest_trade.get("price", 0) / 1_000_000
            summary["last_volume"] = latest_trade.get("amount", 0) / 1_000_000

        return summary
