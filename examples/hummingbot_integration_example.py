#!/usr/bin/env python3
"""
Hummingbot 集成示例

演示如何使用 LightPoolTradingClient 进行用户友好的交易操作，
无需预配置的映射文件，直接通过交易对名称进行下单。

这个示例模拟了 Hummingbot 用户的典型使用场景。
"""

import asyncio
import logging
import os
import sys
from decimal import Decimal

# 添加当前目录的上级目录到 Python 路径，确保使用正确的 lightpool_sdk
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lightpool_sdk import LightPoolTradingClient

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def hummingbot_trading_example():
    """模拟 Hummingbot 的交易场景"""

    # 配置参数
    RPC_URL = "http://localhost:26300"
    PRIVATE_KEY = "225e185208448ef8ee371bc0051523f6b5d10465c156e22de4cec959945af6c1"

    logger.info("🚀 启动 Hummingbot × LightPool 集成示例")
    logger.info("=" * 60)

    async with LightPoolTradingClient(RPC_URL, PRIVATE_KEY) as trading_client:

        # 1. 发现可用市场
        logger.info("📊 发现可用市场...")
        available_markets = await trading_client.list_available_markets()
        logger.info(f"发现 {len(available_markets)} 个市场: {available_markets}")

        if not available_markets:
            logger.warning("⚠️  没有发现可用市场，请确保 LightPool 网络中有创建的市场")
            return

        # 2. 选择交易对（模拟用户输入 "BTC/USDT"）
        trading_pair = "BTC/USDT"
        if trading_pair not in available_markets:
            # 如果 BTC/USDT 不存在，使用第一个可用市场
            trading_pair = available_markets[0]
            logger.info(f"使用第一个可用市场: {trading_pair}")

        # 3. 获取市场信息
        logger.info(f"\n📈 获取 {trading_pair} 市场信息...")
        market_summary = await trading_client.get_market_summary(trading_pair)
        if market_summary:
            logger.info("市场摘要:")
            for key, value in market_summary.items():
                logger.info(f"  {key}: {value}")

        # 4. 查询用户余额
        logger.info(f"\n💰 查询用户余额...")
        market_info = await trading_client.get_market_info(trading_pair)
        if market_info:
            base_symbol = market_info.base_symbol
            quote_symbol = market_info.quote_symbol

            base_balance = await trading_client.get_user_balance(base_symbol)
            quote_balance = await trading_client.get_user_balance(quote_symbol)

            if base_balance:
                logger.info(
                    f"  {base_symbol} 余额: {base_balance.amount / 1_000_000:.6f}"
                )
            else:
                logger.info(f"  {base_symbol} 余额: 0.000000 (未找到余额对象)")

            if quote_balance:
                logger.info(
                    f"  {quote_symbol} 余额: {quote_balance.amount / 1_000_000:.6f}"
                )
            else:
                logger.info(f"  {quote_symbol} 余额: 0.000000 (未找到余额对象)")

        # 5. 获取当前订单簿
        logger.info(f"\n📋 获取 {trading_pair} 订单簿...")
        order_book = await trading_client.get_order_book(trading_pair, depth=5)
        if order_book:
            logger.info("买单 (Bids):")
            for i, (price, amount) in enumerate(order_book.get("bids", [])[:3]):
                logger.info(
                    f"  {i+1}. 价格: {price/1_000_000:.6f}, 数量: {amount/1_000_000:.6f}"
                )

            logger.info("卖单 (Asks):")
            for i, (price, amount) in enumerate(order_book.get("asks", [])[:3]):
                logger.info(
                    f"  {i+1}. 价格: {price/1_000_000:.6f}, 数量: {amount/1_000_000:.6f}"
                )

        # 6. 模拟下单操作（Hummingbot 风格）
        logger.info(
            f"\n🛒 模拟下单: 买入 0.01 {trading_pair.split('/')[0]} @ 50000 {trading_pair.split('/')[1]}"
        )

        # 这就是 Hummingbot 用户需要的简单接口！
        buy_result = await trading_client.place_order(
            trading_pair=trading_pair,
            side="BUY",
            amount=Decimal("0.01"),  # 0.01 BTC
            price=Decimal("50000"),  # 50000 USDT
        )

        if buy_result.success:
            logger.info(f"✅ 买单下单成功!")
            logger.info(f"   交易哈希: {buy_result.transaction_hash}")
        else:
            logger.error(f"❌ 买单下单失败: {buy_result.error}")

        # 7. 模拟卖单
        logger.info(
            f"\n🛒 模拟下单: 卖出 0.005 {trading_pair.split('/')[0]} @ 55000 {trading_pair.split('/')[1]}"
        )

        sell_result = await trading_client.place_order(
            trading_pair=trading_pair,
            side="SELL",
            amount=Decimal("0.005"),  # 0.005 BTC
            price=Decimal("55000"),  # 55000 USDT
        )

        if sell_result.success:
            logger.info(f"✅ 卖单下单成功!")
            logger.info(f"   交易哈希: {sell_result.transaction_hash}")
        else:
            logger.error(f"❌ 卖单下单失败: {sell_result.error}")

        # 8. 查询用户订单
        logger.info(f"\n📜 查询用户在 {trading_pair} 的订单...")
        user_orders = await trading_client.get_user_orders(trading_pair)
        if user_orders:
            logger.info(f"找到 {len(user_orders)} 个订单:")
            for i, order in enumerate(user_orders[:5]):  # 显示前5个订单
                logger.info(f"  订单 {i+1}: {order}")
        else:
            logger.info("没有找到用户订单")

        # 9. 总结
        logger.info("\n🎉 Hummingbot × LightPool 集成示例完成!")
        logger.info("=" * 60)
        logger.info("集成优势:")
        logger.info("✅ 无需预配置映射文件")
        logger.info("✅ 直接使用交易对名称 (如 'BTC/USDT')")
        logger.info("✅ 自动发现市场和处理参数映射")
        logger.info("✅ 统一的下单接口，兼容 Hummingbot")
        logger.info("✅ 实时余额和订单簿查询")
        logger.info("✅ 完整的错误处理和用户反馈")


async def simple_trading_demo():
    """简化的交易演示，展示核心功能"""

    logger.info("\n🔥 简化交易演示")
    logger.info("-" * 40)

    # 这就是 Hummingbot 需要的简单集成！
    async with LightPoolTradingClient(
        rpc_url="http://localhost:26300",
        private_key_hex="225e185208448ef8ee371bc0051523f6b5d10465c156e22de4cec959945af6c1",
    ) as client:

        # 1. 列出市场
        markets = await client.list_available_markets()
        logger.info(f"可用市场: {markets}")

        if markets:
            trading_pair = markets[0]

            # 2. 下买单 - 就这么简单！
            result = await client.place_order(
                trading_pair=trading_pair,
                side="BUY",
                amount=Decimal("0.01"),
                price=Decimal("50000"),
            )

            logger.info(f"下单结果: {result.success}")
            if result.error:
                logger.error(f"错误: {result.error}")


async def main():
    """主函数"""
    try:
        # 运行完整示例
        await hummingbot_trading_example()

        # 运行简化演示
        await simple_trading_demo()

    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
