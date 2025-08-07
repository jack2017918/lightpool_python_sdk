#!/usr/bin/env python3
"""
Compare JSON format between Python and Rust
"""

import asyncio
import json
import aiohttp
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

async def test_json_comparison():
    """Compare JSON format between Python and Rust"""
    
    # Create a simple transaction
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
    
    # Create JSON-RPC request
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "submitTransaction",
        "params": [submit_transaction_params]
    }
    
    print("=== JSON Analysis ===")
    
    # Test different JSON serialization methods
    json_methods = [
        ("json.dumps with default", lambda x: json.dumps(x)),
        ("json.dumps with separators", lambda x: json.dumps(x, separators=(',', ':'))),
        ("json.dumps with indent", lambda x: json.dumps(x, indent=2)),
        ("json.dumps with ensure_ascii=False", lambda x: json.dumps(x, ensure_ascii=False)),
    ]
    
    for method_name, method in json_methods:
        try:
            json_str = method(payload)
            print(f"\n{method_name}:")
            print(f"  Length: {len(json_str)}")
            print(f"  First 100 chars: {json_str[:100]}")
            print(f"  Last 100 chars: {json_str[-100:]}")
            
            # Test if this JSON is valid
            parsed = json.loads(json_str)
            print(f"  ✅ Valid JSON")
            
            # Test sending to server
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:26300/rpc",
                    json=parsed,  # Use parsed to ensure clean JSON
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        print(f"  ✅ Server accepted JSON")
                    else:
                        print(f"  ❌ Server rejected JSON: {response_text}")
                        
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_json_comparison())
