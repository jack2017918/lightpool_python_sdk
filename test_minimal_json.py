#!/usr/bin/env python3
"""
Test minimal JSON format
"""

import asyncio
import json
import aiohttp
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

async def test_minimal_json():
    """Test minimal JSON format"""
    
    # Create a minimal transaction JSON
    transaction_dict = {
        "sender": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
        "expiration": 18446744073709551615,
        "actions": [
            {
                "inputs": [],
                "contract": [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "action": 746789037603618816,
                "params": [1, 0, 0, 0, 64, 75, 76, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 116, 59, 164, 11, 0, 0, 0]
            }
        ]
    }
    
    signatures_list = [
        {
            "part1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
            "part2": [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64]
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
    
    print("=== JSON-RPC Payload ===")
    json_str = json.dumps(payload, separators=(',', ':'))
    print(f"JSON length: {len(json_str)}")
    print(f"JSON: {json_str}")
    
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
                else:
                    print(f"Error response: {response_text}")
                    
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_minimal_json())
