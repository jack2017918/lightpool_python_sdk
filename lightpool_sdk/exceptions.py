"""
LightPool SDK 异常类定义
"""

from typing import Optional, Any, Dict


class LightPoolError(Exception):
    """LightPool SDK 基础异常类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NetworkError(LightPoolError):
    """网络相关错误"""
    pass


class CryptoError(LightPoolError):
    """加密相关错误"""
    pass


class TransactionError(LightPoolError):
    """交易相关错误"""
    pass


class ValidationError(LightPoolError):
    """数据验证错误"""
    pass


class RpcError(LightPoolError):
    """RPC调用错误"""
    
    def __init__(self, message: str, code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.code = code


class InsufficientBalanceError(TransactionError):
    """余额不足错误"""
    pass


class OrderNotFoundError(TransactionError):
    """订单未找到错误"""
    pass


class MarketNotFoundError(TransactionError):
    """市场未找到错误"""
    pass


class InvalidOrderError(TransactionError):
    """无效订单错误"""
    pass


class MarketClosedError(TransactionError):
    """市场已关闭错误"""
    pass 