#!/usr/bin/env python3
"""
Test place order error details
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

async def test_place_order_error():
    """Test place order error details"""
    
    client = LightPoolClient("http://localhost:26300")
    
    # Create a simple transaction that should fail
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
    
    print("=== Place Order RPC Test ===")
    print(f"JSON payload length: {len(json.dumps(payload))}")
    
    # Test sending to server
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:26300/rpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"\n=== Response ===")
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"Response text: {response_text}")
                
                if response.status == 200:
                    response_json = await response.json()
                    print(f"Response JSON: {json.dumps(response_json, indent=2)}")
                    
                    # Check if there's an error in the result
                    if "result" in response_json and "receipt" in response_json["result"]:
                        receipt = response_json["result"]["receipt"]
                        if "status" in receipt:
                            status = receipt["status"]
                            print(f"Transaction status: {status}")
                            if "Failure" in status:
                                print(f"Failure reason: {status['Failure']}")
                else:
                    print(f"Error response: {response_text}")
                    
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_place_order_error())
