#!/usr/bin/env python3
"""
最终测试JSON格式
"""
import json
import aiohttp
import asyncio

async def test_final():
    """最终测试"""
    
    # 创建一个最简单的JSON请求
    payload = {
        "jsonrpc": "2.0",
        "method": "submitTransaction",
        "params": [{
            "tx": {
                "transaction": {
                    "sender": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
                    "expiration": 1234567890,
                    "actions": [{
                        "inputs": [
                            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
                        ],
                        "contract": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
                        "action": 123456789,
                        "params": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
                    }]
                },
                "signatures": [{
                    "part1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
                    "part2": [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64]
                }]
            }
        }],
        "id": 1
    }
    
    print("=== 最终测试 ===")
    
    # 序列化JSON
    json_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=True)
    print(f"JSON字符串长度: {len(json_str)}")
    print(f"JSON字符串: {json_str}")
    print(f"JSON字符串最后10个字符: {repr(json_str[-10:])}")
    print(f"JSON字符串最后10个字符ASCII码: {[ord(c) for c in json_str[-10:]]}")
    print()
    
    # 验证JSON是否有效
    try:
        parsed = json.loads(json_str)
        print("✅ JSON解析成功")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
    
    # 测试发送到实际的RPC服务器
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8080/rpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"HTTP状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"响应: {data}")
                else:
                    text = await response.text()
                    print(f"错误响应: {text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_final()) 