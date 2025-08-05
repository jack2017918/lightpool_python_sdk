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
    
    async def create_tokens_batch(self, num_tokens: int) -> List[Tuple[ObjectID, Address, ObjectID]]:
        """批量创建代币"""
        logger.info(f"批量创建 {num_tokens} 个代币...")
        
        tokens = []
        for i in range(num_tokens):
            name = f"Token{i+1}"
            symbol = f"TKN{i+1}"
            
            create_params = CreateTokenParams(
                name=name,
                symbol=symbol,
                decimals=6,
                total_supply=U256(1_000_000_000_000),  # 1B tokens
                mintable=True,
                to=self.trader.address()
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
                    # 模拟代币信息
                    token_id = ObjectID.random()
                    token_address = Address.random()
                    balance_id = ObjectID.random()
                    
                    tokens.append((token_id, token_address, balance_id))
                    logger.info(f"✅ 创建代币 {symbol}")
                else:
                    logger.error(f"❌ 创建代币 {symbol} 失败")
                    
            except Exception as e:
                logger.error(f"❌ 提交代币 {symbol} 创建交易失败: {e}")
        
        logger.info(f"✅ 成功创建 {len(tokens)} 个代币")
        return tokens
    
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
            
            market_params = CreateMarketParams(
                name=f"Market{i+1}",
                base_token=base_token_address,
                quote_token=quote_token_address,
                min_order_size=100_000,  # 0.1 最小订单
                tick_size=100_000,       # 0.1 价格精度
                maker_fee_bps=10,        # 0.1% maker费用
                taker_fee_bps=20,        # 0.2% taker费用
                allow_market_orders=True,
                state=MarketState.ACTIVE,
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
                    # 模拟市场信息
                    market_id = ObjectID.random()
                    market_address = Address.random()
                    base_price = 10_000_000 + (i * 1_000_000)  # 10-110 基础价格
                    tick_size = 100_000
                    
                    market_info = MarketInfo(
                        market_id=market_id,
                        market_address=market_address,
                        base_token=base_token_address,
                        quote_token=quote_token_address,
                        base_balance_id=base_balance_id,
                        quote_balance_id=quote_balance_id,
                        base_price=base_price,
                        tick_size=tick_size,
                        current_price=base_price
                    )
                    
                    markets.append(market_info)
                    logger.info(f"✅ 创建市场 Market{i+1}")
                else:
                    logger.error(f"❌ 创建市场 Market{i+1} 失败")
                    
            except Exception as e:
                logger.error(f"❌ 提交市场 Market{i+1} 创建交易失败: {e}")
        
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
                side=side,
                amount=amount,
                order_type=LimitOrderParams(TimeInForce.GTC),
                limit_price=price
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