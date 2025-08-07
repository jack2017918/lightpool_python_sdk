#!/usr/bin/env python3
"""
LightPool 高频现货交易示例

这个示例演示了如何使用LightPool Python SDK进行高频现货交易：
1. 批量创建代币和市场
2. 高频下单
3. 性能测试
"""

import asyncio
import logging
import time
import random
import secrets
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from lightpool_sdk import (
    LightPoolClient, Signer, TransactionBuilder, ActionBuilder,
    Address, ObjectID, U256,
    CreateTokenParams, CreateMarketParams, PlaceOrderParams,
    OrderSide, TimeInForce, MarketState, LimitOrderParams,
    TOKEN_CONTRACT_ADDRESS, SPOT_CONTRACT_ADDRESS
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MarketInfo:
    """市场信息"""
    market_id: ObjectID
    market_address: Address
    base_token: Address
    quote_token: Address
    base_balance_id: ObjectID
    quote_balance_id: ObjectID
    base_price: int
    tick_size: int
    bid_levels_used: int = 0
    ask_levels_used: int = 0
    max_levels: int = 20
    current_price: int = 0
    direction: bool = True  # True = 上涨, False = 下跌


class BurstSpotTradingExample:
    """高频现货交易示例类"""
    
    def __init__(self, rpc_url: str = "http://localhost:26300"):
        self.rpc_url = rpc_url
        self.client: Optional[LightPoolClient] = None
        
        # 创建交易者
        self.trader = Signer.new()
        logger.info(f"交易者地址: {self.trader.address()}")
        
        # 市场信息
        self.markets: List[MarketInfo] = []
        self.tokens: List[Tuple[ObjectID, Address, ObjectID]] = []
    
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
    
    async def create_token(self, name: str, symbol: str, total_supply: int) -> Tuple[ObjectID, Address, ObjectID]:
        """创建单个代币"""
        logger.info(f"创建代币: {name} ({symbol})")
        
        create_params = CreateTokenParams(
            name=name,
            symbol=symbol,
            total_supply=total_supply,
            mintable=True,
            to=self.trader.address().to_bytes()  # 使用用户地址作为余额对象的所有者
        )
        
        action = ActionBuilder.create_token(TOKEN_CONTRACT_ADDRESS, create_params)
        
        tx = TransactionBuilder.new()\
            .sender(self.trader.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(self.trader)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            if response["receipt"].is_success():
                logger.info(f"✅ {symbol} 代币创建成功")
                
                # 从事件中提取代币信息
                events = response["receipt"].events
                for event in events:
                    if event.get("event_type", {}).get("Call") == "token_created":
                        # 解析token_created事件的数据 (bincode序列化的TokenCreatedEvent)
                        event_data = event.get("data", {}).get("Bytes", [])

                        if len(event_data) >= 100:  # 降低要求，先看看能否解析
                            try:
                                import struct
                                data = bytes(event_data)
                                
                                # 简化解析：直接提取关键字段
                                # token_id: ObjectID (前16字节)
                                token_id_bytes = data[0:16]
                                token_id = ObjectID(token_id_bytes.hex())
                                
                                # balance_id: ObjectID (最后16字节)
                                balance_id_bytes = data[-16:]
                                balance_id = ObjectID(balance_id_bytes.hex())
                                
                                # token地址就是合约地址
                                token_address = TOKEN_CONTRACT_ADDRESS
                                
                                logger.info(f"📊 提取的对象ID: token_id={token_id}, balance_id={balance_id}")
                                return token_id, token_address, balance_id
                            except Exception as e:
                                logger.warning(f"⚠️ 解析TokenCreatedEvent失败: {e}")
                                break
                
                # 如果无法解析事件，回退到模拟
                logger.warning("⚠️ 无法解析代币创建事件，使用模拟ID")
                token_id = ObjectID(secrets.token_hex(16))
                token_address = Address(secrets.token_hex(32))
                balance_id = ObjectID(secrets.token_hex(16))
                
                return token_id, token_address, balance_id
            else:
                logger.error(f"❌ {symbol} 代币创建失败")
                raise Exception("Token creation failed")
                
        except Exception as e:
            logger.error(f"❌ 提交代币创建交易失败: {e}")
            raise
    
    async def create_tokens_batch(self, num_tokens: int) -> List[Tuple[ObjectID, Address, ObjectID]]:
        """批量创建代币"""
        logger.info(f"批量创建 {num_tokens} 个代币...")
        
        tokens = []
        for i in range(num_tokens):
            name = f"Token{i+1}"
            symbol = f"TKN{i+1}"
            total_supply = 1_000_000_000_000  # 1B tokens
            
            try:
                token_id, token_address, balance_id = await self.create_token(name, symbol, total_supply)
                tokens.append((token_id, token_address, balance_id))
                logger.info(f"✅ 创建代币 {symbol}")
                
                # 等待一下避免过快提交
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ 创建代币 {symbol} 失败: {e}")
        
        logger.info(f"✅ 成功创建 {len(tokens)} 个代币")
        return tokens
    
    async def create_market(self, name: str, base_token: Address, quote_token: Address) -> MarketInfo:
        """创建单个市场"""
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
            .sender(self.trader.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(self.trader)
        
        try:
            response = await self.client.submit_transaction(tx)
            
            if response["receipt"].is_success():
                logger.info(f"✅ {name} 市场创建成功")
                
                # 从事件中提取市场信息
                events = response["receipt"].events
                for event in events:
                    if event.get("event_type", {}).get("Call") == "market_created":
                        # 解析market_created事件的数据 (bincode序列化的MarketCreatedEvent)
                        event_data = event.get("data", {}).get("Bytes", [])

                        if len(event_data) >= 100:  # 降低要求，先看看能否解析
                            try:
                                import struct
                                data = bytes(event_data)
                                
                                # 简化解析：直接提取关键字段
                                # market_id: ObjectID (前16字节)
                                market_id_bytes = data[0:16]
                                market_id = ObjectID(market_id_bytes.hex())
                                
                                # 临时解决方案：使用已知的模式
                                # 根据Rust端的逻辑，余额对象ID应该是连续的序列号
                                market_id_value = int.from_bytes(market_id_bytes, byteorder='little')
                                base_balance_id = ObjectID.from_u128(market_id_value + 5)  # 跳过更多中间对象
                                quote_balance_id = ObjectID.from_u128(market_id_value + 6)  # 再跳过更多中间对象
                                
                                logger.info(f"📊 市场余额对象: base_balance_id={base_balance_id}, quote_balance_id={quote_balance_id}")
                                
                                # 生成市场地址
                                market_address = Address(secrets.token_hex(32))
                                
                                # 设置基础价格和价格精度
                                base_price = 10_000_000 + (len(self.markets) * 1_000_000)  # 10-110 基础价格
                                tick_size = 1_000_000
                                
                                market_info = MarketInfo(
                                    market_id=market_id,
                                    market_address=market_address,
                                    base_token=base_token,
                                    quote_token=quote_token,
                                    base_balance_id=base_balance_id,
                                    quote_balance_id=quote_balance_id,
                                    base_price=base_price,
                                    tick_size=tick_size,
                                    current_price=base_price
                                )
                                
                                logger.info(f"📊 市场创建完成, market_id: {market_id}, market_address: {market_address}, base_balance_id: {base_balance_id}, quote_balance_id: {quote_balance_id}")
                                return market_info
                                
                            except Exception as e:
                                logger.warning(f"⚠️ 解析MarketCreatedEvent失败: {e}")
                                break
                
                # 如果无法解析事件，回退到模拟
                logger.warning("⚠️ 无法解析市场创建事件，使用模拟ID")
                market_id = ObjectID(secrets.token_hex(16))
                market_address = Address(secrets.token_hex(32))
                base_balance_id = ObjectID(secrets.token_hex(16))
                quote_balance_id = ObjectID(secrets.token_hex(16))
                
                # 设置基础价格和价格精度
                base_price = 10_000_000 + (len(self.markets) * 1_000_000)  # 10-110 基础价格
                tick_size = 1_000_000
                
                market_info = MarketInfo(
                    market_id=market_id,
                    market_address=market_address,
                    base_token=base_token,
                    quote_token=quote_token,
                    base_balance_id=base_balance_id,
                    quote_balance_id=quote_balance_id,
                    base_price=base_price,
                    tick_size=tick_size,
                    current_price=base_price
                )
                
                return market_info
            else:
                logger.error(f"❌ {name} 市场创建失败")
                raise Exception("Market creation failed")
                
        except Exception as e:
            logger.error(f"❌ 提交市场创建交易失败: {e}")
            raise
    
    async def create_markets_batch(self, num_markets: int) -> List[MarketInfo]:
        """批量创建市场"""
        logger.info(f"批量创建 {num_markets} 个市场...")
        
        if len(self.tokens) < num_markets * 2:
            raise ValueError(f"需要 {num_markets * 2} 个代币来创建 {num_markets} 个市场")
        
        markets = []
        for i in range(num_markets):
            # 选择两个不同的代币
            token1_idx = i * 2
            token2_idx = i * 2 + 1
            
            base_token_id, base_token_address, base_balance_id = self.tokens[token1_idx]
            quote_token_id, quote_token_address, quote_balance_id = self.tokens[token2_idx]
            
            try:
                market_info = await self.create_market(
                    name=f"Market{i+1}",
                    base_token=base_token_address,
                    quote_token=quote_token_address
                )
                markets.append(market_info)
                logger.info(f"✅ 创建市场 Market{i+1}")
                
                # 等待一下避免过快提交
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ 创建市场 Market{i+1} 失败: {e}")
        
        logger.info(f"✅ 成功创建 {len(markets)} 个市场")
        return markets
    
    def get_next_bid_price(self, market: MarketInfo) -> Optional[int]:
        """获取下一个买单价格"""
        if market.bid_levels_used >= market.max_levels:
            return None
        
        price = market.base_price - (market.bid_levels_used * market.tick_size)
        if price > 0:
            market.bid_levels_used += 1
            return price
        return None
    
    def get_next_ask_price(self, market: MarketInfo) -> Optional[int]:
        """获取下一个卖单价格"""
        if market.ask_levels_used >= market.max_levels:
            return None
        
        price = market.base_price + (market.ask_levels_used * market.tick_size)
        market.ask_levels_used += 1
        return price
    
    def get_matching_price(self, market: MarketInfo) -> int:
        """获取匹配价格（用于方向性移动）"""
        if market.direction:
            # 上涨：在当前价格基础上加价
            price = market.current_price + market.tick_size
            market.current_price = price
            
            # 检查是否达到最高价
            max_price = market.base_price + (market.max_levels * market.tick_size)
            if price >= max_price:
                market.direction = False
                market.current_price = max_price
            
            return price
        else:
            # 下跌：在当前价格基础上降价
            price = market.current_price - market.tick_size
            market.current_price = price
            
            # 检查是否达到最低价
            min_price = market.base_price - (market.max_levels * market.tick_size)
            if price <= min_price:
                market.direction = True
                market.current_price = min_price
            
            return price
    
    async def place_order_async(self, market: MarketInfo, side: OrderSide, 
                               amount: int, price: int) -> bool:
        """异步下单"""
        try:
            # 选择余额ID
            balance_id = market.base_balance_id if side == OrderSide.SELL else market.quote_balance_id
            
            order_params = PlaceOrderParams(
                side=side.to_rust_index(),
                amount=amount,
                order_type=0,  # OrderParamsType::Limit = 0
                limit_price=price,
                tif=0  # TimeInForce::GTC = 0
            )
            
            action = ActionBuilder.place_order(
                market.market_address, 
                market.market_id, 
                balance_id, 
                order_params
            )
            
            tx = TransactionBuilder.new()\
                .sender(self.trader.address())\
                .expiration(0xFFFFFFFFFFFFFFFF)\
                .add_action(action)\
                .build_and_sign(self.trader)
            
            response = await self.client.submit_transaction(tx)
            return response["receipt"].is_success()
            
        except Exception as e:
            logger.debug(f"下单失败: {e}")
            return False
    
    async def burst_trading_task(self, task_id: int, markets: List[MarketInfo], 
                                orders_per_second: int, duration_seconds: int,
                                order_amount: int) -> Dict[str, Any]:
        """高频交易任务"""
        logger.info(f"任务 {task_id} 开始: {orders_per_second} 订单/秒, 持续 {duration_seconds} 秒")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        order_count = 0
        success_count = 0
        
        # 计算订单间隔
        interval = 1.0 / orders_per_second if orders_per_second > 0 else 0.1
        
        while time.time() < end_time:
            # 随机选择市场
            market = random.choice(markets)
            
            # 确定订单方向和价格
            if market.bid_levels_used < market.max_levels:
                # 填充买单
                price = self.get_next_bid_price(market)
                side = OrderSide.BUY
            elif market.ask_levels_used < market.max_levels:
                # 填充卖单
                price = self.get_next_ask_price(market)
                side = OrderSide.SELL
            else:
                # 市场已满，使用方向性移动
                price = self.get_matching_price(market)
                side = OrderSide.BUY if market.direction else OrderSide.SELL
            
            if price is not None:
                # 下单
                success = await self.place_order_async(market, side, order_amount, price)
                order_count += 1
                if success:
                    success_count += 1
            
            # 等待间隔
            await asyncio.sleep(interval)
        
        task_duration = time.time() - start_time
        actual_rate = order_count / task_duration if task_duration > 0 else 0
        
        logger.info(f"任务 {task_id} 完成: {order_count} 订单, {success_count} 成功, "
                   f"实际速率 {actual_rate:.1f} 订单/秒")
        
        return {
            "task_id": task_id,
            "order_count": order_count,
            "success_count": success_count,
            "duration": task_duration,
            "actual_rate": actual_rate
        }
    
    async def run_burst_example(self, num_markets: int = 10, num_tasks: int = 5,
                               orders_per_second: int = 100, duration_seconds: int = 30,
                               order_amount: int = 1_000_000):
        """运行高频交易示例"""
        logger.info("🚀 开始LightPool高频现货交易示例")
        logger.info("=" * 60)
        logger.info(f"配置: {num_markets} 市场, {num_tasks} 任务, "
                   f"{orders_per_second} 订单/秒/任务, {duration_seconds} 秒")
        
        # 测试连接
        if not await self.test_connection():
            logger.error("无法连接到节点，请确保LightPool节点正在运行")
            return
        
        try:
            # 步骤1: 批量创建代币
            logger.info("\n步骤1: 批量创建代币")
            logger.info("-" * 40)
            self.tokens = await self.create_tokens_batch(num_markets * 2)
            
            # 等待代币创建完成
            await asyncio.sleep(2)
            
            # 步骤2: 批量创建市场
            logger.info("\n步骤2: 批量创建市场")
            logger.info("-" * 40)
            self.markets = await self.create_markets_batch(num_markets)
            
            # 等待市场创建完成
            await asyncio.sleep(2)
            
            # 步骤3: 开始高频交易
            logger.info("\n步骤3: 开始高频交易")
            logger.info("-" * 40)
            
            start_time = time.time()
            
            # 创建任务
            tasks = []
            for task_id in range(num_tasks):
                task = self.burst_trading_task(
                    task_id=task_id,
                    markets=self.markets,
                    orders_per_second=orders_per_second,
                    duration_seconds=duration_seconds,
                    order_amount=order_amount
                )
                tasks.append(task)
            
            # 并发执行任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # 统计结果
            total_orders = 0
            total_success = 0
            actual_rates = []
            
            for result in results:
                if isinstance(result, dict):
                    total_orders += result["order_count"]
                    total_success += result["success_count"]
                    actual_rates.append(result["actual_rate"])
                else:
                    logger.error(f"任务执行失败: {result}")
            
            avg_rate = sum(actual_rates) / len(actual_rates) if actual_rates else 0
            total_rate = total_orders / total_duration if total_duration > 0 else 0
            
            # 输出结果
            logger.info("\n🎉 高频交易示例完成!")
            logger.info("=" * 60)
            logger.info("性能统计:")
            logger.info(f"总订单数: {total_orders}")
            logger.info(f"成功订单数: {total_success}")
            logger.info(f"成功率: {total_success/total_orders*100:.1f}%" if total_orders > 0 else "0%")
            logger.info(f"总执行时间: {total_duration:.2f} 秒")
            logger.info(f"平均每任务速率: {avg_rate:.1f} 订单/秒")
            logger.info(f"总速率: {total_rate:.1f} 订单/秒")
            logger.info(f"预期速率: {num_tasks * orders_per_second} 订单/秒")
            logger.info(f"性能达成率: {total_rate/(num_tasks * orders_per_second)*100:.1f}%" if num_tasks * orders_per_second > 0 else "0%")
            
        except Exception as e:
            logger.error(f"❌ 示例执行失败: {e}")
            raise


async def main():
    """主函数"""
    # 配置参数
    config = {
        "num_markets": 5,      # 市场数量
        "num_tasks": 3,        # 并发任务数
        "orders_per_second": 50,  # 每任务每秒订单数
        "duration_seconds": 10,   # 持续时间
        "order_amount": 1_000_000  # 订单数量
    }
    
    async with BurstSpotTradingExample() as example:
        await example.run_burst_example(**config)


if __name__ == "__main__":
    asyncio.run(main()) 