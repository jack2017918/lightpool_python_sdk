#!/usr/bin/env python3
"""
详细测试JSON格式，模拟实际的HTTP请求
"""
import json
import aiohttp
import asyncio

async def test_json_request():
    """测试实际的JSON请求"""
    
    # 模拟下单交易的JSON结构
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "submitTransaction",
        "params": [{
            "tx": {
                "transaction": {
                    "sender": [214, 200, 27, 9, 113, 49, 192, 74, 170, 36, 103, 191, 184, 236, 59, 91, 194, 212, 231, 42, 42, 203, 77, 173, 135, 110, 22, 94, 25, 223, 97, 196],
                    "expiration": 18446744073709551615,
                    "actions": [{
                        "inputs": [
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 13, 129, 2, 93, 102, 189, 176, 178, 119, 45, 202, 213, 36, 63, 80, 163, 9, 110],
                            [170, 36, 103, 191, 184, 236, 59, 91, 194, 212, 231, 42, 42, 203, 77, 173, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 13, 126]
                        ],
                        "contract": [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        "action": 746789037603618816,
                        "params": [1, 0, 0, 0, 64, 75, 76, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 116, 59, 164, 11, 0, 0, 0]
                    }]
                },
                "signatures": [{
                    "part1": [208, 110, 237, 219, 80, 213, 237, 57, 219, 15, 14, 81, 166, 136, 54, 79, 76, 38, 64, 75, 160, 250, 217, 128, 95, 235, 254, 221, 165, 180, 162, 238],
                    "part2": [35, 122, 90, 207, 69, 43, 20, 173, 215, 177, 243, 29, 59, 55, 113, 6, 73, 228, 199, 79, 154, 219, 46, 179, 213, 251, 164, 126, 211, 146, 216, 14]
                }]
            }
        }]
    }
    
    print("=== 测试JSON序列化格式 ===")
    
    # 方式1: 使用json.dumps()
    json_str1 = json.dumps(payload, separators=(',', ':'), ensure_ascii=True)
    print(f"方式1 - json.dumps():")
    print(f"长度: {len(json_str1)}")
    print(f"最后10个字符: {repr(json_str1[-10:])}")
    print(f"最后10个字符ASCII码: {[ord(c) for c in json_str1[-10:]]}")
    print(f"JSON字符串: {json_str1}")
    print()
    
    # 方式2: 使用aiohttp的json参数
    print("方式2 - 使用aiohttp的json参数:")
    print(f"payload: {payload}")
    print()
    
    # 验证JSON是否有效
    try:
        parsed1 = json.loads(json_str1)
        print("✅ 方式1 JSON解析成功")
    except json.JSONDecodeError as e:
        print(f"❌ 方式1 JSON解析失败: {e}")
    
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
    asyncio.run(test_json_request()) 