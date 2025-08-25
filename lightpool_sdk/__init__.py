"""
LightPool Python SDK

一个用于与LightPool区块链进行交互的Python SDK，特别专注于现货交易功能。
"""

from .client import LightPoolClient
from .crypto import Signer
from .transaction import TransactionBuilder, ActionBuilder
from .trading_client import LightPoolTradingClient, MarketInfo, UserBalance, OrderResult
from .types import (
    Address,
    ObjectID,
    U256,
    Digest,
    OrderId,
    OrderSide,
    TimeInForce,
    OrderParamsType,
    MarketState,
    CreateTokenParams,
    TransferParams,
    MintParams,
    SplitParams,
    MergeParams,
    CreateMarketParams,
    UpdateMarketParams,
    PlaceOrderParams,
    CancelOrderParams,
    TransactionReceipt,
    ExecutionStatus,
    LimitOrderParams,
    MarketOrderParams,
    TOKEN_CONTRACT_ADDRESS,
    SPOT_CONTRACT_ADDRESS,
    create_limit_order_params,
)
from .exceptions import (
    LightPoolError,
    NetworkError,
    CryptoError,
    TransactionError,
    ValidationError,
    RpcError,
)

__version__ = "0.1.0"
__author__ = "LightPool Team"
__email__ = "team@lightpool.com"

__all__ = [
    # Core classes
    "LightPoolClient",
    "Signer",
    "TransactionBuilder",
    "ActionBuilder",
    # High-level trading client
    "LightPoolTradingClient",
    "MarketInfo",
    "UserBalance",
    "OrderResult",
    # Types
    "Address",
    "ObjectID",
    "U256",
    "Digest",
    "OrderId",
    "OrderSide",
    "TimeInForce",
    "OrderParamsType",
    "MarketState",
    # Token parameters
    "CreateTokenParams",
    "TransferParams",
    "MintParams",
    "SplitParams",
    "MergeParams",
    # Spot trading parameters
    "CreateMarketParams",
    "UpdateMarketParams",
    "PlaceOrderParams",
    "CancelOrderParams",
    "LimitOrderParams",
    "MarketOrderParams",
    # Transaction results
    "TransactionReceipt",
    "ExecutionStatus",
    # Constants
    "TOKEN_CONTRACT_ADDRESS",
    "SPOT_CONTRACT_ADDRESS",
    "create_limit_order_params",
    # Exceptions
    "LightPoolError",
    "NetworkError",
    "CryptoError",
    "TransactionError",
    "ValidationError",
    "RpcError",
]
