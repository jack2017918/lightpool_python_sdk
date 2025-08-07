#!/usr/bin/env python3
"""
简化的Bincode兼容性测试
直接测试核心序列化逻辑，避免依赖问题
"""

import struct
import enum
import attr
from typing import Optional


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
    FOK = "fok"  # Fill Or Kill
    
    def to_rust_index(self) -> int:
        """转换为Rust枚举索引"""
        mapping = {
            TimeInForce.GTC: 0,  # GTC
            TimeInForce.IOC: 1,  # IOC
            TimeInForce.FOK: 2,  # FOK
        }
        return mapping[self]


@attr.s(auto_attribs=True)
class PlaceOrderParams:
    side: int = attr.ib()              # OrderSide as int for bincode compatibility
    amount: int = attr.ib()            # u64 in Rust
    order_type: int = attr.ib()        # OrderParamsType as enum index for bincode (0=Limit, 1=Market, 2=Trigger)
    limit_price: int = attr.ib()       # u64 in Rust (not optional)
    # 可选字段，根据 order_type 使用
    tif: Optional[int] = attr.ib(default=0)                    # For Limit orders
    slippage: Optional[int] = attr.ib(default=100)             # For Market orders
    trigger_price: Optional[int] = attr.ib(default=0)          # For Trigger orders
    is_market: Optional[bool] = attr.ib(default=False)         # For Trigger orders
    trigger_type: Optional[int] = attr.ib(default=0)           # For Trigger orders


def create_limit_order_params(side: OrderSide, amount: int, limit_price: int, 
                            tif: TimeInForce = TimeInForce.GTC) -> PlaceOrderParams:
    """创建限价单参数的辅助函数"""
    return PlaceOrderParams(
        side=side.to_rust_index(),
        amount=amount,
        order_type=0,  # OrderParamsType::Limit = 0
        limit_price=limit_price,
        tif=tif.to_rust_index() if hasattr(tif, 'to_rust_index') else 0
    )


def serialize_place_order_params(params: PlaceOrderParams) -> bytes:
    """序列化PlaceOrderParams，与Rust bincode格式兼容"""
    result = b''
    
    # side: OrderSide - 4字节小端u32（枚举索引）
    side_index = params.side if isinstance(params.side, int) else params.side.to_rust_index()
    result += struct.pack('<I', side_index)
    
    # amount: u64 - 8字节小端
    result += struct.pack('<Q', params.amount)
    
    # order_type: OrderParamsType - 序列化完整枚举结构
    order_type_index = params.order_type
    result += struct.pack('<I', order_type_index)
    
    # 根据order_type添加对应的枚举内容
    if order_type_index == 0:  # Limit
        # TimeInForce: 4字节小端u32
        tif_value = getattr(params, 'tif', 0)  # 默认GTC=0
        if hasattr(tif_value, 'to_rust_index'):
            tif_index = tif_value.to_rust_index()
        else:
            tif_index = int(tif_value)
        result += struct.pack('<I', tif_index)
        
    elif order_type_index == 1:  # Market
        # slippage: 8字节小端u64
        slippage = getattr(params, 'slippage', 100)  # 默认100bp
        result += struct.pack('<Q', slippage)
        
    elif order_type_index == 2:  # Trigger
        # trigger_price: u64, is_market: bool, trigger_type: u32
        trigger_price = getattr(params, 'trigger_price', 0)
        is_market = getattr(params, 'is_market', False)
        trigger_type = getattr(params, 'trigger_type', 0)
        result += struct.pack('<Q', trigger_price)
        result += struct.pack('<?', is_market)
        result += struct.pack('<I', trigger_type)
    
    # limit_price: u64 - 8字节小端
    result += struct.pack('<Q', params.limit_price)
    
    return result


def test_bincode_compatibility():
    """测试与Rust bincode的兼容性"""
    
    print("=== Bincode兼容性测试 ===")
    
    # 创建与Rust示例相同的参数
    params = create_limit_order_params(
        side=OrderSide.SELL,
        amount=5_000_000,
        limit_price=50_000_000_000,
        tif=TimeInForce.GTC
    )
    
    print(f"创建的参数: {params}")
    
    # 序列化
    serialized = serialize_place_order_params(params)
    
    # 验证关键字节
    expected_length = 28
    actual_length = len(serialized)
    print(f"\n长度检查: 期望 {expected_length} 字节, 实际 {actual_length} 字节")
    assert actual_length == expected_length, f"Expected {expected_length} bytes, got {actual_length}"
    
    # 验证各字段
    print("\n字段验证:")
    
    # side字段验证
    side_bytes = serialized[0:4]
    side_value = struct.unpack('<I', side_bytes)[0]
    print(f"  side: {side_value} (期望 1 for Sell)")
    assert side_value == 1, f"Expected side=1 (Sell), got {side_value}"
    
    # amount字段验证
    amount_bytes = serialized[4:12]
    amount_value = struct.unpack('<Q', amount_bytes)[0]
    print(f"  amount: {amount_value} (期望 5000000)")
    assert amount_value == 5_000_000, f"Expected amount=5000000, got {amount_value}"
    
    # order_type字段验证
    order_type_bytes = serialized[12:16]
    order_type_value = struct.unpack('<I', order_type_bytes)[0]
    print(f"  order_type: {order_type_value} (期望 0 for Limit)")
    assert order_type_value == 0, f"Expected order_type=0 (Limit), got {order_type_value}"
    
    # tif字段验证
    tif_bytes = serialized[16:20]
    tif_value = struct.unpack('<I', tif_bytes)[0]
    print(f"  tif: {tif_value} (期望 0 for GTC)")
    assert tif_value == 0, f"Expected tif=0 (GTC), got {tif_value}"
    
    # limit_price字段验证
    limit_price_bytes = serialized[20:28]
    limit_price_value = struct.unpack('<Q', limit_price_bytes)[0]
    print(f"  limit_price: {limit_price_value} (期望 50000000000)")
    assert limit_price_value == 50_000_000_000, f"Expected limit_price=50000000000, got {limit_price_value}"
    
    print(f"\n✅ Bincode兼容性测试通过")
    print(f"序列化长度: {len(serialized)} 字节")
    print(f"十六进制: {serialized.hex()}")
    
    # 与debug输出对比
    print(f"\n与debug_bincode.py输出对比:")
    print(f"  实际: {serialized.hex()}")
    print(f"  之前: 01000000404b4c0000000000000000000000000000743ba40b000000")
    
    return serialized


if __name__ == "__main__":
    try:
        test_bincode_compatibility()
        print("\n🎉 简化版兼容性测试通过!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
