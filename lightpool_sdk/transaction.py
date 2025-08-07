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
from .bincode import bincode_serialize


@dataclass
class Action:
    """交易操作，与Rust Action完全兼容"""
    input_objects: List[ObjectID]   # 与Rust字段顺序一致
    target_address: Address         # target_address
    action_name: str               # action_name (Name类型)
    params: bytes                  # params (Vec<u8>)


class ActionBuilder:
    """操作构建器"""
    
    @staticmethod
    def create_token(contract_address: Address, params: CreateTokenParams) -> Action:
        """创建代币操作"""
        # 使用自定义bincode兼容的序列化，与Rust SDK保持一致
        params_bytes = bincode_serialize(params)
        
        # 添加调试日志
        print(f"📤 [PYTHON SDK] CreateToken serialized params hex: {params_bytes.hex()}")
        print(f"📤 [PYTHON SDK] CreateToken params length: {len(params_bytes)} bytes")
        print(f"📤 [PYTHON SDK] CreateToken original params: {params}")
        
        return Action(
            input_objects=[],
            target_address=contract_address,
            action_name="create",  # 与Rust CREATE_ACTION一致
            params=params_bytes
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
            input_objects=[balance_id],
            target_address=token_address,
            action_name="transfer",  # 与Rust TRANSFER_ACTION一致
            params=params_bytes
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
            input_objects=[token_id],
            target_address=token_address,
            action_name="mint",  # 与Rust MINT_ACTION一致
            params=params_bytes
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
            input_objects=[balance_id],
            target_address=token_address,
            action_name="split",  # 与Rust SPLIT_ACTION一致
            params=params_bytes
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
            input_objects=[main_balance_id] + params.other_balance_ids,
            target_address=token_address,
            action_name="merge",  # 与Rust MERGE_ACTION一致
            params=params_bytes
        )
    
    @staticmethod
    def create_market(contract_address: Address, params: CreateMarketParams) -> Action:
        """创建市场操作"""
        # 使用自定义bincode兼容的序列化
        params_bytes = bincode_serialize(params)
        
        # 添加调试日志
        print(f"📤 [PYTHON SDK] CreateMarket serialized params hex: {params_bytes.hex()}")
        print(f"📤 [PYTHON SDK] CreateMarket params length: {len(params_bytes)} bytes")
        print(f"📤 [PYTHON SDK] CreateMarket original params: {params}")
        
        return Action(
            input_objects=[],
            target_address=contract_address,
            action_name="mkt_create",
            params=params_bytes
        )
    
    @staticmethod
    def update_market(market_address: Address, market_id: ObjectID, params: UpdateMarketParams) -> Action:
        """更新市场操作"""
        # 使用自定义bincode兼容的序列化，与Rust SDK保持一致
        params_bytes = bincode_serialize(params)
        
        # 添加调试日志
        print(f"📤 [PYTHON SDK] UpdateMarket serialized params hex: {params_bytes.hex()}")
        print(f"📤 [PYTHON SDK] UpdateMarket params length: {len(params_bytes)} bytes")
        print(f"📤 [PYTHON SDK] UpdateMarket original params: {params}")
        
        return Action(
            input_objects=[market_id],
            target_address=market_address,
            action_name="mkt_update",
            params=params_bytes
        )
    
    @staticmethod
    def place_order(market_address: Address, market_id: ObjectID, balance_id: ObjectID, params: PlaceOrderParams) -> Action:
        """下单操作"""
        # 使用自定义bincode兼容的序列化，与Rust SDK保持一致
        params_bytes = bincode_serialize(params)
        
        # 添加调试日志
        print(f"📤 [PYTHON SDK] PlaceOrder serialized params hex: {params_bytes.hex()}")
        print(f"📤 [PYTHON SDK] PlaceOrder params length: {len(params_bytes)} bytes")
        print(f"📤 [PYTHON SDK] PlaceOrder original params: {params}")
        
        return Action(
            input_objects=[market_id, balance_id],  # 顺序与Rust一致
            target_address=market_address,
            action_name="ord_place",               # 使用正确的字段名
            params=params_bytes
        )
    
    @staticmethod
    def cancel_order(market_address: Address, market_id: ObjectID, params: CancelOrderParams) -> Action:
        """撤单操作"""
        # 使用自定义bincode兼容的序列化，与Rust SDK保持一致
        params_bytes = bincode_serialize(params)
        
        # 添加调试日志
        print(f"📤 [PYTHON SDK] CancelOrder serialized params hex: {params_bytes.hex() if hasattr(params_bytes, 'hex') else str(params_bytes)}")
        print(f"📤 [PYTHON SDK] CancelOrder params length: {len(params_bytes) if hasattr(params_bytes, '__len__') else 'N/A'} bytes")
        print(f"📤 [PYTHON SDK] CancelOrder original params: {params}")
        
        return Action(
            input_objects=[market_id],
            target_address=market_address,
            action_name="ord_cancel",
            params=params_bytes
        )


@dataclass
class Transaction:
    """交易结构，与Rust Transaction保持一致"""
    sender: Address
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
                    "expiration": self.signed_transaction.transaction.expiration,
                    "actions": [
                        {
                            "inputObjects": [str(obj_id) for obj_id in action.input_objects],
                            "targetAddress": str(action.target_address),
                            "actionName": action.action_name,      # 修正字段名
                            "params": list(action.params)          # Vec<u8> 兼容格式
                        }
                        for action in self.signed_transaction.transaction.actions
                    ]
                },
                "signatures": [sig.hex() for sig in self.signed_transaction.signatures]
            },
            "digest": str(self.digest)
        }
    
    def _serialize_params(self, params: bytes) -> list:
        """序列化参数，将字节数组转换为整数列表，与Rust Vec<u8>兼容"""
        return list(params)


class TransactionBuilder:
    """交易构建器"""
    
    def __init__(self):
        self._sender: Optional[Address] = None
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
            "expiration": transaction.expiration,
            "actions": [
                {
                    "inputObjects": [str(obj_id) for obj_id in action.input_objects],
                    "targetAddress": str(action.target_address),
                    "actionName": action.action_name,
                    "params": self._serialize_params(action.params)
                }
                for action in transaction.actions
            ]
        }
        
        tx_json = json.dumps(tx_dict, sort_keys=True, separators=(',', ':'))
        return tx_json.encode('utf-8')
    
    def _serialize_params(self, params) -> list:
        """序列化参数，将字节数组转换为整数列表，与Rust Vec<u8>兼容"""
        if isinstance(params, bytes):
            return list(params)
        elif isinstance(params, ObjectID):
            # 如果参数是ObjectID，直接返回其字节表示
            return list(params.value)
        else:
            # 其他类型，尝试转换为字节
            if hasattr(params, 'value'):
                return list(params.value)
            else:
                raise ValueError(f"Unsupported params type: {type(params)}") 