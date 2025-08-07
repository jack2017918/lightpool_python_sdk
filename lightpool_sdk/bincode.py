"""
Bincode兼容的序列化实现
与Rust bincode格式完全兼容
"""

import struct
from typing import Union, Any, Tuple
from .types import CreateTokenParams, CreateMarketParams, PlaceOrderParams, CancelOrderParams, UpdateMarketParams, ObjectID, Address
from .event_types import MarketCreatedEvent, TokenCreatedEvent


def serialize_create_token_params(params: CreateTokenParams) -> bytes:
    """序列化CreateTokenParams，与Rust bincode格式兼容"""
    result = b''
    
    # name: CompactString - 长度(8字节小端) + UTF-8内容
    name_bytes = params.name.encode('utf-8')
    result += struct.pack('<Q', len(name_bytes)) + name_bytes
    
    # symbol: CompactString - 长度(8字节小端) + UTF-8内容
    symbol_bytes = params.symbol.encode('utf-8')
    result += struct.pack('<Q', len(symbol_bytes)) + symbol_bytes
    
    # total_supply: u64 - 8字节小端
    result += struct.pack('<Q', params.total_supply)
    
    # mintable: bool - 1字节
    result += struct.pack('<?', params.mintable)
    
    # to: Address - 直接32字节，无长度前缀
    result += params.to
    
    return result


def serialize_create_market_params(params: CreateMarketParams) -> bytes:
    """序列化CreateMarketParams，与Rust bincode格式兼容"""
    result = b''
    
    # name: CompactString - 长度(8字节小端) + UTF-8内容
    name_bytes = params.name.encode('utf-8')
    result += struct.pack('<Q', len(name_bytes)) + name_bytes
    
    # base_token: Address - 直接32字节
    result += params.base_token
    
    # quote_token: Address - 直接32字节
    result += params.quote_token
    
    # min_order_size: u64 - 8字节小端
    result += struct.pack('<Q', params.min_order_size)
    
    # tick_size: u64 - 8字节小端
    result += struct.pack('<Q', params.tick_size)
    
    # maker_fee_bps: u16 - 2字节小端
    result += struct.pack('<H', params.maker_fee_bps)
    
    # taker_fee_bps: u16 - 2字节小端
    result += struct.pack('<H', params.taker_fee_bps)
    
    # allow_market_orders: bool - 1字节
    result += struct.pack('<?', params.allow_market_orders)
    
    # state: MarketState - 4字节小端u32（枚举索引）
    result += struct.pack('<I', params.state)
    
    # limit_order: bool - 1字节
    result += struct.pack('<?', params.limit_order)
    
    return result


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


def serialize_cancel_order_params(params: CancelOrderParams) -> bytes:
    """序列化CancelOrderParams，与Rust bincode格式兼容"""
    # order_id: OrderId - 32字节 (4个u64，每个8字节)
    # 需要将OrderId转换为32字节的bincode格式
    import struct
    
    # 处理params.order_id，它可能是ObjectID或字符串
    if hasattr(params.order_id, 'value'):
        # 如果是ObjectID，直接使用其字节值
        order_id_bytes = params.order_id.value
    else:
        # 如果是字符串，解析为字节
        order_id_str = str(params.order_id)
        if order_id_str.startswith('0x'):
            order_id_str = order_id_str[2:]
        
        if len(order_id_str) != 32:  # 16字节 = 32个十六进制字符
            raise ValueError(f"Invalid OrderId length: {len(order_id_str)}")
        
        # 解析为16字节
        order_id_bytes = bytes.fromhex(order_id_str)
    
    # 如果order_id_bytes是16字节，需要扩展为32字节的OrderId格式
    if len(order_id_bytes) == 16:
        # 将16字节扩展为4个u64 (32字节)
        result = b''
        for i in range(4):
            # 每个u64取4字节，不足的用0填充
            start = i * 4
            end = min(start + 4, len(order_id_bytes))
            chunk = order_id_bytes[start:end]
            # 扩展为8字节
            chunk = chunk + b'\x00' * (8 - len(chunk))
            result += struct.pack('<Q', int.from_bytes(chunk, 'little'))
        return result
    else:
        # 如果已经是32字节，直接返回
        return order_id_bytes


def serialize_update_market_params(params: UpdateMarketParams) -> bytes:
    """序列化UpdateMarketParams，与Rust bincode格式兼容"""
    import struct
    
    result = bytearray()
    
    # 序列化min_order_size (Option<u64>)
    if params.min_order_size is not None:
        result.extend(b'\x01')  # Some
        result.extend(struct.pack('<Q', params.min_order_size))
    else:
        result.extend(b'\x00')  # None
    
    # 序列化maker_fee_bps (Option<u16>)
    if params.maker_fee_bps is not None:
        result.extend(b'\x01')  # Some
        result.extend(struct.pack('<H', params.maker_fee_bps))
    else:
        result.extend(b'\x00')  # None
    
    # 序列化taker_fee_bps (Option<u16>)
    if params.taker_fee_bps is not None:
        result.extend(b'\x01')  # Some
        result.extend(struct.pack('<H', params.taker_fee_bps))
    else:
        result.extend(b'\x00')  # None
    
    # 序列化allow_market_orders (Option<bool>)
    if params.allow_market_orders is not None:
        result.extend(b'\x01')  # Some
        result.extend(struct.pack('<?', params.allow_market_orders))
    else:
        result.extend(b'\x00')  # None
    
    # 序列化state (Option<MarketState>)
    if params.state is not None:
        result.extend(b'\x01')  # Some
        state_index = params.state.to_rust_index()
        result.extend(struct.pack('<I', state_index))  # u32 for enum
    else:
        result.extend(b'\x00')  # None
    
    return bytes(result)


# 通用序列化函数
def bincode_serialize(obj: Any) -> bytes:
    """通用bincode序列化函数"""
    if isinstance(obj, CreateTokenParams):
        return serialize_create_token_params(obj)
    elif isinstance(obj, CreateMarketParams):
        return serialize_create_market_params(obj)
    elif isinstance(obj, PlaceOrderParams):
        return serialize_place_order_params(obj)
    elif isinstance(obj, CancelOrderParams):
        return serialize_cancel_order_params(obj)
    elif isinstance(obj, UpdateMarketParams):
        return serialize_update_market_params(obj)
    else:
        raise ValueError(f"Unsupported type for bincode serialization: {type(obj)}")


def deserialize_market_created_event(data: bytes) -> MarketCreatedEvent:
    """反序列化MarketCreatedEvent"""
    offset = 0
    
    # 解析market_id (16字节)
    if len(data) < offset + 16:
        raise ValueError("数据长度不足，无法解析market_id")
    market_id_bytes = data[offset:offset+16]
    market_id = ObjectID(market_id_bytes)
    offset += 16
    
    # 解析market_address (32字节)
    if len(data) < offset + 32:
        raise ValueError("数据长度不足，无法解析market_address")
    market_address_bytes = data[offset:offset+32]
    market_address = Address(market_address_bytes)
    offset += 32
    
    # 解析name (CompactString)
    if len(data) < offset + 8:
        raise ValueError("数据长度不足，无法解析name长度")
    name_len = int.from_bytes(data[offset:offset+8], 'little')
    offset += 8
    
    if len(data) < offset + name_len:
        raise ValueError("数据长度不足，无法解析name内容")
    name = data[offset:offset+name_len].decode('utf-8')
    offset += name_len
    
    # 解析base_token (32字节)
    if len(data) < offset + 32:
        raise ValueError("数据长度不足，无法解析base_token")
    base_token_bytes = data[offset:offset+32]
    base_token = Address(base_token_bytes)
    offset += 32
    
    # 解析quote_token (32字节)
    if len(data) < offset + 32:
        raise ValueError("数据长度不足，无法解析quote_token")
    quote_token_bytes = data[offset:offset+32]
    quote_token = Address(quote_token_bytes)
    offset += 32
    
    # 解析base_balance (16字节)
    if len(data) < offset + 16:
        raise ValueError("数据长度不足，无法解析base_balance")
    base_balance_bytes = data[offset:offset+16]
    base_balance = ObjectID(base_balance_bytes)
    offset += 16
    
    # 解析quote_balance (16字节)
    if len(data) < offset + 16:
        raise ValueError("数据长度不足，无法解析quote_balance")
    quote_balance_bytes = data[offset:offset+16]
    quote_balance = ObjectID(quote_balance_bytes)
    offset += 16
    
    # 解析price_index_id (16字节)
    if len(data) < offset + 16:
        raise ValueError("数据长度不足，无法解析price_index_id")
    price_index_id_bytes = data[offset:offset+16]
    price_index_id = ObjectID(price_index_id_bytes)
    offset += 16
    
    # 解析min_order_size (8字节)
    if len(data) < offset + 8:
        raise ValueError("数据长度不足，无法解析min_order_size")
    min_order_size = int.from_bytes(data[offset:offset+8], 'little')
    offset += 8
    
    # 解析tick_size (8字节)
    if len(data) < offset + 8:
        raise ValueError("数据长度不足，无法解析tick_size")
    tick_size = int.from_bytes(data[offset:offset+8], 'little')
    offset += 8
    
    # 解析maker_fee_bps (2字节)
    if len(data) < offset + 2:
        raise ValueError("数据长度不足，无法解析maker_fee_bps")
    maker_fee_bps = int.from_bytes(data[offset:offset+2], 'little')
    offset += 2
    
    # 解析taker_fee_bps (2字节)
    if len(data) < offset + 2:
        raise ValueError("数据长度不足，无法解析taker_fee_bps")
    taker_fee_bps = int.from_bytes(data[offset:offset+2], 'little')
    offset += 2
    
    # 解析allow_market_orders (1字节)
    if len(data) < offset + 1:
        raise ValueError("数据长度不足，无法解析allow_market_orders")
    allow_market_orders = bool(data[offset])
    offset += 1
    
    # 解析state (4字节)
    if len(data) < offset + 4:
        raise ValueError("数据长度不足，无法解析state")
    state = int.from_bytes(data[offset:offset+4], 'little')
    offset += 4
    
    # 解析creator (32字节)
    if len(data) < offset + 32:
        raise ValueError("数据长度不足，无法解析creator")
    creator_bytes = data[offset:offset+32]
    creator = Address(creator_bytes)
    offset += 32
    
    return MarketCreatedEvent(
        market_id=market_id,
        market_address=market_address,
        name=name,
        base_token=base_token,
        quote_token=quote_token,
        base_balance=base_balance,
        quote_balance=quote_balance,
        price_index_id=price_index_id,
        min_order_size=min_order_size,
        tick_size=tick_size,
        maker_fee_bps=maker_fee_bps,
        taker_fee_bps=taker_fee_bps,
        allow_market_orders=allow_market_orders,
        state=state,
        creator=creator
    )


def deserialize_token_created_event(data: bytes) -> TokenCreatedEvent:
    """反序列化TokenCreatedEvent"""
    offset = 0
    
    # 解析token_id (16字节)
    if len(data) < offset + 16:
        raise ValueError("数据长度不足，无法解析token_id")
    token_id_bytes = data[offset:offset+16]
    token_id = ObjectID(token_id_bytes)
    offset += 16
    
    # 解析token_address (32字节)
    if len(data) < offset + 32:
        raise ValueError("数据长度不足，无法解析token_address")
    token_address_bytes = data[offset:offset+32]
    token_address = Address(token_address_bytes)
    offset += 32
    
    # 解析name (CompactString)
    if len(data) < offset + 8:
        raise ValueError("数据长度不足，无法解析name长度")
    name_len = int.from_bytes(data[offset:offset+8], 'little')
    offset += 8
    
    if len(data) < offset + name_len:
        raise ValueError("数据长度不足，无法解析name内容")
    name = data[offset:offset+name_len].decode('utf-8')
    offset += name_len
    
    # 解析symbol (CompactString)
    if len(data) < offset + 8:
        raise ValueError("数据长度不足，无法解析symbol长度")
    symbol_len = int.from_bytes(data[offset:offset+8], 'little')
    offset += 8
    
    if len(data) < offset + symbol_len:
        raise ValueError("数据长度不足，无法解析symbol内容")
    symbol = data[offset:offset+symbol_len].decode('utf-8')
    offset += symbol_len
    
    # 解析total_supply (8字节)
    if len(data) < offset + 8:
        raise ValueError("数据长度不足，无法解析total_supply")
    total_supply = int.from_bytes(data[offset:offset+8], 'little')
    offset += 8
    
    # 解析creator (32字节)
    if len(data) < offset + 32:
        raise ValueError("数据长度不足，无法解析creator")
    creator_bytes = data[offset:offset+32]
    creator = Address(creator_bytes)
    offset += 32
    
    # 解析mintable (1字节)
    if len(data) < offset + 1:
        raise ValueError("数据长度不足，无法解析mintable")
    mintable = bool(data[offset])
    offset += 1
    
    # 解析to (32字节)
    if len(data) < offset + 32:
        raise ValueError("数据长度不足，无法解析to")
    to_bytes = data[offset:offset+32]
    to = Address(to_bytes)
    offset += 32
    
    # 解析balance_id (16字节)
    if len(data) < offset + 16:
        raise ValueError("数据长度不足，无法解析balance_id")
    balance_id_bytes = data[offset:offset+16]
    balance_id = ObjectID(balance_id_bytes)
    offset += 16
    
    return TokenCreatedEvent(
        token_id=token_id,
        token_address=token_address,
        name=name,
        symbol=symbol,
        total_supply=total_supply,
        creator=creator,
        mintable=mintable,
        to=to,
        balance_id=balance_id
    )
