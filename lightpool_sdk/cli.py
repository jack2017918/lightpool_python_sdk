#!/usr/bin/env python3
"""
LightPool SDK 命令行工具

提供现货交易的命令行接口，支持：
- 创建代币和市场
- 下单和撤单
- 查询订单簿和交易历史
- 性能测试
"""

import asyncio
import argparse
import json
import logging
from typing import Optional, Dict, Any

from .client import LightPoolClient
from .crypto import Signer
from .transaction import TransactionBuilder, ActionBuilder
from .types import (
    Address, ObjectID, U256,
    CreateTokenParams, CreateMarketParams, PlaceOrderParams, CancelOrderParams,
    OrderSide, TimeInForce, MarketState, LimitOrderParams,
    TOKEN_CONTRACT_ADDRESS, SPOT_CONTRACT_ADDRESS
)


class LightPoolCLI:
    """LightPool命令行工具"""
    
    def __init__(self, rpc_url: str = "http://localhost:26300"):
        self.rpc_url = rpc_url
        self.client: Optional[LightPoolClient] = None
        self.signer: Optional[Signer] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = LightPoolClient(self.rpc_url)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.close()
    
    def load_signer(self, private_key: Optional[str] = None) -> Signer:
        """加载签名者"""
        if private_key:
            if private_key.startswith("0x"):
                private_key = private_key[2:]
            secret_key_bytes = bytes.fromhex(private_key)
            self.signer = Signer.from_secret_key_bytes(secret_key_bytes)
        else:
            self.signer = Signer.new()
        
        print(f"使用地址: {self.signer.address()}")
        return self.signer
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            is_healthy = await self.client.health_check()
            if is_healthy:
                print("✅ 节点连接正常")
                return True
            else:
                print("⚠️ 节点响应但不健康")
                return False
        except Exception as e:
            print(f"❌ 连接节点失败: {e}")
            return False
    
    async def create_token(self, name: str, symbol: str, decimals: int,
                          total_supply: int, mintable: bool = True) -> Dict[str, Any]:
        """创建代币"""
        print(f"创建代币: {name} ({symbol})")
        
        create_params = CreateTokenParams(
            name=name,
            symbol=symbol,
            decimals=decimals,
            total_supply=U256(total_supply),
            mintable=mintable,
            to=self.signer.address()
        )
        
        action = ActionBuilder.create_token(TOKEN_CONTRACT_ADDRESS, create_params)
        
        tx = TransactionBuilder.new()\
            .sender(self.signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(self.signer)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            if response["receipt"].is_success():
                print(f"✅ {symbol} 代币创建成功")
                print(f"交易哈希: {response['digest']}")
                return {
                    "success": True,
                    "digest": response["digest"],
                    "receipt": response["receipt"]
                }
            else:
                print(f"❌ {symbol} 代币创建失败")
                return {"success": False, "error": "Token creation failed"}
                
        except Exception as e:
            print(f"❌ 提交代币创建交易失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_market(self, name: str, base_token: str, quote_token: str,
                           min_order_size: int, tick_size: int) -> Dict[str, Any]:
        """创建市场"""
        print(f"创建市场: {name}")
        
        # 解析代币地址
        base_token_addr = Address(base_token)
        quote_token_addr = Address(quote_token)
        
        market_params = CreateMarketParams(
            name=name,
            base_token=base_token_addr,
            quote_token=quote_token_addr,
            min_order_size=min_order_size,
            tick_size=tick_size,
            maker_fee_bps=10,        # 0.1% maker费用
            taker_fee_bps=20,        # 0.2% taker费用
            allow_market_orders=True,
            state=MarketState.ACTIVE,
            limit_order=True
        )
        
        action = ActionBuilder.create_market(SPOT_CONTRACT_ADDRESS, market_params)
        
        tx = TransactionBuilder.new()\
            .sender(self.signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(self.signer)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            if response["receipt"].is_success():
                print(f"✅ {name} 市场创建成功")
                print(f"交易哈希: {response['digest']}")
                return {
                    "success": True,
                    "digest": response["digest"],
                    "receipt": response["receipt"]
                }
            else:
                print(f"❌ {name} 市场创建失败")
                return {"success": False, "error": "Market creation failed"}
                
        except Exception as e:
            print(f"❌ 提交市场创建交易失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def place_order(self, market_address: str, market_id: str, balance_id: str,
                         side: str, amount: int, price: int) -> Dict[str, Any]:
        """下单"""
        side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        side_str = "买单" if side_enum == OrderSide.BUY else "卖单"
        
        print(f"下{side_str}: {amount} 数量, 价格 {price}")
        
        order_params = PlaceOrderParams(
            side=side_enum,
            amount=amount,
            order_type=LimitOrderParams(TimeInForce.GTC),
            limit_price=price
        )
        
        action = ActionBuilder.place_order(
            Address(market_address),
            ObjectID(market_id),
            ObjectID(balance_id),
            order_params
        )
        
        tx = TransactionBuilder.new()\
            .sender(self.signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(self.signer)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            if response["receipt"].is_success():
                print(f"✅ {side_str}下单成功")
                print(f"交易哈希: {response['digest']}")
                return {
                    "success": True,
                    "digest": response["digest"],
                    "receipt": response["receipt"]
                }
            else:
                print(f"❌ {side_str}下单失败")
                return {"success": False, "error": "Order placement failed"}
                
        except Exception as e:
            print(f"❌ 提交{side_str}交易失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_order(self, market_address: str, market_id: str, order_id: str) -> Dict[str, Any]:
        """撤单"""
        print(f"撤单: {order_id}")
        
        cancel_params = CancelOrderParams(order_id=ObjectID(order_id))
        
        action = ActionBuilder.cancel_order(
            Address(market_address),
            ObjectID(market_id),
            cancel_params
        )
        
        tx = TransactionBuilder.new()\
            .sender(self.signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(self.signer)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            if response["receipt"].is_success():
                print("✅ 撤单成功")
                print(f"交易哈希: {response['digest']}")
                return {
                    "success": True,
                    "digest": response["digest"],
                    "receipt": response["receipt"]
                }
            else:
                print("⚠️ 撤单失败（可能订单已成交或被撤销）")
                return {"success": False, "error": "Order cancellation failed"}
                
        except Exception as e:
            print(f"❌ 提交撤单交易失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_order_book(self, market_id: str, depth: int = 10) -> Dict[str, Any]:
        """获取订单簿"""
        print(f"获取订单簿: {market_id}, 深度: {depth}")
        
        try:
            result = await self.client.get_order_book(ObjectID(market_id), depth)
            if result:
                print("✅ 订单簿获取成功")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return {"success": True, "data": result}
            else:
                print("❌ 订单簿获取失败")
                return {"success": False, "error": "Failed to get order book"}
                
        except Exception as e:
            print(f"❌ 获取订单簿失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_trades(self, market_id: str, limit: int = 100) -> Dict[str, Any]:
        """获取交易历史"""
        print(f"获取交易历史: {market_id}, 限制: {limit}")
        
        try:
            result = await self.client.get_trades(ObjectID(market_id), limit)
            if result:
                print("✅ 交易历史获取成功")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return {"success": True, "data": result}
            else:
                print("❌ 交易历史获取失败")
                return {"success": False, "error": "Failed to get trades"}
                
        except Exception as e:
            print(f"❌ 获取交易历史失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_orders(self, address: str, market_id: Optional[str] = None) -> Dict[str, Any]:
        """获取用户订单"""
        print(f"获取用户订单: {address}")
        if market_id:
            print(f"市场ID: {market_id}")
        
        try:
            result = await self.client.get_orders(Address(address), ObjectID(market_id) if market_id else None)
            print("✅ 用户订单获取成功")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return {"success": True, "data": result}
                
        except Exception as e:
            print(f"❌ 获取用户订单失败: {e}")
            return {"success": False, "error": str(e)}


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LightPool SDK 命令行工具")
    parser.add_argument("--rpc-url", default="http://localhost:26300", help="RPC服务器URL")
    parser.add_argument("--private-key", help="私钥（十六进制）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 健康检查命令
    subparsers.add_parser("health", help="健康检查")
    
    # 创建代币命令
    create_token_parser = subparsers.add_parser("create-token", help="创建代币")
    create_token_parser.add_argument("--name", required=True, help="代币名称")
    create_token_parser.add_argument("--symbol", required=True, help="代币符号")
    create_token_parser.add_argument("--decimals", type=int, default=6, help="小数位数")
    create_token_parser.add_argument("--total-supply", type=int, required=True, help="总供应量")
    create_token_parser.add_argument("--mintable", action="store_true", help="是否可铸造")
    
    # 创建市场命令
    create_market_parser = subparsers.add_parser("create-market", help="创建市场")
    create_market_parser.add_argument("--name", required=True, help="市场名称")
    create_market_parser.add_argument("--base-token", required=True, help="基础代币地址")
    create_market_parser.add_argument("--quote-token", required=True, help="报价代币地址")
    create_market_parser.add_argument("--min-order-size", type=int, default=100000, help="最小订单大小")
    create_market_parser.add_argument("--tick-size", type=int, default=100000, help="价格精度")
    
    # 下单命令
    place_order_parser = subparsers.add_parser("place-order", help="下单")
    place_order_parser.add_argument("--market-address", required=True, help="市场地址")
    place_order_parser.add_argument("--market-id", required=True, help="市场ID")
    place_order_parser.add_argument("--balance-id", required=True, help="余额ID")
    place_order_parser.add_argument("--side", choices=["buy", "sell"], required=True, help="订单方向")
    place_order_parser.add_argument("--amount", type=int, required=True, help="订单数量")
    place_order_parser.add_argument("--price", type=int, required=True, help="订单价格")
    
    # 撤单命令
    cancel_order_parser = subparsers.add_parser("cancel-order", help="撤单")
    cancel_order_parser.add_argument("--market-address", required=True, help="市场地址")
    cancel_order_parser.add_argument("--market-id", required=True, help="市场ID")
    cancel_order_parser.add_argument("--order-id", required=True, help="订单ID")
    
    # 查询订单簿命令
    order_book_parser = subparsers.add_parser("order-book", help="查询订单簿")
    order_book_parser.add_argument("--market-id", required=True, help="市场ID")
    order_book_parser.add_argument("--depth", type=int, default=10, help="深度")
    
    # 查询交易历史命令
    trades_parser = subparsers.add_parser("trades", help="查询交易历史")
    trades_parser.add_argument("--market-id", required=True, help="市场ID")
    trades_parser.add_argument("--limit", type=int, default=100, help="限制数量")
    
    # 查询用户订单命令
    orders_parser = subparsers.add_parser("orders", help="查询用户订单")
    orders_parser.add_argument("--address", required=True, help="用户地址")
    orders_parser.add_argument("--market-id", help="市场ID（可选）")
    
    args = parser.parse_args()
    
    # 配置日志
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    if not args.command:
        parser.print_help()
        return
    
    async with LightPoolCLI(args.rpc_url) as cli:
        # 加载签名者
        cli.load_signer(args.private_key)
        
        # 执行命令
        if args.command == "health":
            await cli.health_check()
        
        elif args.command == "create-token":
            await cli.create_token(
                name=args.name,
                symbol=args.symbol,
                decimals=args.decimals,
                total_supply=args.total_supply,
                mintable=args.mintable
            )
        
        elif args.command == "create-market":
            await cli.create_market(
                name=args.name,
                base_token=args.base_token,
                quote_token=args.quote_token,
                min_order_size=args.min_order_size,
                tick_size=args.tick_size
            )
        
        elif args.command == "place-order":
            await cli.place_order(
                market_address=args.market_address,
                market_id=args.market_id,
                balance_id=args.balance_id,
                side=args.side,
                amount=args.amount,
                price=args.price
            )
        
        elif args.command == "cancel-order":
            await cli.cancel_order(
                market_address=args.market_address,
                market_id=args.market_id,
                order_id=args.order_id
            )
        
        elif args.command == "order-book":
            await cli.get_order_book(
                market_id=args.market_id,
                depth=args.depth
            )
        
        elif args.command == "trades":
            await cli.get_trades(
                market_id=args.market_id,
                limit=args.limit
            )
        
        elif args.command == "orders":
            await cli.get_orders(
                address=args.address,
                market_id=args.market_id
            )


if __name__ == "__main__":
    asyncio.run(main()) 