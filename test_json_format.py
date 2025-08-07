#!/usr/bin/env python3
"""
测试JSON格式是否正确
"""
import json

def test_json_format():
    """测试JSON格式"""
    
    # 模拟下单交易的JSON结构
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "submitTransaction",
        "params": [{
            "tx": {
                "transaction": {
                    "sender": [59, 14, 232, 147, 64, 89, 154, 6, 157, 6, 209, 69, 84, 40, 248, 109, 33, 86, 215, 230, 148, 42, 193, 184, 62, 36, 166, 159, 180, 56, 201, 239],
                    "expiration": 18446744073709551615,
                    "actions": [{
                        "inputs": [
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 12, 2, 116, 111, 60, 240, 104, 136, 67, 225, 184, 45, 69, 126, 175, 112, 35],
                            [157, 6, 209, 69, 84, 40, 248, 109, 33, 86, 215, 230, 148, 42, 193, 184, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 9]
                        ],
                        "contract": [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        "action": 746789037603618816,
                        "params": [1, 0, 0, 0, 64, 75, 76, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 116, 59, 164, 11, 0, 0, 0]
                    }]
                },
                "signatures": [{
                    "part1": [183, 233, 60, 45, 9, 36, 204, 12, 47, 61, 139, 11, 92, 89, 68, 10, 106, 32, 229, 155, 128, 98, 7, 177, 105, 165, 37, 15, 72, 136, 53, 150],
                    "part2": [147, 66, 87, 244, 83, 190, 211, 89, 17, 157, 43, 122, 143, 241, 221, 18, 113, 107, 237, 229, 76, 85, 217, 74, 190, 105, 9, 77, 133, 68, 225, 2]
                }]
            }
        }]
    }
    
    # 测试不同的JSON序列化方式
    print("=== 测试JSON序列化格式 ===")
    
    # 方式1: 使用json.dumps()
    json_str1 = json.dumps(payload, separators=(',', ':'), ensure_ascii=True)
    print(f"方式1 - json.dumps():")
    print(f"长度: {len(json_str1)}")
    print(f"最后10个字符: {repr(json_str1[-10:])}")
    print(f"最后10个字符ASCII码: {[ord(c) for c in json_str1[-10:]]}")
    print()
    
    # 方式2: 使用json.dumps() + indent
    json_str2 = json.dumps(payload, separators=(',', ':'), ensure_ascii=True, indent=2)
    print(f"方式2 - json.dumps() + indent:")
    print(f"长度: {len(json_str2)}")
    print(f"最后10个字符: {repr(json_str2[-10:])}")
    print(f"最后10个字符ASCII码: {[ord(c) for c in json_str2[-10:]]}")
    print()
    
    # 方式3: 使用json.dumps() + sort_keys
    json_str3 = json.dumps(payload, separators=(',', ':'), ensure_ascii=True, sort_keys=True)
    print(f"方式3 - json.dumps() + sort_keys:")
    print(f"长度: {len(json_str3)}")
    print(f"最后10个字符: {repr(json_str3[-10:])}")
    print(f"最后10个字符ASCII码: {[ord(c) for c in json_str3[-10:]]}")
    print()
    
    # 验证JSON是否有效
    try:
        parsed1 = json.loads(json_str1)
        print("✅ 方式1 JSON解析成功")
    except json.JSONDecodeError as e:
        print(f"❌ 方式1 JSON解析失败: {e}")
    
    try:
        parsed2 = json.loads(json_str2)
        print("✅ 方式2 JSON解析成功")
    except json.JSONDecodeError as e:
        print(f"❌ 方式2 JSON解析失败: {e}")
    
    try:
        parsed3 = json.loads(json_str3)
        print("✅ 方式3 JSON解析成功")
    except json.JSONDecodeError as e:
        print(f"❌ 方式3 JSON解析失败: {e}")

if __name__ == "__main__":
    test_json_format() 