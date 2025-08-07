"""
LightPool SDK RPC客户端
"""

import json
import asyncio
from typing import Optional, Dict, Any, List
import aiohttp
from aiohttp import ClientTimeout

from .types import Address, ObjectID, TransactionReceipt, ExecutionStatus
from .exceptions import NetworkError, RpcError


class LightPoolClient:
    """LightPool RPC客户端"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            base_url: RPC服务器基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """确保会话已创建"""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def _make_request(self, method: str, params) -> Dict[str, Any]:
        """
        发送RPC请求
        
        Args:
            method: RPC方法名
            params: 请求参数
            
        Returns:
            响应数据
        """
        await self._ensure_session()
        
        # jsonrpsee使用位置参数，需要将参数包装在数组中
        # SubmitTransactionParams作为第一个参数传递
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": [params]  # 使用位置参数数组格式
        }
        
        # Ensure clean JSON serialization
        import json
        clean_payload = json.loads(json.dumps(payload, separators=(',', ':')))
        


        
        try:
            async with self.session.post(
                f"{self.base_url}/rpc",
                json=clean_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    raise NetworkError(f"HTTP {response.status}: {response.reason}")
                
                data = await response.json()
                
                if "error" in data:
                    error = data["error"]
                    raise RpcError(
                        message=error.get("message", "Unknown RPC error"),
                        code=error.get("code"),
                        details=error
                    )
                
                return data.get("result", {})
                
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error: {e}")
        except json.JSONDecodeError as e:
            raise NetworkError(f"Invalid JSON response: {e}")
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            节点是否健康
        """
        try:
            # 尝试连接RPC服务器
            await self._ensure_session()
            
            # 发送一个简单的POST请求来检查服务器是否响应
            async with self.session.post(
                f"{self.base_url}/rpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "submitTransaction",
                    "params": {},
                    "id": 1
                },
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                # 如果服务器响应，说明节点是可达的
                # 即使返回错误，也说明服务器在运行
                return response.status == 200 or response.status == 400
                
        except Exception:
            return False
    
    async def submit_transaction(self, transaction: 'VerifiedTransaction') -> Dict[str, Any]:
        """
        提交交易
        
        Args:
            transaction: 已验证的交易
            
        Returns:
            交易提交结果
        """
        # 序列化交易，只发送SignedTransaction部分
        # 将Address转换为字节数组（32字节）
        def address_to_bytes(addr):
            hex_str = str(addr).replace('0x', '')
            return list(bytes.fromhex(hex_str))
        
        def objectid_to_bytes(obj_id):
            hex_str = str(obj_id).replace('0x', '')
            return list(bytes.fromhex(hex_str))
        
        # 先构造actions数组
        actions_list = []
        for action in transaction.signed_transaction.transaction.actions:
            action_dict = {
                "inputs": [objectid_to_bytes(obj_id) for obj_id in action.input_objects],
                "contract": address_to_bytes(action.target_address),
                "action": self._action_name_to_u64(action.action_name),
                "params": list(action.params)  # 字节数组转换为整数列表，与Rust Vec<u8>兼容
            }
            actions_list.append(action_dict)
        
        # 构造transaction对象，与Rust Transaction结构保持一致
        transaction_dict = {
            "sender": address_to_bytes(transaction.signed_transaction.transaction.sender),
            "expiration": transaction.signed_transaction.transaction.expiration,
            "actions": actions_list
        }
        
        # 构造signatures数组
        signatures_list = []
        for sig in transaction.signed_transaction.signatures:
            sig_dict = self._signature_to_rust_format(sig)
            signatures_list.append(sig_dict)
        
        # 构造SignedTransaction格式
        signed_transaction = {
            "transaction": transaction_dict,
            "signatures": signatures_list
        }
        
        # 构造SubmitTransactionParams格式，与Rust SDK保持一致
        params = {
            "tx": signed_transaction
        }
        
        # 构造符合SubmitTransactionParams的格式
        # SubmitTransactionParams { tx: SignedTransaction }
        submit_transaction_params = {
            "tx": {
                "transaction": transaction_dict,
                "signatures": signatures_list
            }
        }
        
        # Debug: print the transaction JSON (clean format)
        import json
        clean_json = json.dumps(submit_transaction_params, separators=(',', ':'))
        print(f"📤 [PYTHON SDK] SubmitTransactionParams (clean): {clean_json}")
        
        result = await self._make_request("submitTransaction", submit_transaction_params)
        
        # 解析响应
        return {
            "digest": result.get("digest"),
            "receipt": TransactionReceipt(
                status=ExecutionStatus(result.get("receipt", {}).get("status", "failure")),
                events=result.get("receipt", {}).get("events", []),
                effects=result.get("receipt", {}).get("effects", {}),
                digest=result.get("digest", "")
            )
        }
    
    def _serialize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """序列化参数，确保所有对象都能正确序列化"""
        serialized = {}
        for key, value in params.items():
            if hasattr(value, '__str__'):
                serialized[key] = str(value)
            elif hasattr(value, 'to_bytes'):
                # 对于U256等类型，转换为字节然后编码
                serialized[key] = value.to_bytes().hex()
            else:
                serialized[key] = value
        return serialized
    
    def _action_name_to_u64(self, action_name: str) -> int:
        """将action名称转换为u64值，与Rust Name类型兼容"""
        # 实现与Rust Name::from_str_literal_const相同的逻辑
        BASE = 32
        NAME_LENGTH = 12
        
        if len(action_name) > NAME_LENGTH:
            raise ValueError(f"Action name too long: {action_name}")
        
        result = 0
        for c in action_name:
            if c == '_':
                digit = 0
            elif '1' <= c <= '5':
                digit = ord(c) - ord('1') + 1
            elif 'a' <= c <= 'z':
                digit = ord(c) - ord('a') + 6
            else:
                raise ValueError(f"Invalid character in action name: {c}")
            
            result = result * BASE + digit
        
        # 用零填充到12个字符
        chars_processed = len(action_name)
        while chars_processed < NAME_LENGTH:
            result = result * BASE
            chars_processed += 1
        
        return result
    
    def _signature_to_rust_format(self, signature: bytes) -> Dict[str, Any]:
        """将DER编码的签名转换为Rust Signature格式"""
        # 如果签名是DER编码的，我们需要转换为raw格式
        # Ed25519签名应该是64字节：前32字节是part1，后32字节是part2
        if len(signature) == 64:
            # 已经是raw格式
            part1 = list(signature[:32])
            part2 = list(signature[32:])
        else:
            # 可能是DER编码，需要解码
            # 对于Ed25519，我们可能需要从DER格式中提取64字节的raw签名
            # 这里暂时假设我们能得到64字节的raw签名
            raise ValueError(f"Unsupported signature format, length: {len(signature)}")
        
        return {
            "part1": part1,
            "part2": part2
        }
    
    async def get_transaction(self, digest: str) -> Optional[Dict[str, Any]]:
        """
        获取交易信息
        
        Args:
            digest: 交易摘要
            
        Returns:
            交易信息
        """
        try:
            result = await self._make_request("getTransaction", {"digest": digest})
            return result
        except RpcError:
            return None
    
    async def get_transaction_receipt(self, digest: str) -> Optional[TransactionReceipt]:
        """
        获取交易收据
        
        Args:
            digest: 交易摘要
            
        Returns:
            交易收据
        """
        try:
            result = await self._make_request("getTransactionReceipt", {"digest": digest})
            
            return TransactionReceipt(
                status=ExecutionStatus(result.get("status", "failure")),
                events=result.get("events", []),
                effects=result.get("effects", {}),
                digest=digest
            )
        except RpcError:
            return None
    
    async def get_object(self, object_id: ObjectID) -> Optional[Dict[str, Any]]:
        """
        获取对象信息
        
        Args:
            object_id: 对象ID
            
        Returns:
            对象信息
        """
        try:
            result = await self._make_request("getObject", {"objectId": str(object_id)})
            return result
        except RpcError:
            return None
    
    async def get_balance(self, address: Address, object_id: ObjectID) -> Optional[Dict[str, Any]]:
        """
        获取余额信息
        
        Args:
            address: 地址
            object_id: 代币对象ID
            
        Returns:
            余额信息
        """
        try:
            result = await self._make_request("getBalance", {
                "address": str(address),
                "objectId": str(object_id)
            })
            return result
        except RpcError:
            return None
    
    async def get_market_info(self, market_id: ObjectID) -> Optional[Dict[str, Any]]:
        """
        获取市场信息
        
        Args:
            market_id: 市场ID
            
        Returns:
            市场信息
        """
        try:
            result = await self._make_request("getMarketInfo", {"marketId": str(market_id)})
            return result
        except RpcError:
            return None
    
    async def get_order_book(self, market_id: ObjectID, depth: int = 10) -> Optional[Dict[str, Any]]:
        """
        获取订单簿
        
        Args:
            market_id: 市场ID
            depth: 深度
            
        Returns:
            订单簿信息
        """
        try:
            result = await self._make_request("getOrderBook", {
                "marketId": str(market_id),
                "depth": depth
            })
            return result
        except RpcError:
            return None
    
    async def get_orders(self, address: Address, market_id: Optional[ObjectID] = None) -> List[Dict[str, Any]]:
        """
        获取用户订单
        
        Args:
            address: 用户地址
            market_id: 市场ID（可选）
            
        Returns:
            订单列表
        """
        try:
            params = {"address": str(address)}
            if market_id:
                params["marketId"] = str(market_id)
            
            result = await self._make_request("getOrders", params)
            return result.get("orders", [])
        except RpcError:
            return []
    
    async def get_trades(self, market_id: ObjectID, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取交易历史
        
        Args:
            market_id: 市场ID
            limit: 限制数量
            
        Returns:
            交易历史
        """
        try:
            result = await self._make_request("getTrades", {
                "marketId": str(market_id),
                "limit": limit
            })
            return result.get("trades", [])
        except RpcError:
            return []
    
    async def get_account_info(self, address: Address) -> Optional[Dict[str, Any]]:
        """
        获取账户信息
        
        Args:
            address: 账户地址
            
        Returns:
            账户信息
        """
        try:
            result = await self._make_request("getAccountInfo", {"address": str(address)})
            return result
        except RpcError:
            return None
    
    async def get_chain_info(self) -> Optional[Dict[str, Any]]:
        """
        获取链信息
        
        Returns:
            链信息
        """
        try:
            result = await self._make_request("getChainInfo", {})
            return result
        except RpcError:
            return None
    
    async def close(self):
        """关闭客户端连接"""
        if self.session:
            await self.session.close()
            self.session = None 