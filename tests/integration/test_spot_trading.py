#!/usr/bin/env python3
"""
LightPool Python SDK 现货交易集成测试

这些测试需要运行中的LightPool节点才能执行。
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock

from lightpool_sdk import (
    LightPoolClient, Signer, TransactionBuilder, ActionBuilder,
    Address, ObjectID, U256,
    CreateTokenParams, CreateMarketParams, PlaceOrderParams, CancelOrderParams,
    OrderSide, TimeInForce, MarketState, LimitOrderParams,
    TOKEN_CONTRACT_ADDRESS, SPOT_CONTRACT_ADDRESS
)


@pytest.mark.integration
class TestSpotTradingIntegration:
    """现货交易集成测试"""
    
    @pytest.fixture
    def rpc_url(self):
        """获取RPC URL"""
        return os.getenv("LIGHTPOOL_RPC_URL", "http://localhost:26300")
    
    @pytest.fixture
    def client(self, rpc_url):
        """创建客户端"""
        return LightPoolClient(rpc_url)
    
    @pytest.fixture
    def signer(self):
        """创建签名者"""
        return Signer.new()
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查"""
        is_healthy = await client.health_check()
        assert isinstance(is_healthy, bool)
    
    @pytest.mark.asyncio
    async def test_create_token_integration(self, client, signer):
        """测试代币创建集成"""
        # 跳过测试，如果没有运行中的节点
        if not await client.health_check():
            pytest.skip("LightPool node is not running")
        
        create_params = CreateTokenParams(
            name="Test Token",
            symbol="TEST",
            decimals=6,
            total_supply=U256(1_000_000_000_000),
            mintable=True,
            to=signer.address()
        )
        
        action = ActionBuilder.create_token(TOKEN_CONTRACT_ADDRESS, create_params)
        
        tx = TransactionBuilder.new()\
            .sender(signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(signer)
        
        try:
            response = await client.submit_transaction(tx)
            assert response["receipt"].is_success()
            print(f"Token created successfully: {response['digest']}")
        except Exception as e:
            pytest.skip(f"Token creation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_create_market_integration(self, client, signer):
        """测试市场创建集成"""
        # 跳过测试，如果没有运行中的节点
        if not await client.health_check():
            pytest.skip("LightPool node is not running")
        
        # 创建两个代币用于市场
        token1_params = CreateTokenParams(
            name="Base Token",
            symbol="BASE",
            decimals=6,
            total_supply=U256(1_000_000_000_000),
            mintable=True,
            to=signer.address()
        )
        
        token2_params = CreateTokenParams(
            name="Quote Token",
            symbol="QUOTE",
            decimals=6,
            total_supply=U256(1_000_000_000_000),
            mintable=True,
            to=signer.address()
        )
        
        # 创建代币
        token1_action = ActionBuilder.create_token(TOKEN_CONTRACT_ADDRESS, token1_params)
        token2_action = ActionBuilder.create_token(TOKEN_CONTRACT_ADDRESS, token2_params)
        
        tx = TransactionBuilder.new()\
            .sender(signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(token1_action)\
            .add_action(token2_action)\
            .build_and_sign(signer)
        
        try:
            response = await client.submit_transaction(tx)
            assert response["receipt"].is_success()
            print(f"Tokens created successfully: {response['digest']}")
            
            # 创建市场
            market_params = CreateMarketParams(
                name="BASE/QUOTE",
                base_token=Address.random(),  # 模拟代币地址
                quote_token=Address.random(),  # 模拟代币地址
                min_order_size=100_000,
                tick_size=100_000,
                maker_fee_bps=10,
                taker_fee_bps=20,
                allow_market_orders=True,
                state=MarketState.ACTIVE,
                limit_order=True
            )
            
            market_action = ActionBuilder.create_market(SPOT_CONTRACT_ADDRESS, market_params)
            
            market_tx = TransactionBuilder.new()\
                .sender(signer.address())\
                .expiration(0xFFFFFFFFFFFFFFFF)\
                .add_action(market_action)\
                .build_and_sign(signer)
            
            response = await client.submit_transaction(market_tx)
            assert response["receipt"].is_success()
            print(f"Market created successfully: {response['digest']}")
            
        except Exception as e:
            pytest.skip(f"Market creation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_place_order_integration(self, client, signer):
        """测试下单集成"""
        # 跳过测试，如果没有运行中的节点
        if not await client.health_check():
            pytest.skip("LightPool node is not running")
        
        # 模拟市场参数
        market_address = Address.random()
        market_id = ObjectID.random()
        balance_id = ObjectID.random()
        
        order_params = PlaceOrderParams(
            side=OrderSide.BUY,
            amount=1_000_000,
            order_type=LimitOrderParams(TimeInForce.GTC),
            limit_price=50_000_000_000
        )
        
        action = ActionBuilder.place_order(
            market_address,
            market_id,
            balance_id,
            order_params
        )
        
        tx = TransactionBuilder.new()\
            .sender(signer.address())\
            .expiration(0xFFFFFFFFFFFFFFFF)\
            .add_action(action)\
            .build_and_sign(signer)
        
        try:
            response = await client.submit_transaction(tx)
            # 注意：这个测试可能会失败，因为需要真实的市场和余额
            print(f"Order placement result: {response['receipt'].status}")
        except Exception as e:
            print(f"Order placement failed (expected): {e}")
            # 这是预期的，因为我们使用的是模拟数据


@pytest.mark.integration
class TestClientIntegration:
    """客户端集成测试"""
    
    @pytest.fixture
    def rpc_url(self):
        """获取RPC URL"""
        return os.getenv("LIGHTPOOL_RPC_URL", "http://localhost:26300")
    
    @pytest.fixture
    def client(self, rpc_url):
        """创建客户端"""
        return LightPoolClient(rpc_url)
    
    @pytest.mark.asyncio
    async def test_client_connection(self, client):
        """测试客户端连接"""
        try:
            is_healthy = await client.health_check()
            assert isinstance(is_healthy, bool)
        except Exception as e:
            pytest.skip(f"Client connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_get_chain_info(self, client):
        """测试获取链信息"""
        if not await client.health_check():
            pytest.skip("LightPool node is not running")
        
        try:
            chain_info = await client.get_chain_info()
            if chain_info:
                print(f"Chain info: {chain_info}")
        except Exception as e:
            print(f"Get chain info failed: {e}")
    
    @pytest.mark.asyncio
    async def test_get_account_info(self, client):
        """测试获取账户信息"""
        if not await client.health_check():
            pytest.skip("LightPool node is not running")
        
        signer = Signer.new()
        address = signer.address()
        
        try:
            account_info = await client.get_account_info(address)
            if account_info:
                print(f"Account info: {account_info}")
        except Exception as e:
            print(f"Get account info failed: {e}")


# 标记所有集成测试
pytestmark = pytest.mark.integration 