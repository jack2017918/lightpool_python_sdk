#!/usr/bin/env python3
"""
Test RPC error details
"""

import asyncio
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

async def test_rpc_error():
    """Test RPC error details"""
    
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
    
    try:
        # Try to submit the transaction
        response = await client.submit_transaction(tx)
        print(f"✅ Success: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'details'):
            print(f"Error details: {e.details}")
        if hasattr(e, 'message'):
            print(f"Error message: {e.message}")
        if hasattr(e, 'code'):
            print(f"Error code: {e.code}")

if __name__ == "__main__":
    asyncio.run(test_rpc_error())
