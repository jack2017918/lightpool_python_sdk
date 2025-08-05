#!/usr/bin/env python3
"""
LightPool Python SDK 测试运行脚本

支持自定义参数来运行不同类型的测试。
"""

import sys
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description="运行LightPool Python SDK测试")
    parser.add_argument("--run-integration", action="store_true", 
                       help="运行集成测试（需要运行中的LightPool节点）")
    parser.add_argument("--unit-only", action="store_true",
                       help="只运行单元测试")
    parser.add_argument("--integration-only", action="store_true",
                       help="只运行集成测试")
    parser.add_argument("--all", action="store_true",
                       help="运行所有测试")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出")
    
    args = parser.parse_args()
    
    # 构建pytest命令
    cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.run_integration or args.integration_only:
        # 运行集成测试
        cmd.extend(["tests/integration/", "-m", "integration"])
        print("运行集成测试...")
    elif args.unit_only:
        # 只运行单元测试
        cmd.extend(["tests/", "-m", "not integration"])
        print("运行单元测试...")
    elif args.all:
        # 运行所有测试
        cmd.extend(["tests/"])
        print("运行所有测试...")
    else:
        # 默认运行单元测试
        cmd.extend(["tests/", "-m", "not integration"])
        print("运行单元测试...")
    
    # 执行命令
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"运行测试时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 