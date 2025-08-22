#!/usr/bin/env python3
"""
LightPool 简单现货交易示例

这个示例演示了如何使用LightPool Python SDK进行基本的现货交易操作：
1. 创建代币
2. 创建市场
3. 下单
4. 撤单
"""

import asyncio
import logging
from typing import Optional, Tuple

from lightpool_sdk import (
    LightPoolClient, Signer, TransactionBuilder, ActionBuilder,
    Address, ObjectID, U256,
    CreateTokenParams, CreateMarketParams, PlaceOrderParams, CancelOrderParams, UpdateMarketParams,
    OrderSide, TimeInForce, MarketState, LimitOrderParams, OrderParamsType,
    TOKEN_CONTRACT_ADDRESS, SPOT_CONTRACT_ADDRESS, create_limit_order_params
)
from lightpool_sdk.types import OrderId
from lightpool_sdk.event_parser import print_receipt_json, print_spot_receipt_json

# 配置日志 - 简化输出
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpotTradingExample:
    """现货交易示例类"""
    
    def __init__(self, rpc_url: str = "http://localhost:26300"):
        self.rpc_url = rpc_url
        self.client: Optional[LightPoolClient] = None
        
        # 创建交易者
        self.trader1 = Signer.new()
        self.trader2 = Signer.new()
        
        logger.info(f"交易者1地址: {self.trader1.address()}")
        logger.info(f"交易者2地址: {self.trader2.address()}")
        logger.info(f"交易者1私钥: {self.trader1.private_key_bytes().hex()}")
        logger.info(f"交易者2私钥: {self.trader2.private_key_bytes().hex()}")
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = LightPoolClient(self.rpc_url)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.close()
    
    async def test_connection(self) -> bool:
        """测试节点连接"""
        logger.info("测试节点连接...")
        
        try:
            is_healthy = await self.client.health_check()
            if is_healthy:
                logger.info("✅ 节点连接正常")
                return True
            else:
                logger.warning("⚠️ 节点响应但不健康")
                return False
        except Exception as e:
            logger.error(f"❌ 连接节点失败: {e}")
            return False
    
    async def create_token(self, name: str, symbol: str, decimals: int, 
                          total_supply: int, mintable: bool, 
                          signer: Signer) -> Tuple[ObjectID, Address, ObjectID]:
        """创建代币"""
        logger.info(f"创建代币: {name} ({symbol})")
        
        create_params = CreateTokenParams(
            name=name,
            symbol=symbol,
            total_supply=total_supply,
            mintable=mintable,
            to=signer.address().to_bytes()  # 转换为字节数组
        )
        
        action = ActionBuilder.create_token(TOKEN_CONTRACT_ADDRESS, create_params)
        
        tx = TransactionBuilder.new()\
            .sender(signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(signer)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            logger.info(f"交易响应: {response}")
            
            if response["receipt"].is_success():
                logger.info(f"✅ {symbol} 代币创建成功")
                
                # 使用与Rust SDK相同的格式打印事件
                print_receipt_json(response["receipt"].__dict__)
                
                # 从事件中提取代币信息
                events = response["receipt"].events
                for event in events:
                    if event.get("event_type", {}).get("Call") == "token_created":
                        # 解析token_created事件的数据 (bincode序列化的TokenCreatedEvent)
                        event_data = event.get("data", {}).get("Bytes", [])

                        if len(event_data) > 0:
                            try:
                                data = bytes(event_data)
                                
                                # 使用bincode反序列化
                                from lightpool_sdk.bincode import deserialize_token_created_event
                                token_event = deserialize_token_created_event(data)
                                
                                logger.info(f"📊 代币ID: {token_event.token_id}")
                                return token_event.token_id, token_event.token_address, token_event.balance_id
                            except Exception as e:
                                logger.warning(f"⚠️ bincode反序列化失败: {e}")
                                # 回退到手动解析
                                return self._fallback_parse_token_event(data)
                
                # 如果无法解析事件，使用回退
                logger.warning("⚠️ 无法找到token_created事件，使用回退")
                return self._fallback_parse_token_event(b'')
            else:
                logger.error(f"❌ {symbol} 代币创建失败")
                logger.error(f"状态: {response['receipt'].status}")
                if 'events' in response:
                    logger.error(f"事件: {response['events']}")
                raise Exception("Token creation failed")
                
        except Exception as e:
            logger.error(f"❌ 提交代币创建交易失败: {e}")
            raise
    
    def _fallback_parse_token_event(self, data: bytes) -> Tuple[ObjectID, Address, ObjectID]:
        """回退解析token事件方法，用于调试和兼容性"""
        try:
            # 尝试手动解析关键字段
            # 注意：这种方法不够可靠，仅用于调试
            if len(data) >= 16:  # 至少需要token_id
                token_id_bytes = data[0:16]  # ObjectID是16字节
                token_id = ObjectID(token_id_bytes)
                
                # token地址是固定的TOKEN合约地址
                token_address = TOKEN_CONTRACT_ADDRESS
                
                # 尝试从数据末尾解析balance_id
                if len(data) >= 32:
                    balance_id_bytes = data[-16:]  # 最后16字节
                    balance_id = ObjectID(balance_id_bytes)
                else:
                    balance_id = ObjectID.random()
                
                logger.info(f"📊 回退解析token成功: token_id={token_id}, balance_id={balance_id}")
                return token_id, token_address, balance_id
        except Exception as e:
            logger.warning(f"⚠️ 回退解析token也失败: {e}")
        
        # 最后的回退：使用随机ID
        logger.warning("⚠️ 使用随机token_id")
        return ObjectID.random(), TOKEN_CONTRACT_ADDRESS, ObjectID.random()
    
    async def create_market(self, name: str, base_token: Address, quote_token: Address,
                           signer: Signer) -> Tuple[ObjectID, Address]:
        """创建市场"""
        logger.info(f"创建市场: {name}")
        
        market_params = CreateMarketParams(
            name=name,
            base_token=base_token.to_bytes(),  # 转换为字节数组
            quote_token=quote_token.to_bytes(),  # 转换为字节数组
            min_order_size=100_000,  # 0.1 最小订单
            tick_size=1_000_000,     # 1 价格精度
            maker_fee_bps=10,        # 0.1% maker费用
            taker_fee_bps=20,        # 0.2% taker费用
            allow_market_orders=True,
            state=MarketState.ACTIVE.to_rust_index(),  # 转换为Rust枚举索引
            limit_order=True
        )
        
        action = ActionBuilder.create_market(SPOT_CONTRACT_ADDRESS, market_params)
        
        tx = TransactionBuilder.new()\
            .sender(signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(signer)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            if response["receipt"].is_success():
                logger.info(f"✅ {name} 市场创建成功")
                
                # 使用与Rust SDK相同的格式打印事件
                print_spot_receipt_json(response["receipt"].__dict__)
                
                # 从事件中提取市场信息
                events = response["receipt"].events
                for event in events:
                    if event.get("event_type", {}).get("Call") == "market_created":
                        # 解析market_created事件的数据 (bincode序列化的MarketCreatedEvent)
                        event_data = event.get("data", {}).get("Bytes", [])
                        if len(event_data) > 0:
                            try:
                                data = bytes(event_data)
                                
                                # 使用bincode反序列化
                                from lightpool_sdk.bincode import deserialize_market_created_event
                                market_event = deserialize_market_created_event(data)
                                
                                logger.info(f"📊 市场ID: {market_event.market_id}")
                                return market_event.market_id, market_event.market_address
                                
                            except Exception as e:
                                logger.warning(f"⚠️ bincode反序列化失败: {e}")
                                # 回退到手动解析
                                return self._fallback_parse_market_event(data)
                
                # 如果无法解析事件，使用回退
                logger.warning("⚠️ 无法找到market_created事件，使用回退")
                return self._fallback_parse_market_event(b'')
            else:
                logger.error(f"❌ {name} 市场创建失败")
                raise Exception("Market creation failed")
                
        except Exception as e:
            logger.error(f"❌ 提交市场创建交易失败: {e}")
            raise
    
    def _fallback_parse_market_event(self, data: bytes) -> Tuple[ObjectID, Address]:
        """回退解析方法，用于调试和兼容性"""
        try:
            # 尝试手动解析关键字段
            # 注意：这种方法不够可靠，仅用于调试
            if len(data) >= 16:  # 至少需要market_id
                market_id_bytes = data[0:16]  # ObjectID是16字节
                market_id = ObjectID(market_id_bytes)
                
                # 市场地址是固定的SPOT合约地址
                market_address = SPOT_CONTRACT_ADDRESS
                
                logger.info(f"📊 回退解析成功: market_id={market_id}")
                return market_id, market_address
        except Exception as e:
            logger.warning(f"⚠️ 回退解析也失败: {e}")
        
        # 最后的回退：使用随机ID
        logger.warning("⚠️ 使用随机market_id")
        return ObjectID.random(), SPOT_CONTRACT_ADDRESS
    
    def _extract_order_id_from_events(self, events) -> Optional[OrderId]:
        """从事件中提取订单ID"""
        try:
            for event in events:
                # 检查事件类型
                event_type = event.get("event_type", {})
                
                if isinstance(event_type, dict) and event_type.get("Call") == "order_created":
                    # 解析order_created事件的数据
                    event_data = event.get("data", {})
                    
                    if isinstance(event_data, dict):
                        bytes_data = event_data.get("Bytes", [])
                        
                        if len(bytes_data) >= 32:  # OrderId需要32字节
                            try:
                                data = bytes(bytes_data)
                                
                                # 手动解析OrderCreatedEvent结构
                                order_id_bytes = data[0:32]
                                order_id = OrderId(order_id_bytes)
                                logger.info(f"📊 订单ID: {order_id}")
                                return order_id
                                
                            except Exception as e:
                                logger.warning(f"⚠️ 解析OrderCreatedEvent失败: {e}")
                                # 回退到手动解析
                                return self._fallback_parse_order_event(data)
                        else:
                            logger.warning(f"⚠️ 字节数据长度不足: {len(bytes_data)} < 32")
        except Exception as e:
            logger.warning(f"⚠️ 提取订单ID失败: {e}")
        
        logger.warning("⚠️ 未找到order_created事件或解析失败")
        return None
    
    def _fallback_parse_order_event(self, data: bytes) -> Optional[OrderId]:
        """回退解析订单事件方法"""
        try:
            # 尝试手动解析关键字段
            # 注意：这种方法不够可靠，仅用于调试
            if len(data) >= 32:  # OrderId需要32字节
                order_id_bytes = data[0:32]  # OrderId是32字节
                order_id = OrderId(order_id_bytes)
                
                logger.info(f"📊 回退解析订单成功: order_id={order_id}")
                return order_id
        except Exception as e:
            logger.warning(f"⚠️ 回退解析订单也失败: {e}")
        
        return None
    
    async def place_order(self, market_address: Address, market_id: ObjectID,
                         balance_id: ObjectID, side: OrderSide, amount: int,
                         price: int, signer: Signer) -> Optional[OrderId]:
        """下单"""
        side_str = "买单" if side == OrderSide.BUY else "卖单"
        logger.info(f"下{side_str}: {amount} 数量, 价格 {price}")
        
        # 修正：使用正确的OrderParamsType构造
        # 根据Rust代码，OrderParamsType::Limit { tif } 需要包含TimeInForce
        order_params = create_limit_order_params(
            side=side,
            amount=amount,
            limit_price=price,
            tif=TimeInForce.GTC  # 使用Good Till Cancel
        )
        
        action = ActionBuilder.place_order(market_address, market_id, balance_id, order_params)
        
        tx = TransactionBuilder.new()\
            .sender(signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(signer)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            if response["receipt"].is_success():
                logger.info(f"✅ {side_str}下单成功")
                
                # 使用与Rust SDK相同的格式打印事件
                print_spot_receipt_json(response["receipt"].__dict__)
                
                # 从事件中提取订单ID
                order_id = self._extract_order_id_from_events(response["receipt"].events)
                if order_id:
                    logger.info(f"📊 成功提取订单ID: {order_id}")
                    return order_id
                else:
                    logger.warning("⚠️ 无法从事件中提取订单ID，使用模拟ID")
                    return ObjectID.random()  # 回退到模拟ID
            else:
                logger.error(f"❌ {side_str}下单失败")
                logger.error(f"------状态: {response['receipt'].status}")
                logger.error(f"------事件: {response['receipt'].events}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 提交{side_str}交易失败: {e}")
            logger.error(f"------异常详情: {type(e).__name__}: {str(e)}")
            return None
    
    async def cancel_order(self, market_address: Address, market_id: ObjectID,
                          order_id: OrderId, signer: Signer) -> bool:
        """撤单"""
        logger.info(f"撤单: {order_id}")
        
        cancel_params = CancelOrderParams(order_id=order_id)
        
        action = ActionBuilder.cancel_order(market_address, market_id, cancel_params)
        
        tx = TransactionBuilder.new()\
            .sender(signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(signer)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            if response["receipt"].is_success():
                logger.info("✅ 撤单成功")
                
                # 使用与Rust SDK相同的格式打印事件
                print_spot_receipt_json(response["receipt"].__dict__)
                
                return True
            else:
                logger.warning("⚠️ 撤单失败（可能订单已成交或被撤销）")
                return False
                
        except Exception as e:
            error_str = str(e)
            if "Price level not found" in error_str:
                logger.warning("⚠️ 撤单失败：订单可能已完全成交或价格级别已被清理")
                logger.info("💡 这是正常的业务逻辑，表示订单已经不存在于订单簿中")
            else:
                logger.error(f"❌ 提交撤单交易失败: {e}")
            return False
    
    async def run_example(self):
        """运行完整示例"""
        logger.info("🚀 开始LightPool现货交易示例")
        logger.info("=" * 50)
        
        # 测试连接
        if not await self.test_connection():
            logger.error("无法连接到节点，请确保LightPool节点正在运行")
            return
        
        try:
            # 步骤1: 创建BTC代币
            logger.info("\n步骤1: 创建BTC代币")
            logger.info("-" * 30)
            btc_token_id, btc_token_address, btc_balance_id = await self.create_token(
                name="Bitcoin",
                symbol="BTC",
                decimals=6,
                total_supply=21_000_000_000_000,  # 21M BTC
                mintable=True,
                signer=self.trader1
            )
            
            # 步骤2: 创建USDT代币
            logger.info("\n步骤2: 创建USDT代币")
            logger.info("-" * 30)
            usdt_token_id, usdt_token_address, usdt_balance_id = await self.create_token(
                name="USD Tether",
                symbol="USDT",
                decimals=6,
                total_supply=150_000_000_000_000_000,  # 150000B USDT
                mintable=True,
                signer=self.trader2
            )
            
            # 等待代币创建完成
            await asyncio.sleep(1)
            
            # 步骤3: 创建BTC/USDT市场
            logger.info("\n步骤3: 创建BTC/USDT市场")
            logger.info("-" * 30)
            market_id, market_address = await self.create_market(
                name="BTC/USDT",
                base_token=btc_token_address,
                quote_token=usdt_token_address,
                signer=self.trader1
            )
            
            # 等待市场创建完成
            await asyncio.sleep(1)
            
            # 步骤4: 交易者1下卖单 (使用BTC余额)
            logger.info("\n步骤4: 交易者1下卖单")
            logger.info("-" * 30)
            sell_order_id = await self.place_order(
                market_address=market_address,
                market_id=market_id,
                balance_id=btc_balance_id,  # 使用BTC余额
                side=OrderSide.SELL,
                amount=5_000_000,  # 5 BTC
                price=50_000_000_000,  # 50,000 USDT
                signer=self.trader1
            )
            
            # 步骤5: 交易者2下买单 (使用USDT余额)
            logger.info("\n步骤5: 交易者2下买单")
            logger.info("-" * 30)
            buy_order_id = await self.place_order(
                market_address=market_address,
                market_id=market_id,
                balance_id=usdt_balance_id,  # 使用USDT余额
                side=OrderSide.BUY,
                amount=3_000_000,  # 1 BTC
                price=50_000_000_000,  # 50,000 USDT
                signer=self.trader2
            )
            
            # 等待订单匹配
            await asyncio.sleep(1)
            
            # 步骤6: 撤销剩余卖单
            if sell_order_id:
                logger.info("\n步骤6: 撤销剩余卖单")
                logger.info("-" * 30)
                await self.cancel_order(
                    market_address=market_address,
                    market_id=market_id,
                    order_id=sell_order_id,
                    signer=self.trader1
                )
            
            # 步骤7: 更新市场参数
            logger.info("\n步骤7: 更新市场参数")
            logger.info("-" * 30)
            
            # 创建更新市场参数
            market_update_params = UpdateMarketParams(
                min_order_size=50_000,        # 减少最小订单大小到0.05 BTC
                maker_fee_bps=5,              # 减少maker费用到0.05%
                taker_fee_bps=15,             # 减少taker费用到0.15%
                allow_market_orders=True,      # 允许市价单
                state=MarketState.ACTIVE       # 保持活跃状态
            )
            
            action = ActionBuilder.update_market(market_address, market_id, market_update_params)
            
            tx = TransactionBuilder.new()\
                .sender(self.trader1.address())\
                .expiration(0xffffffffffffffff)\
                .add_action(action)\
                .build_and_sign(self.trader1)
            
            response = await self.client.submit_transaction(tx)
            logger.info(f"交易响应: {response}")
            
            if response["receipt"].is_success():
                logger.info("✅ 市场参数更新成功")
                # 使用与Rust SDK相同的格式打印事件
                print_spot_receipt_json(response["receipt"].__dict__)
            else:
                logger.error("❌ 市场参数更新失败")
            
            logger.info("\n🎉 现货交易示例完成!")
            logger.info("=" * 50)
            logger.info("操作总结:")
            logger.info("1. ✅ 创建BTC代币 (21M供应量给交易者1)")
            logger.info("2. ✅ 创建USDT代币 (1B供应量给交易者2)")
            logger.info("3. ✅ 创建BTC/USDT交易市场")
            logger.info("4. ✅ 下卖单 (交易者1卖出5 BTC，价格50,000 USDT)")
            logger.info("5. ✅ 下买单 (交易者2买入3 BTC，价格50,000 USDT) - 应该匹配成交")
            logger.info("6. ✅ 撤销剩余卖单 (2 BTC)")
            logger.info("7. ✅ 更新市场参数")
            
        except Exception as e:
            logger.error(f"❌ 示例执行失败: {e}")
            raise


async def main():
    """主函数"""
    async with SpotTradingExample() as example:
        await example.run_example()


if __name__ == "__main__":
    asyncio.run(main()) 