import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .types import ObjectID, Address, OrderId

logger = logging.getLogger(__name__)

@dataclass
class HumanReadableEvent:
    """Human readable event data"""
    event_type: str
    sender: Optional[str]
    contract: Optional[str]
    block_num: int
    data: Dict[str, Any]

@dataclass
class ReceiptDisplay:
    """Receipt display structure"""
    status: str
    events: List[HumanReadableEvent]

def format_address(addr: Address) -> str:
    """Format address as hex string"""
    return f"0x{addr.to_bytes().hex()}"

def format_object_id(obj_id: ObjectID) -> str:
    """Format ObjectID as string"""
    return str(obj_id)

def format_order_id(order_id: OrderId) -> str:
    """Format OrderId as string"""
    return str(order_id)

def parse_token_event_data(event_type: str, data: bytes) -> Optional[Dict[str, Any]]:
    """Parse token event data to human readable format"""
    try:
        if event_type == "token_created":
            # Parse TokenCreatedEvent
            if len(data) >= 16:  # token_id
                token_id_bytes = data[0:16]
                token_id = ObjectID(token_id_bytes)
                
                if len(data) >= 48:  # token_address (32 bytes after token_id)
                    token_address_bytes = data[16:48]
                    token_address = Address(token_address_bytes)
                    
                    # Parse name (string)
                    name_start = 48
                    name_length = data[name_start] if name_start < len(data) else 0
                    name_end = name_start + 1 + name_length
                    name = data[name_start + 1:name_end].decode('utf-8', errors='ignore')
                    
                    # Parse symbol (string)
                    symbol_start = name_end
                    symbol_length = data[symbol_start] if symbol_start < len(data) else 0
                    symbol_end = symbol_start + 1 + symbol_length
                    symbol = data[symbol_start + 1:symbol_end].decode('utf-8', errors='ignore')
                    
                    # Parse total_supply (u64)
                    total_supply_start = symbol_end
                    if total_supply_start + 8 <= len(data):
                        total_supply = int.from_bytes(data[total_supply_start:total_supply_start + 8], 'little')
                        
                        # Parse creator (Address)
                        creator_start = total_supply_start + 8
                        if creator_start + 32 <= len(data):
                            creator_bytes = data[creator_start:creator_start + 32]
                            creator = Address(creator_bytes)
                            
                            # Parse balance_id (ObjectID)
                            balance_start = creator_start + 32
                            if balance_start + 16 <= len(data):
                                balance_id_bytes = data[balance_start:balance_start + 16]
                                balance_id = ObjectID(balance_id_bytes)
                                
                                return {
                                    "token_id": format_object_id(token_id),
                                    "token_address": format_address(token_address),
                                    "name": name,
                                    "symbol": symbol,
                                    "total_supply": total_supply,
                                    "creator": format_address(creator),
                                    "balance_id": format_object_id(balance_id)
                                }
        
        elif event_type == "Transfer":
            # Parse TransferEvent
            if len(data) >= 32:  # from address
                from_bytes = data[0:32]
                from_addr = Address(from_bytes)
                
                if len(data) >= 64:  # to address
                    to_bytes = data[32:64]
                    to_addr = Address(to_bytes)
                    
                    if len(data) >= 72:  # amount (u64)
                        amount = int.from_bytes(data[64:72], 'little')
                        
                        if len(data) >= 88:  # original_balance_id
                            original_balance_bytes = data[72:88]
                            original_balance_id = ObjectID(original_balance_bytes)
                            
                            if len(data) >= 104:  # to_balance_id
                                to_balance_bytes = data[88:104]
                                to_balance_id = ObjectID(to_balance_bytes)
                                
                                # Parse remainder_id (optional ObjectID)
                                remainder_id = None
                                remainder = 0
                                
                                if len(data) >= 120:  # remainder_id (16 bytes)
                                    remainder_id_bytes = data[104:120]
                                    remainder_id = ObjectID(remainder_id_bytes)
                                    
                                    if len(data) >= 128:  # remainder (u64)
                                        remainder = int.from_bytes(data[120:128], 'little')
                                
                                return {
                                    "from": format_address(from_addr),
                                    "to": format_address(to_addr),
                                    "amount": amount,
                                    "original_balance_id": format_object_id(original_balance_id),
                                    "to_balance_id": format_object_id(to_balance_id),
                                    "remainder_id": format_object_id(remainder_id) if remainder_id else None,
                                    "remainder": remainder
                                }
    
    except Exception as e:
        logger.warning(f"Failed to parse token event data: {e}")
    
    return None

def parse_spot_event_data(event_type: str, data: bytes) -> Optional[Dict[str, Any]]:
    """Parse spot event data to human readable format"""
    try:
        if event_type == "market_created":
            # Parse MarketCreatedEvent
            if len(data) >= 16:  # market_id
                market_id_bytes = data[0:16]
                market_id = ObjectID(market_id_bytes)
                
                if len(data) >= 48:  # market_address (32 bytes after market_id)
                    market_address_bytes = data[16:48]
                    market_address = Address(market_address_bytes)
                    
                    # Parse name (string)
                    name_start = 48
                    name_length = data[name_start] if name_start < len(data) else 0
                    name_end = name_start + 1 + name_length
                    name = data[name_start + 1:name_end].decode('utf-8', errors='ignore')
                    
                    # Parse base_token (Address)
                    base_token_start = name_end
                    if base_token_start + 32 <= len(data):
                        base_token_bytes = data[base_token_start:base_token_start + 32]
                        base_token = Address(base_token_bytes)
                        
                        # Parse quote_token (Address)
                        quote_token_start = base_token_start + 32
                        if quote_token_start + 32 <= len(data):
                            quote_token_bytes = data[quote_token_start:quote_token_start + 32]
                            quote_token = Address(quote_token_bytes)
                            
                            # Parse base_balance (ObjectID)
                            base_balance_start = quote_token_start + 32
                            if base_balance_start + 16 <= len(data):
                                base_balance_bytes = data[base_balance_start:base_balance_start + 16]
                                base_balance = ObjectID(base_balance_bytes)
                                
                                # Parse quote_balance (ObjectID)
                                quote_balance_start = base_balance_start + 16
                                if quote_balance_start + 16 <= len(data):
                                    quote_balance_bytes = data[quote_balance_start:quote_balance_start + 16]
                                    quote_balance = ObjectID(quote_balance_bytes)
                                    
                                    # Parse price_index_id (ObjectID)
                                    price_index_start = quote_balance_start + 16
                                    if price_index_start + 16 <= len(data):
                                        price_index_bytes = data[price_index_start:price_index_start + 16]
                                        price_index_id = ObjectID(price_index_bytes)
                                        
                                        # Parse min_order_size (u64)
                                        min_order_start = price_index_start + 16
                                        if min_order_start + 8 <= len(data):
                                            min_order_size = int.from_bytes(data[min_order_start:min_order_start + 8], 'little')
                                            
                                            # Parse tick_size (u64)
                                            tick_size_start = min_order_start + 8
                                            if tick_size_start + 8 <= len(data):
                                                tick_size = int.from_bytes(data[tick_size_start:tick_size_start + 8], 'little')
                                                
                                                # Parse maker_fee_bps (u16)
                                                maker_fee_start = tick_size_start + 8
                                                if maker_fee_start + 2 <= len(data):
                                                    maker_fee_bps = int.from_bytes(data[maker_fee_start:maker_fee_start + 2], 'little')
                                                    
                                                    # Parse taker_fee_bps (u16)
                                                    taker_fee_start = maker_fee_start + 2
                                                    if taker_fee_start + 2 <= len(data):
                                                        taker_fee_bps = int.from_bytes(data[taker_fee_start:taker_fee_start + 2], 'little')
                                                        
                                                        # Parse allow_market_orders (bool)
                                                        allow_market_start = taker_fee_start + 2
                                                        if allow_market_start + 1 <= len(data):
                                                            allow_market_orders = bool(data[allow_market_start])
                                                            
                                                            # Parse state (u8)
                                                            state_start = allow_market_start + 1
                                                            if state_start + 1 <= len(data):
                                                                state = data[state_start]
                                                                
                                                                # Parse creator (Address)
                                                                creator_start = state_start + 1
                                                                if creator_start + 32 <= len(data):
                                                                    creator_bytes = data[creator_start:creator_start + 32]
                                                                    creator = Address(creator_bytes)
                                                                    
                                                                    return {
                                                                        "market_id": format_object_id(market_id),
                                                                        "market_address": format_address(market_address),
                                                                        "name": name,
                                                                        "base_token": format_address(base_token),
                                                                        "quote_token": format_address(quote_token),
                                                                        "base_balance": format_object_id(base_balance),
                                                                        "quote_balance": format_object_id(quote_balance),
                                                                        "price_index_id": format_object_id(price_index_id),
                                                                        "min_order_size": min_order_size,
                                                                        "tick_size": tick_size,
                                                                        "maker_fee_bps": maker_fee_bps,
                                                                        "taker_fee_bps": taker_fee_bps,
                                                                        "allow_market_orders": allow_market_orders,
                                                                        "state": state,
                                                                        "creator": format_address(creator)
                                                                    }
        
        elif event_type == "order_created":
            # Parse OrderCreatedEvent
            if len(data) >= 32:  # order_id
                order_id_bytes = data[0:32]
                order_id = OrderId(order_id_bytes)
                
                if len(data) >= 40:  # side (u8)
                    side = data[32]
                    
                    if len(data) >= 48:  # amount (u64)
                        amount = int.from_bytes(data[40:48], 'little')
                        
                        if len(data) >= 80:  # creator (Address)
                            creator_bytes = data[48:80]
                            creator = Address(creator_bytes)
                            
                            if len(data) >= 81:  # order_type (u8)
                                order_type = data[80]
                                
                                return {
                                    "order_id": format_order_id(order_id),
                                    "side": "Sell" if side == 1 else "Buy",
                                    "amount": amount,
                                    "creator": format_address(creator),
                                    "order_type": "Limit" if order_type == 0 else "Market"
                                }
        
        elif event_type == "order_filled":
            # Parse OrderFilledEvent
            if len(data) >= 32:  # order_id
                order_id_bytes = data[0:32]
                order_id = OrderId(order_id_bytes)
                
                if len(data) >= 40:  # side (u8)
                    side = data[32]
                    
                    if len(data) >= 48:  # filled_price (u64)
                        filled_price = int.from_bytes(data[40:48], 'little')
                        
                        if len(data) >= 56:  # filled_amount (u64)
                            filled_amount = int.from_bytes(data[48:56], 'little')
                            
                            if len(data) >= 64:  # remaining_amount (u64)
                                remaining_amount = int.from_bytes(data[56:64], 'little')
                                
                                if len(data) >= 65:  # is_complete (bool)
                                    is_complete = bool(data[64])
                                    
                                    return {
                                        "order_id": format_order_id(order_id),
                                        "side": "Sell" if side == 1 else "Buy",
                                        "filled_price": filled_price,
                                        "filled_amount": filled_amount,
                                        "remaining_amount": remaining_amount,
                                        "is_complete": is_complete
                                    }
        
        elif event_type == "order_cancelled":
            # Parse OrderCancelledEvent
            if len(data) >= 32:  # order_id
                order_id_bytes = data[0:32]
                order_id = OrderId(order_id_bytes)
                
                if len(data) >= 40:  # side (u8)
                    side = data[32]
                    
                    if len(data) >= 48:  # price (u64)
                        price = int.from_bytes(data[40:48], 'little')
                        
                        if len(data) >= 56:  # remaining_amount (u64)
                            remaining_amount = int.from_bytes(data[48:56], 'little')
                            
                            if len(data) >= 64:  # reason (u8)
                                reason = data[56]
                                
                                return {
                                    "order_id": format_order_id(order_id),
                                    "side": "Sell" if side == 1 else "Buy",
                                    "price": price,
                                    "remaining_amount": remaining_amount,
                                    "reason": reason
                                }
        
        elif event_type == "Transfer":
            # Parse TransferEvent (same as token events)
            return parse_token_event_data("Transfer", data)
    
    except Exception as e:
        logger.warning(f"Failed to parse spot event data: {e}")
    
    return None

def print_receipt_json(receipt: Dict[str, Any]) -> None:
    """Print transaction receipt in a human readable format (for token events)"""
    try:
        events = receipt.get("events", [])
        human_readable_events = []
        
        for event in events:
            event_type = event.get("event_type", {})
            if isinstance(event_type, dict):
                call_type = event_type.get("Call")
                if call_type:
                    event_type_str = call_type
                else:
                    event_type_str = "Unknown"
            else:
                event_type_str = str(event_type)
            
            sender = event.get("sender")
            sender_str = None
            if sender:
                sender_str = f"0x{bytes(sender).hex()}"
            
            contract = event.get("contract")
            contract_str = None
            if contract:
                contract_str = f"0x{bytes(contract).hex()}"
            
            block_num = event.get("block_num", 0)
            
            data = event.get("data", {})
            event_data = None
            if isinstance(data, dict) and "Bytes" in data:
                bytes_data = data["Bytes"]
                if isinstance(bytes_data, list):
                    event_data = parse_token_event_data(event_type_str, bytes(bytes_data))
            
            human_readable_events.append(HumanReadableEvent(
                event_type=event_type_str,
                sender=sender_str,
                contract=contract_str,
                block_num=block_num,
                data=event_data or {}
            ))
        
        display_receipt = ReceiptDisplay(
            status=str(receipt.get("status", "Unknown")),
            events=human_readable_events
        )
        
        json_str = json.dumps(display_receipt.__dict__, indent=2, default=str)
        print(f"   {json_str}")
        
    except Exception as e:
        print(f"   ⚠️  Failed to serialize receipt to JSON: {e}")

def print_spot_receipt_json(receipt: Dict[str, Any]) -> None:
    """Print spot transaction receipt in a human readable format"""
    try:
        events = receipt.get("events", [])
        human_readable_events = []
        
        for event in events:
            event_type = event.get("event_type", {})
            if isinstance(event_type, dict):
                call_type = event_type.get("Call")
                if call_type:
                    event_type_str = call_type
                else:
                    event_type_str = "Unknown"
            else:
                event_type_str = str(event_type)
            
            sender = event.get("sender")
            sender_str = None
            if sender:
                sender_str = f"0x{bytes(sender).hex()}"
            
            contract = event.get("contract")
            contract_str = None
            if contract:
                contract_str = f"0x{bytes(contract).hex()}"
            
            block_num = event.get("block_num", 0)
            
            data = event.get("data", {})
            event_data = None
            if isinstance(data, dict) and "Bytes" in data:
                bytes_data = data["Bytes"]
                if isinstance(bytes_data, list):
                    event_data = parse_spot_event_data(event_type_str, bytes(bytes_data))
            
            human_readable_events.append(HumanReadableEvent(
                event_type=event_type_str,
                sender=sender_str,
                contract=contract_str,
                block_num=block_num,
                data=event_data or {}
            ))
        
        display_receipt = ReceiptDisplay(
            status=str(receipt.get("status", "Unknown")),
            events=human_readable_events
        )
        
        json_str = json.dumps(display_receipt.__dict__, indent=2, default=str)
        print(f"   {json_str}")
        
    except Exception as e:
        print(f"   ⚠️  Failed to serialize receipt to JSON: {e}")
