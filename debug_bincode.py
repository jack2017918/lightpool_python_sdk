#!/usr/bin/env python3
"""
调试bincode序列化格式
"""

import struct

def debug_place_order_params():
    """调试PlaceOrderParams的序列化"""
    
    # 模拟参数
    side = 1  # Sell = 1
    amount = 5000000  # 5M
    limit_price = 50000000000  # 50B
    
    print("=== 调试PlaceOrderParams序列化 ===")
    print(f"side (OrderSide::Sell): {side}")
    print(f"amount: {amount}")
    print(f"limit_price: {limit_price}")
    
    # 方法1: 当前的序列化方式
    print("\n--- 方法1: 当前方式 ---")
    order_type_data = (
        struct.pack('<I', 0) +  # Limit variant = 0
        struct.pack('<I', 0)    # TimeInForce::GTC = 0
    )
    
    params_data = (
        struct.pack('<I', side) +  # side as u32 (OrderSide enum)
        struct.pack('<Q', amount) +  # amount as u64
        order_type_data +  # order_type as OrderParamsType::Limit
        struct.pack('<Q', limit_price)  # limit_price as u64
    )
    
    print(f"序列化长度: {len(params_data)} 字节")
    print(f"十六进制: {params_data.hex()}")
    
    # 分析每个部分
    print("\n字节分析:")
    offset = 0
    
    # side (u32)
    side_bytes = params_data[offset:offset+4]
    print(f"side ({offset:2d}-{offset+3:2d}): {side_bytes.hex()} = {struct.unpack('<I', side_bytes)[0]}")
    offset += 4
    
    # amount (u64)
    amount_bytes = params_data[offset:offset+8]
    print(f"amount ({offset:2d}-{offset+7:2d}): {amount_bytes.hex()} = {struct.unpack('<Q', amount_bytes)[0]}")
    offset += 8
    
    # order_type variant (u32)
    variant_bytes = params_data[offset:offset+4]
    print(f"order_type variant ({offset:2d}-{offset+3:2d}): {variant_bytes.hex()} = {struct.unpack('<I', variant_bytes)[0]}")
    offset += 4
    
    # TimeInForce (u32)
    tif_bytes = params_data[offset:offset+4]
    print(f"TimeInForce ({offset:2d}-{offset+3:2d}): {tif_bytes.hex()} = {struct.unpack('<I', tif_bytes)[0]}")
    offset += 4
    
    # limit_price (u64)
    price_bytes = params_data[offset:offset+8]
    print(f"limit_price ({offset:2d}-{offset+7:2d}): {price_bytes.hex()} = {struct.unpack('<Q', price_bytes)[0]}")
    
    # 方法2: 尝试不同的enum序列化
    print("\n--- 方法2: OrderSide as u8 ---")
    
    order_type_data2 = (
        struct.pack('<I', 0) +  # Limit variant = 0
        struct.pack('<I', 0)    # TimeInForce::GTC = 0
    )
    
    params_data2 = (
        struct.pack('<B', side) +  # side as u8 (smaller enum)
        struct.pack('<Q', amount) +  # amount as u64
        order_type_data2 +  # order_type as OrderParamsType::Limit
        struct.pack('<Q', limit_price)  # limit_price as u64
    )
    
    print(f"序列化长度: {len(params_data2)} 字节")
    print(f"十六进制: {params_data2.hex()}")

if __name__ == "__main__":
    debug_place_order_params()