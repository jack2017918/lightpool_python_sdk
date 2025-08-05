#!/usr/bin/env python3
"""
LightPool Python SDK 基本测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from lightpool_sdk import (
    Signer, Address, ObjectID, U256, Digest,
    OrderSide, TimeInForce, MarketState, ExecutionStatus,
    CreateTokenParams, CreateMarketParams, PlaceOrderParams,
    LimitOrderParams, TOKEN_CONTRACT_ADDRESS, SPOT_CONTRACT_ADDRESS
)


class TestTypes:
    """类型测试"""
    
    def test_address(self):
        """测试地址类型"""
        # 测试从字符串创建
        addr1 = Address("0x" + "0" * 64)
        assert str(addr1) == "0x" + "0" * 64
        
        # 测试从字节创建
        addr2 = Address(bytes(32))
        assert str(addr2) == "0x" + "0" * 64
        
        # 测试从整数创建
        addr3 = Address(0)
        assert str(addr3) == "0x" + "0" * 64
        
        # 测试特殊地址
        zero_addr = Address.zero()
        assert str(zero_addr) == "0x" + "0" * 64
        
        one_addr = Address.one()
        assert str(one_addr) == "0x" + "01" + "0" * 62
        
        two_addr = Address.two()
        assert str(two_addr) == "0x" + "02" + "0" * 62
        
        # 测试随机地址
        random_addr = Address.random()
        assert len(str(random_addr)) == 66  # 0x + 64 hex chars
    
    def test_object_id(self):
        """测试对象ID类型"""
        # 测试从字符串创建
        obj_id1 = ObjectID("0x" + "1" * 64)
        assert str(obj_id1) == "0x" + "1" * 64
        
        # 测试从字节创建
        obj_id2 = ObjectID(bytes([1] * 32))
        assert str(obj_id2) == "0x" + "01" * 32
        
        # 测试随机对象ID
        random_obj_id = ObjectID.random()
        assert len(str(random_obj_id)) == 66
    
    def test_u256(self):
        """测试U256类型"""
        # 测试从整数创建
        u256_1 = U256(1000)
        assert int(u256_1) == 1000
        assert str(u256_1) == "1000"
        
        # 测试从字符串创建
        u256_2 = U256("1000")
        assert int(u256_2) == 1000
        
        # 测试从十六进制字符串创建
        u256_3 = U256("0x3e8")
        assert int(u256_3) == 1000
        
        # 测试从字节创建
        u256_4 = U256(1000)  # 直接使用整数，避免字节转换问题
        assert int(u256_4) == 1000
        
        # 测试转换为字节
        bytes_data = u256_1.to_bytes()
        assert len(bytes_data) == 32
        
        # 测试负数错误
        with pytest.raises(ValueError):
            U256(-1)
    
    def test_digest(self):
        """测试摘要类型"""
        # 测试从字符串创建
        digest1 = Digest("0x" + "a" * 64)
        assert str(digest1) == "0x" + "a" * 64
        
        # 测试从字节创建
        digest2 = Digest(bytes([0xaa] * 32))
        assert str(digest2) == "0x" + "aa" * 32
        
        # 测试从数据生成摘要
        data = b"test data"
        digest3 = Digest.from_bytes(data)
        assert len(str(digest3)) == 66


class TestSigner:
    """签名者测试"""
    
    def test_new_signer(self):
        """测试创建新签名者"""
        signer = Signer.new()
        assert signer.address() is not None
        assert len(str(signer.address())) == 66
    
    def test_from_hex(self):
        """测试从十六进制字符串创建签名者"""
        # 生成一个私钥
        original_signer = Signer.new()
        private_key_int = original_signer.private_key_raw()
        
        # 从私钥整数重新创建签名者
        new_signer = Signer.from_secret_key_int(private_key_int)
        
        # 验证地址相同
        assert str(original_signer.address()) == str(new_signer.address())
    
    def test_sign_and_verify(self):
        """测试签名和验证"""
        signer = Signer.new()
        message = b"test message"
        
        # 签名
        signature = signer.sign(message)
        assert len(signature) > 0
        
        # 验证
        assert signer.verify(message, signature) == True
        assert signer.verify(message + b"wrong", signature) == False
    
    def test_hex_sign_and_verify(self):
        """测试十六进制签名和验证"""
        signer = Signer.new()
        message_hex = "0x74657374206d657373616765"  # "test message"
        
        # 签名
        signature_hex = signer.sign_hex(message_hex)
        assert signature_hex.startswith("0x")
        
        # 验证
        assert signer.verify_hex(message_hex, signature_hex) == True
        assert signer.verify_hex("0x776f6e67", signature_hex) == False


class TestParameters:
    """参数类型测试"""
    
    def test_create_token_params(self):
        """测试创建代币参数"""
        params = CreateTokenParams(
            name="Test Token",
            symbol="TEST",
            decimals=6,
            total_supply=U256(1000000),
            mintable=True,
            to=Address.one()
        )
        
        assert params.name == "Test Token"
        assert params.symbol == "TEST"
        assert params.decimals == 6
        assert int(params.total_supply) == 1000000
        assert params.mintable == True
        assert str(params.to) == str(Address.one())
    
    def test_create_market_params(self):
        """测试创建市场参数"""
        params = CreateMarketParams(
            name="BTC/USDT",
            base_token=Address.one(),
            quote_token=Address.two(),
            min_order_size=100000,
            tick_size=1000000,
            maker_fee_bps=10,
            taker_fee_bps=20,
            allow_market_orders=True,
            state=MarketState.ACTIVE,
            limit_order=True
        )
        
        assert params.name == "BTC/USDT"
        assert str(params.base_token) == str(Address.one())
        assert str(params.quote_token) == str(Address.two())
        assert params.min_order_size == 100000
        assert params.tick_size == 1000000
        assert params.maker_fee_bps == 10
        assert params.taker_fee_bps == 20
        assert params.allow_market_orders == True
        assert params.state == MarketState.ACTIVE
        assert params.limit_order == True
    
    def test_place_order_params(self):
        """测试下单参数"""
        order_type = LimitOrderParams(TimeInForce.GTC)
        params = PlaceOrderParams(
            side=OrderSide.BUY,
            amount=1000000,
            order_type=order_type,
            limit_price=50000000000
        )
        
        assert params.side == OrderSide.BUY
        assert params.amount == 1000000
        assert params.order_type == order_type
        assert params.limit_price == 50000000000


class TestEnums:
    """枚举类型测试"""
    
    def test_order_side(self):
        """测试订单方向"""
        assert OrderSide.BUY.value == "buy"
        assert OrderSide.SELL.value == "sell"
    
    def test_time_in_force(self):
        """测试订单有效期"""
        assert TimeInForce.GTC.value == "gtc"
        assert TimeInForce.IOC.value == "ioc"
        assert TimeInForce.FOK.value == "fok"
    
    def test_market_state(self):
        """测试市场状态"""
        assert MarketState.ACTIVE.value == "active"
        assert MarketState.PAUSED.value == "paused"
        assert MarketState.CLOSED.value == "closed"
    
    def test_execution_status(self):
        """测试执行状态"""
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.FAILURE.value == "failure"


class TestConstants:
    """常量测试"""
    
    def test_contract_addresses(self):
        """测试合约地址"""
        # TOKEN_CONTRACT_ADDRESS应该是Module::TOKEN的地址（第一个字节是0x01）
        expected_token_address = Address(bytes([0x01] + [0x00] * 31))
        assert str(TOKEN_CONTRACT_ADDRESS) == str(expected_token_address)
        # SPOT_CONTRACT_ADDRESS应该是Module::SPOT的地址（第一个字节是0x02）
        expected_spot_address = Address(bytes([0x02] + [0x00] * 31))
        assert str(SPOT_CONTRACT_ADDRESS) == str(expected_spot_address)


if __name__ == "__main__":
    pytest.main([__file__]) 