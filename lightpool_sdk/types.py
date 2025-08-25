"""
LightPool SDK 类型定义
"""

import enum
from typing import Union, Optional, List, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator
import hashlib
import secrets
import attr
import attrs2bin
from attrs2bin import UnsignedInt
import struct
from typing import List, Optional, Union
from dataclasses import dataclass


class OrderSide(enum.Enum):
    """订单方向"""

    BUY = "buy"
    SELL = "sell"

    def to_rust_index(self) -> int:
        """转换为Rust枚举索引"""
        return 0 if self == OrderSide.BUY else 1


class TimeInForce(enum.Enum):
    """订单有效期"""

    GTC = "gtc"  # Good Till Cancel
    IOC = "ioc"  # Immediate Or Cancel

    def to_rust_index(self) -> int:
        """转换为Rust枚举索引"""
        mapping = {
            TimeInForce.GTC: 0,  # GTC
            TimeInForce.IOC: 1,  # IOC
        }
        return mapping[self]

    FOK = "fok"  # Fill Or Kill


class MarketState(enum.Enum):
    """市场状态"""

    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"

    def to_rust_index(self) -> int:
        """转换为Rust枚举索引"""
        # 根据Rust MarketState的定义顺序
        mapping = {
            MarketState.ACTIVE: 0,  # Active
            MarketState.PAUSED: 1,  # Paused
            MarketState.CLOSED: 4,  # Closed (跳过PostOnly=2, CancelOnly=3)
        }
        return mapping[self]


class ExecutionStatus(enum.Enum):
    """执行状态"""

    SUCCESS = "success"
    FAILURE = "failure"
    # 兼容Rust版本的大写形式
    Success = "Success"
    Failure = "Failure"


class U256:
    """256位无符号整数"""

    def __init__(self, value: Union[int, str, bytes]):
        if isinstance(value, int):
            if value < 0:
                raise ValueError("U256 cannot be negative")
            self.value = value
        elif isinstance(value, str):
            if value.startswith("0x"):
                self.value = int(value, 16)
            else:
                self.value = int(value)
        elif isinstance(value, bytes):
            self.value = int.from_bytes(value, byteorder="big")
        else:
            raise ValueError(f"Invalid U256 value: {value}")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"U256({self.value})"

    def to_bytes(self, length: int = 32) -> bytes:
        """转换为字节数组"""
        return self.value.to_bytes(length, byteorder="big")


class Address:
    """LightPool地址类型"""

    def __init__(self, value: Union[str, bytes, int]):
        if isinstance(value, str):
            if value.startswith("0x"):
                value = value[2:]
            if len(value) != 64:  # 32字节 = 64个十六进制字符
                raise ValueError(f"Invalid address length: {len(value)}")
            self.value = bytes.fromhex(value)
        elif isinstance(value, bytes):
            if len(value) != 32:
                raise ValueError(f"Invalid address length: {len(value)}")
            self.value = value
        elif isinstance(value, int):
            self.value = value.to_bytes(32, byteorder="big")
        else:
            raise ValueError(f"Invalid address value: {value}")

    def __str__(self) -> str:
        return "0x" + self.value.hex()

    def __repr__(self) -> str:
        return f"Address('{self}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, Address):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def to_bytes(self) -> bytes:
        """返回地址的字节数组表示"""
        return self.value

    @classmethod
    def zero(cls) -> "Address":
        """返回零地址"""
        return cls(bytes(32))

    @classmethod
    def one(cls) -> "Address":
        """返回地址1"""
        return cls(bytes([1] + [0] * 31))

    @classmethod
    def two(cls) -> "Address":
        """返回地址2"""
        return cls(bytes([2] + [0] * 31))

    @classmethod
    def random(cls) -> "Address":
        """生成随机地址"""
        return cls(secrets.token_bytes(32))


class ObjectID:
    """ObjectID represents a 16-byte identifier"""

    def __init__(self, value: Union[str, bytes]):
        if isinstance(value, str):
            # Remove 0x prefix if present
            if value.startswith("0x"):
                value = value[2:]
            # Convert hex string to bytes
            self.value = bytes.fromhex(value)
        elif isinstance(value, bytes):
            self.value = value
        else:
            raise ValueError(f"Invalid ObjectID value: {value}")

        if len(self.value) != 16:
            raise ValueError(f"Invalid ObjectID length: {len(self.value)}")

    def __str__(self):
        return f"0x{self.value.hex()}"

    def __repr__(self):
        return f"ObjectID('{self}')"

    def __eq__(self, other):
        if isinstance(other, ObjectID):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(self.value)

    @classmethod
    def random(cls):
        """Generate a random ObjectID"""
        import os

        return cls(os.urandom(16))

    @classmethod
    def from_u128(cls, value: int) -> "ObjectID":
        """从u128值创建ObjectID"""
        return cls(value.to_bytes(16, byteorder="little"))


class OrderId:
    """OrderId represents a 32-byte identifier (4 u64 values)"""

    def __init__(self, value: Union[str, bytes, List[int]]):
        if isinstance(value, str):
            # Remove 0x prefix if present
            if value.startswith("0x"):
                value = value[2:]
            # Convert hex string to bytes
            self.value = bytes.fromhex(value)
        elif isinstance(value, bytes):
            self.value = value
        elif isinstance(value, list):
            # Convert list of 4 u64 values to bytes
            if len(value) != 4:
                raise ValueError(
                    f"OrderId must have exactly 4 u64 values, got {len(value)}"
                )
            self.value = b""
            for u64_val in value:
                self.value += struct.pack("<Q", u64_val)
        else:
            raise ValueError(f"Invalid OrderId value: {value}")

        if len(self.value) != 32:
            raise ValueError(f"Invalid OrderId length: {len(self.value)}")

    def __str__(self):
        return f"0x{self.value.hex()}"

    def __repr__(self):
        return f"OrderId('{self}')"

    def __eq__(self, other):
        if isinstance(other, OrderId):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(self.value)

    def as_array(self) -> List[int]:
        """Convert to array of 4 u64 values"""
        result = []
        for i in range(4):
            u64_bytes = self.value[i * 8 : (i + 1) * 8]
            result.append(struct.unpack("<Q", u64_bytes)[0])
        return result


class Digest:
    """交易摘要类型"""

    def __init__(self, value: Union[str, bytes]):
        if isinstance(value, str):
            if value.startswith("0x"):
                value = value[2:]
            if len(value) != 64:
                raise ValueError(f"Invalid digest length: {len(value)}")
            self.value = bytes.fromhex(value)
        elif isinstance(value, bytes):
            if len(value) != 32:
                raise ValueError(f"Invalid digest length: {len(value)}")
            self.value = value
        else:
            raise ValueError(f"Invalid digest value: {value}")

    def __str__(self) -> str:
        return "0x" + self.value.hex()

    def __repr__(self) -> str:
        return f"Digest('{self}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, Digest):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    @classmethod
    def from_bytes(cls, data: bytes) -> "Digest":
        """从字节数据生成摘要"""
        return cls(hashlib.sha256(data).digest())


# 代币相关参数类型
@attr.s(auto_attribs=True)
class CreateTokenParams:
    name: str = attr.ib()
    symbol: str = attr.ib()
    total_supply: int = attr.ib()  # u64 in Rust
    mintable: bool = attr.ib()
    to: bytes = attr.ib()  # Address as 32 bytes for bincode compatibility


@attr.s(auto_attribs=True)
class TransferParams:
    to: bytes = attr.ib()  # Address as 32 bytes for bincode compatibility
    amount: int = attr.ib()  # u64 in Rust


@attr.s(auto_attribs=True)
class MintParams:
    to: bytes = attr.ib()  # Address as 32 bytes for bincode compatibility
    amount: int = attr.ib()  # u64 in Rust


@attr.s(auto_attribs=True)
class SplitParams:
    amount: int = attr.ib()  # u64 in Rust


@attr.s(auto_attribs=True)
class MergeParams:
    pass  # MergeParams is empty in Rust


# 现货交易相关参数类型
@attr.s(auto_attribs=True)
class CreateMarketParams:
    name: str = attr.ib()
    base_token: bytes = attr.ib()  # Address as bytes for bincode compatibility
    quote_token: bytes = attr.ib()  # Address as bytes for bincode compatibility
    min_order_size: int = attr.ib()  # u64 in Rust
    tick_size: int = attr.ib()  # u64 in Rust
    maker_fee_bps: int = attr.ib()  # u16 in Rust (but int in Python is fine)
    taker_fee_bps: int = attr.ib()  # u16 in Rust (but int in Python is fine)
    allow_market_orders: bool = attr.ib()
    state: int = attr.ib()  # MarketState as integer for bincode compatibility
    limit_order: bool = attr.ib()


@dataclass
class UpdateMarketParams:
    min_order_size: Optional[int] = None
    maker_fee_bps: Optional[int] = None
    taker_fee_bps: Optional[int] = None
    allow_market_orders: Optional[bool] = None
    state: Optional[MarketState] = None


@attr.s(auto_attribs=True)
class PlaceOrderParams:
    side: int = attr.ib()  # OrderSide as int for bincode compatibility
    amount: int = attr.ib()  # u64 in Rust
    order_type: int = (
        attr.ib()
    )  # OrderParamsType as enum index for bincode (0=Limit, 1=Market, 2=Trigger)
    limit_price: int = attr.ib()  # u64 in Rust (not optional)
    # 可选字段，根据 order_type 使用
    tif: Optional[int] = attr.ib(default=0)  # For Limit orders
    slippage: Optional[int] = attr.ib(default=100)  # For Market orders
    trigger_price: Optional[int] = attr.ib(default=0)  # For Trigger orders
    is_market: Optional[bool] = attr.ib(default=False)  # For Trigger orders
    trigger_type: Optional[int] = attr.ib(default=0)  # For Trigger orders


@attr.s(auto_attribs=True)
class LimitOrderParams:
    """限价单参数 - 对应Rust的OrderParamsType::Limit { tif }"""

    tif: int = attr.ib()  # TimeInForce as int for bincode compatibility


@attr.s(auto_attribs=True)
class MarketOrderParams:
    """市价单参数 - 对应Rust的OrderParamsType::Market { slippage }"""

    slippage: int = attr.ib()  # u64 in Rust


@attr.s(auto_attribs=True)
class TriggerOrderParams:
    """触发单参数 - 对应Rust的OrderParamsType::Trigger { trigger_price, is_market, trigger_type }"""

    trigger_price: int = attr.ib()  # u64 in Rust
    is_market: bool = attr.ib()
    trigger_type: int = attr.ib()  # TriggerType as int for bincode compatibility


@attr.s(auto_attribs=True)
class CancelOrderParams:
    order_id: bytes = attr.ib()  # OrderId as bytes for bincode compatibility


# 订单参数类型枚举索引
class OrderParamsType:
    """订单参数类型索引 - 对应Rust的OrderParamsType枚举"""

    LIMIT = 0  # Limit order
    MARKET = 1  # Market order
    TRIGGER = 2  # Trigger order


class LimitOrderParams(OrderParamsType):
    """限价单参数"""

    def __init__(self, tif: TimeInForce = TimeInForce.GTC):
        self.tif = tif

    def to_rust_index(self) -> int:
        """转换为Rust枚举索引 - 目前只支持GTC"""
        return 0  # OrderParamsType::Limit = 0


class MarketOrderParams(OrderParamsType):
    """市价单参数"""

    def __init__(self, slippage: int):
        self.slippage = slippage

    def to_rust_index(self) -> int:
        """转换为Rust枚举索引"""
        return 1  # OrderParamsType::Market = 1


def create_limit_order_params(
    side: OrderSide, amount: int, limit_price: int, tif: TimeInForce = TimeInForce.GTC
) -> PlaceOrderParams:
    """创建限价单参数的辅助函数"""
    return PlaceOrderParams(
        side=side.to_rust_index(),
        amount=amount,
        order_type=0,  # OrderParamsType::Limit = 0
        limit_price=limit_price,
        tif=tif.to_rust_index() if hasattr(tif, "to_rust_index") else 0,
    )


def create_market_order_params(
    side: OrderSide, amount: int, limit_price: int, slippage: int = 100
) -> PlaceOrderParams:
    """创建市价单参数的辅助函数"""
    return PlaceOrderParams(
        side=side.to_rust_index(),
        amount=amount,
        order_type=1,  # OrderParamsType::Market = 1
        limit_price=limit_price,
        slippage=slippage,
    )


def create_trigger_order_params(
    side: OrderSide,
    amount: int,
    limit_price: int,
    trigger_price: int,
    is_market: bool,
    trigger_type: int,
) -> PlaceOrderParams:
    """创建触发单参数的辅助函数"""
    return PlaceOrderParams(
        side=side.to_rust_index(),
        amount=amount,
        order_type=2,  # OrderParamsType::Trigger = 2
        limit_price=limit_price,
    )


# 交易收据类型
@dataclass
class TransactionReceipt:
    status: ExecutionStatus
    events: List[Dict[str, Any]]
    effects: Dict[str, Any]
    digest: str
    # 附加调试字段：保留原始状态与错误信息，便于定位失败原因
    raw_status: Any = None
    error: Optional[str] = None

    def is_success(self) -> bool:
        return self.status in (ExecutionStatus.SUCCESS, ExecutionStatus.Success)


class OrderId:
    """订单ID类型，用于处理32字节的订单标识符"""

    def __init__(self, data):
        """
        初始化订单ID

        Args:
            data: 可以是字节数组、十六进制字符串或32字节的bytes
        """
        if isinstance(data, str):
            # 处理十六进制字符串
            hex_str = data.replace("0x", "")
            if len(hex_str) != 64:  # 32字节 = 64个十六进制字符
                raise ValueError(
                    f"OrderId hex string must be 64 characters, got {len(hex_str)}"
                )
            self.bytes = bytes.fromhex(hex_str)
        elif isinstance(data, bytes):
            if len(data) != 32:
                raise ValueError(f"OrderId bytes must be 32 bytes, got {len(data)}")
            self.bytes = data
        elif isinstance(data, list) and len(data) == 32:
            # 处理字节数组
            self.bytes = bytes(data)
        else:
            raise ValueError(f"Invalid OrderId data type: {type(data)}")

    @classmethod
    def from_string(cls, hex_str: str) -> "OrderId":
        """从十六进制字符串创建OrderId"""
        return cls(hex_str)

    @classmethod
    def from_bytes(cls, data: bytes) -> "OrderId":
        """从字节数据创建OrderId"""
        return cls(data)

    @classmethod
    def random(cls) -> "OrderId":
        """生成随机OrderId（用于测试）"""
        import os

        return cls(os.urandom(32))

    def to_hex(self) -> str:
        """转换为十六进制字符串"""
        return "0x" + self.bytes.hex()

    def to_bytes(self) -> bytes:
        """获取字节表示"""
        return self.bytes

    def __str__(self) -> str:
        return self.to_hex()

    def __repr__(self) -> str:
        return f"OrderId({self.to_hex()})"

    def __eq__(self, other) -> bool:
        if isinstance(other, OrderId):
            return self.bytes == other.bytes
        return False

    def __hash__(self) -> int:
        return hash(self.bytes)


# 常量定义（基于Module枚举值）
# Token模块地址：第一个字节是0x01，其余31字节为0
TOKEN_CONTRACT_ADDRESS = Address(bytes([0x01] + [0x00] * 31))
# Spot模块地址：第一个字节是0x02，其余31字节为0
SPOT_CONTRACT_ADDRESS = Address(bytes([0x02] + [0x00] * 31))
