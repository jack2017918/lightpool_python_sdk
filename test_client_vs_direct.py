#!/usr/bin/env python3
"""
Compare Python client vs direct HTTP request
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

async def test_client_vs_direct():
    """Compare Python client vs direct HTTP request"""
    
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
    
    print("=== Client vs Direct Comparison ===")
    
    # Test 1: Direct HTTP request (working)
    print("\n1. Direct HTTP request:")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:26300/rpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_text = await response.text()
                print(f"  Status: {response.status}")
                print(f"  Response: {response_text[:200]}...")
                if response.status == 200:
                    print("  ✅ Direct request successful")
                else:
                    print("  ❌ Direct request failed")
        except Exception as e:
            print(f"  ❌ Direct request error: {e}")
    
    # Test 2: Python client request (failing)
    print("\n2. Python client request:")
    client = LightPoolClient("http://localhost:26300")
    try:
        # This should fail with the same error
        result = await client.submit_transaction(tx)
        print(f"  ✅ Client request successful: {result}")
    except Exception as e:
        print(f"  ❌ Client request error: {e}")
        print(f"  Error type: {type(e).__name__}")
        if hasattr(e, 'details'):
            print(f"  Error details: {e.details}")

if __name__ == "__main__":
    asyncio.run(test_client_vs_direct())
