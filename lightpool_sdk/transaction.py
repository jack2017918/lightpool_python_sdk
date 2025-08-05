"""
LightPool SDK 交易构建模块
"""

import hashlib
import json
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, asdict
import attrs2bin

from .types import (
    Address, ObjectID, U256, Digest,
    OrderSide, TimeInForce, OrderParamsType, MarketState,
    CreateTokenParams, TransferParams, MintParams, SplitParams, MergeParams,
    CreateMarketParams, UpdateMarketParams, PlaceOrderParams, CancelOrderParams,
    LimitOrderParams, MarketOrderParams
)
from .crypto import Signer
from .exceptions import ValidationError, TransactionError


@dataclass
class Action:
    """交易操作"""
    action_type: str
    params: bytes  # 改为字节数组，与Rust版本一致
    input_objects: List[ObjectID]
    target_address: Address
    module_address: Address


class ActionBuilder:
    """操作构建器"""
    
    @staticmethod
    def create_token(contract_address: Address, params: CreateTokenParams) -> Action:
        """创建代币操作"""
        # 使用bincode兼容的序列化，与Rust SDK保持一致
        params_bytes = attrs2bin.serialize(params)
        
        return Action(
            action_type="create",
            params=params_bytes,
            input_objects=[],
            target_address=contract_address,
            module_address=contract_address
        )
    
    @staticmethod
    def transfer_token(token_address: Address, balance_id: ObjectID, params: TransferParams) -> Action:
        """转账操作"""
        import json
        params_dict = asdict(params)
        # 将Address对象转换为字符串
        for key, value in params_dict.items():
            if hasattr(value, '__str__'):
                params_dict[key] = str(value)
        params_json = json.dumps(params_dict, separators=(',', ':'))
        params_bytes = params_json.encode('utf-8')
        
        return Action(
            action_type="transfer",
            params=params_bytes,
            input_objects=[balance_id],
            target_address=token_address,
            module_address=token_address
        )
    
    @staticmethod
    def mint_token(token_address: Address, token_id: ObjectID, params: MintParams) -> Action:
        """铸造代币操作"""
        import json
        params_dict = asdict(params)
        # 将Address对象转换为字符串
        for key, value in params_dict.items():
            if hasattr(value, '__str__'):
                params_dict[key] = str(value)
        params_json = json.dumps(params_dict, separators=(',', ':'))
        params_bytes = params_json.encode('utf-8')
        
        return Action(
            action_type="mint",
            params=params_bytes,
            input_objects=[token_id],
            target_address=token_address,
            module_address=token_address
        )
    
    @staticmethod
    def split_token(token_address: Address, balance_id: ObjectID, params: SplitParams) -> Action:
        """分割代币操作"""
        import json
        params_dict = asdict(params)
        # 将Address对象转换为字符串
        for key, value in params_dict.items():
            if hasattr(value, '__str__'):
                params_dict[key] = str(value)
        params_json = json.dumps(params_dict, separators=(',', ':'))
        params_bytes = params_json.encode('utf-8')
        
        return Action(
            action_type="split",
            params=params_bytes,
            input_objects=[balance_id],
            target_address=token_address,
            module_address=token_address
        )
    
    @staticmethod
    def merge_token(token_address: Address, main_balance_id: ObjectID, params: MergeParams) -> Action:
        """合并代币操作"""
        import json
        params_dict = asdict(params)
        # 将Address对象转换为字符串
        for key, value in params_dict.items():
            if hasattr(value, '__str__'):
                params_dict[key] = str(value)
        params_json = json.dumps(params_dict, separators=(',', ':'))
        params_bytes = params_json.encode('utf-8')
        
        return Action(
            action_type="merge",
            params=params_bytes,
            input_objects=[main_balance_id] + params.other_balance_ids,
            target_address=token_address,
            module_address=token_address
        )
    
    @staticmethod
    def create_market(contract_address: Address, params: CreateMarketParams) -> Action:
        """创建市场操作"""
        # 手动实现bincode兼容的序列化
        import struct
        
        # 序列化字符串 (长度 + 内容)
        name_bytes = params.name.encode('utf-8')
        name_data = struct.pack('<Q', len(name_bytes)) + name_bytes
        
        # 序列化地址 (32字节)
        base_token_data = params.base_token
        quote_token_data = params.quote_token
        
        # 序列化整数
        min_order_size_data = struct.pack('<Q', params.min_order_size)  # u64
        tick_size_data = struct.pack('<Q', params.tick_size)  # u64
        maker_fee_bps_data = struct.pack('<H', params.maker_fee_bps)  # u16
        taker_fee_bps_data = struct.pack('<H', params.taker_fee_bps)  # u16
        
        # 序列化布尔值
        allow_market_orders_data = struct.pack('<?', params.allow_market_orders)
        
        # 序列化枚举 (u32)
        state_data = struct.pack('<I', params.state)
        
        # 序列化布尔值
        limit_order_data = struct.pack('<?', params.limit_order)
        
        # 组合所有数据
        params_bytes = (name_data + base_token_data + quote_token_data + 
                       min_order_size_data + tick_size_data + 
                       maker_fee_bps_data + taker_fee_bps_data + 
                       allow_market_orders_data + state_data + limit_order_data)
        
        return Action(
            action_type="mkt_create",
            params=params_bytes,
            input_objects=[],
            target_address=contract_address,
            module_address=contract_address
        )
    
    @staticmethod
    def update_market(market_address: Address, market_id: ObjectID, params: UpdateMarketParams) -> Action:
        """更新市场操作"""
        return Action(
            action_type="update_market",
            params=asdict(params),
            input_objects=[market_id],
            target_address=market_address,
            module_address=market_address
        )
    
    @staticmethod
    def place_order(market_address: Address, market_id: ObjectID, balance_id: ObjectID, params: PlaceOrderParams) -> Action:
        """下单操作"""
        # 手动实现bincode兼容的序列化
        import struct
        
        # 序列化PlaceOrderParams结构
        # side: OrderSide (enum, u32 in bincode)
        # amount: u64
        # order_type: OrderParamsType (complex enum with data)
        # limit_price: u64
        
        # 序列化OrderParamsType::Limit { tif }
        # 枚举变体索引 0 + TimeInForce枚举值
        order_type_data = (
            struct.pack('<I', 0) +  # Limit variant = 0
            struct.pack('<I', 0)    # TimeInForce::GTC = 0
        )
        
        params_data = (
            struct.pack('<I', params.side) +  # side as u32 (OrderSide enum)
            struct.pack('<Q', params.amount) +  # amount as u64
            order_type_data +  # order_type as OrderParamsType::Limit
            struct.pack('<Q', params.limit_price)  # limit_price as u64
        )
        

        return Action(
            action_type="ord_place",  # 修正action名称
            params=params_data,
            input_objects=[market_id, balance_id],
            target_address=market_address,
            module_address=market_address
        )
    
    @staticmethod
    def cancel_order(market_address: Address, market_id: ObjectID, params: CancelOrderParams) -> Action:
        """撤单操作"""
        # 手动实现bincode兼容的序列化
        # CancelOrderParams只包含order_id (OrderId类型，在Rust中是32字节)
        params_data = params.order_id  # order_id as bytes (32 bytes)
        
        return Action(
            action_type="ord_cancel",  # 修正action名称
            params=params_data,
            input_objects=[market_id],
            target_address=market_address,
            module_address=market_address
        )


@dataclass
class Transaction:
    """交易结构"""
    sender: Address
    nonce: int
    gas_budget: int
    gas_price: int
    expiration: int
    actions: List[Action]


@dataclass
class SignedTransaction:
    """已签名交易"""
    transaction: Transaction
    signatures: List[bytes]  # 改为签名数组，与Rust SignedTransaction兼容


@dataclass
class VerifiedTransaction:
    """已验证交易"""
    signed_transaction: SignedTransaction
    digest: Digest
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "signedTransaction": {
                "transaction": {
                    "sender": str(self.signed_transaction.transaction.sender),
                    "nonce": self.signed_transaction.transaction.nonce,
                    "gasBudget": self.signed_transaction.transaction.gas_budget,
                    "gasPrice": self.signed_transaction.transaction.gas_price,
                    "expiration": self.signed_transaction.transaction.expiration,
                    "actions": [
                        {
                            "actionType": action.action_type,
                            "params": action.params.hex(),  # 字节数组转换为十六进制字符串
                            "inputObjects": [str(obj_id) for obj_id in action.input_objects],
                            "targetAddress": str(action.target_address),
                            "moduleAddress": str(action.module_address)
                        }
                        for action in self.signed_transaction.transaction.actions
                    ]
                },
                "signatures": [sig.hex() for sig in self.signed_transaction.signatures]
            },
            "digest": str(self.digest)
        }
    
    def _serialize_params(self, params: bytes) -> str:
        """序列化参数，将字节数组转换为十六进制字符串"""
        return params.hex()


class TransactionBuilder:
    """交易构建器"""
    
    def __init__(self):
        self._sender: Optional[Address] = None
        self._nonce: int = 0
        self._gas_budget: int = 1_000_000
        self._gas_price: int = 1
        self._expiration: int = 0xFFFFFFFFFFFFFFFF  # 最大过期时间
        self._actions: List[Action] = []
    
    @classmethod
    def new(cls) -> 'TransactionBuilder':
        """创建新的交易构建器"""
        return cls()
    
    def sender(self, sender: Address) -> 'TransactionBuilder':
        """设置发送者地址"""
        self._sender = sender
        return self
    
    def nonce(self, nonce: int) -> 'TransactionBuilder':
        """设置nonce"""
        self._nonce = nonce
        return self
    
    def gas_budget(self, gas_budget: int) -> 'TransactionBuilder':
        """设置gas预算"""
        self._gas_budget = gas_budget
        return self
    
    def gas_price(self, gas_price: int) -> 'TransactionBuilder':
        """设置gas价格"""
        self._gas_price = gas_price
        return self
    
    def expiration(self, expiration: int) -> 'TransactionBuilder':
        """设置过期时间"""
        self._expiration = expiration
        return self
    
    def add_action(self, action: Action) -> 'TransactionBuilder':
        """添加操作"""
        self._actions.append(action)
        return self
    
    def build(self) -> Transaction:
        """构建交易"""
        if self._sender is None:
            raise ValidationError("Sender address is required")
        
        if not self._actions:
            raise ValidationError("At least one action is required")
        
        return Transaction(
            sender=self._sender,
            nonce=self._nonce,
            gas_budget=self._gas_budget,
            gas_price=self._gas_price,
            expiration=self._expiration,
            actions=self._actions
        )
    
    def build_and_sign(self, signer: Signer) -> VerifiedTransaction:
        """构建并签名交易"""
        transaction = self.build()
        
        # 序列化交易
        tx_bytes = self._serialize_transaction(transaction)
        
        # 签名
        signature = signer.sign(tx_bytes)
        
        # 创建已签名交易
        signed_tx = SignedTransaction(
            transaction=transaction,
            signatures=[signature]  # 改为签名数组
        )
        
        # 计算摘要
        digest = Digest.from_bytes(tx_bytes)
        
        return VerifiedTransaction(
            signed_transaction=signed_tx,
            digest=digest
        )
    
    def _serialize_transaction(self, transaction: Transaction) -> bytes:
        """序列化交易"""
        # 简化的序列化实现
        tx_dict = {
            "sender": str(transaction.sender),
            "nonce": transaction.nonce,
            "gasBudget": transaction.gas_budget,
            "gasPrice": transaction.gas_price,
            "expiration": transaction.expiration,
            "actions": [
                {
                    "actionType": action.action_type,
                    "params": self._serialize_params(action.params),
                    "inputObjects": [str(obj_id) for obj_id in action.input_objects],
                    "targetAddress": str(action.target_address),
                    "moduleAddress": str(action.module_address)
                }
                for action in transaction.actions
            ]
        }
        
        tx_json = json.dumps(tx_dict, sort_keys=True, separators=(',', ':'))
        return tx_json.encode('utf-8')
    
    def _serialize_params(self, params: bytes) -> str:
        """序列化参数，将字节数组转换为十六进制字符串"""
        return params.hex() 