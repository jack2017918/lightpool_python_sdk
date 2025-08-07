#!/usr/bin/env python3
"""
Debug JSON format differences between Python and Rust SDKs
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from lightpool_sdk import (
    LightPoolClient, Signer, TransactionBuilder, ActionBuilder,
    Address, ObjectID, U256,
    CreateTokenParams, CreateMarketParams, PlaceOrderParams, CancelOrderParams,
    OrderSide, TimeInForce, MarketState, LimitOrderParams, OrderParamsType,
    TOKEN_CONTRACT_ADDRESS, SPOT_CONTRACT_ADDRESS, create_limit_order_params
)

def debug_json_format():
    """Debug the JSON format being sent"""
    
    # Create a simple transaction to test
    signer = Signer.new()
    address = signer.address()
    
    # Create a simple place order action
    order_params = create_limit_order_params(
        side=OrderSide.SELL,
        amount=5_000_000,
        limit_price=50_000_000_000,
        tif=TimeInForce.GTC
    )
    
    # Create action
    action = ActionBuilder.place_order(
        market_address=SPOT_CONTRACT_ADDRESS,
        market_id=ObjectID.random(),
        balance_id=ObjectID.random(),
        params=order_params
    )
    
    # Create transaction
    tx = TransactionBuilder.new()\
        .sender(address)\
        .expiration(0xFFFFFFFFFFFFFFFF)\
        .add_action(action)\
        .build_and_sign(signer)
    
    # Extract the JSON that would be sent
    transaction_dict = {
        "sender": list(address.to_bytes()),
        "expiration": tx.signed_transaction.transaction.expiration,
        "actions": [
            {
                "inputs": [list(bytes.fromhex(str(obj_id).replace('0x', ''))) for obj_id in action.input_objects],
                "contract": list(action.target_address.to_bytes()),
                "action": 746789037603618816,  # ord_place
                "params": list(action.params)
            }
        ]
    }
    
    signatures_list = [
        {
            "part1": list(tx.signed_transaction.signatures[0][:32]),
            "part2": list(tx.signed_transaction.signatures[0][32:])
        }
    ]
    
    submit_transaction_params = {
        "tx": {
            "transaction": transaction_dict,
            "signatures": signatures_list
        }
    }
    
    print("=== JSON Format Debug ===")
    print(f"Transaction JSON:")
    print(json.dumps(transaction_dict, indent=2))
    print(f"\nSubmitTransactionParams:")
    print(json.dumps(submit_transaction_params, indent=2))
    
    # Test the action name encoding
    print(f"\n=== Action Name Debug ===")
    print(f"Action name: {action.action_name}")
    
    # Test the _action_name_to_u64 function
    def action_name_to_u64(action_name: str) -> int:
        BASE = 32
        NAME_LENGTH = 12
        
        if len(action_name) > NAME_LENGTH:
            raise ValueError(f"Action name too long: {action_name}")
        
        result = 0
        for c in action_name:
            if c == '_':
                digit = 0
            elif '1' <= c <= '5':
                digit = ord(c) - ord('1') + 1
            elif 'a' <= c <= 'z':
                digit = ord(c) - ord('a') + 6
            else:
                raise ValueError(f"Invalid character in action name: {c}")
            
            result = result * BASE + digit
        
        # 用零填充到12个字符
        chars_processed = len(action_name)
        while chars_processed < NAME_LENGTH:
            result = result * BASE
            chars_processed += 1
        
        return result
    
    encoded = action_name_to_u64(action.action_name)
    print(f"Encoded action name: {encoded}")
    print(f"Expected for 'ord_place': 746789037603618816")
    print(f"Match: {encoded == 746789037603618816}")

if __name__ == "__main__":
    debug_json_format()
