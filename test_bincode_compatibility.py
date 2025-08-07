#!/usr/bin/env python3
"""
Bincode兼容性测试
验证Python SDK与Rust SDK的bincode序列化兼容性
"""

import struct
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from lightpool_sdk.types import OrderSide, TimeInForce, PlaceOrderParams, create_limit_order_params
from lightpool_sdk.bincode import serialize_place_order_params


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
    
    # 预期的Rust格式（用于对比）
    expected_hex = "01000000404b4c0000000000000000000000000000743ba40b000000"
    actual_hex = serialized.hex()
    print(f"\n格式对比:")
    print(f"  期望: {expected_hex}")
    print(f"  实际: {actual_hex}")
    print(f"  匹配: {'✅' if expected_hex == actual_hex else '❌'}")
    
    return serialized


def test_market_order_compatibility():
    """测试市价单的兼容性"""
    print("\n=== 市价单兼容性测试 ===")
    
    from lightpool_sdk.types import create_market_order_params
    
    params = create_market_order_params(
        side=OrderSide.BUY,
        amount=3_000_000,
        limit_price=51_000_000_000,
        slippage=200  # 200bp = 2%
    )
    
    print(f"市价单参数: {params}")
    
    serialized = serialize_place_order_params(params)
    
    print(f"序列化长度: {len(serialized)} 字节")
    print(f"十六进制: {serialized.hex()}")
    
    # 验证市价单特定字段
    order_type_bytes = serialized[12:16]
    order_type_value = struct.unpack('<I', order_type_bytes)[0]
    assert order_type_value == 1, f"Expected order_type=1 (Market), got {order_type_value}"
    
    # 验证slippage字段（在order_type之后）
    slippage_bytes = serialized[16:24]
    slippage_value = struct.unpack('<Q', slippage_bytes)[0]
    assert slippage_value == 200, f"Expected slippage=200, got {slippage_value}"
    
    print("✅ 市价单测试通过")
    
    return serialized


def main():
    """主测试函数"""
    try:
        test_bincode_compatibility()
        test_market_order_compatibility()
        print("\n🎉 所有兼容性测试通过!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
