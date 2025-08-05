"""
LightPool SDK 加密模块
"""

import secrets
import hashlib
from typing import Optional, Union
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
from cryptography.exceptions import InvalidKey

from .types import Address
from .exceptions import CryptoError


class Signer:
    """LightPool签名者类"""
    
    def __init__(self, private_key: Optional[Union[bytes, int]] = None):
        """
        初始化签名者
        
        Args:
            private_key: 私钥字节数组或整数，如果为None则生成新的密钥对
        """
        if private_key is None:
            # 生成新的Ed25519私钥
            self._private_key = ed25519.Ed25519PrivateKey.generate()
        else:
            try:
                if isinstance(private_key, int):
                    # 从整数创建私钥（转换为32字节）
                    private_key_bytes = private_key.to_bytes(32, byteorder='big')
                    self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
                else:
                    # 如果是字节数组
                    if len(private_key) == 32:
                        self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
                    else:
                        raise ValueError("Ed25519 private key must be 32 bytes")
            except Exception as e:
                raise CryptoError(f"Invalid private key: {e}")
        
        self._public_key = self._private_key.public_key()
        self._address = self._compute_address()
    
    @classmethod
    def new(cls) -> 'Signer':
        """生成新的签名者"""
        return cls()
    
    @classmethod
    def from_secret_key_bytes(cls, secret_key_bytes: bytes) -> 'Signer':
        """从私钥字节数组创建签名者"""
        return cls(secret_key_bytes)
    
    @classmethod
    def from_secret_key_int(cls, secret_key_int: int) -> 'Signer':
        """从私钥整数创建签名者"""
        return cls(secret_key_int)
    
    @classmethod
    def from_hex(cls, hex_string: str) -> 'Signer':
        """从十六进制字符串创建签名者"""
        if hex_string.startswith("0x"):
            hex_string = hex_string[2:]
        secret_key_bytes = bytes.fromhex(hex_string)
        return cls(secret_key_bytes)
    
    def private_key_bytes(self) -> bytes:
        """获取私钥字节数组"""
        return self._private_key.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=NoEncryption()
        )
    
    def private_key_raw(self) -> bytes:
        """获取原始私钥字节数组"""
        return self._private_key.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=NoEncryption()
        )
    
    def private_key_hex(self) -> str:
        """获取私钥十六进制字符串"""
        return "0x" + self.private_key_bytes().hex()
    
    def public_key_bytes(self) -> bytes:
        """获取公钥字节数组"""
        return self._public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
    
    def address(self) -> Address:
        """获取地址"""
        return self._address
    
    def _compute_address(self) -> Address:
        """计算地址"""
        # 获取Ed25519公钥字节（32字节）
        public_key_bytes = self._public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        
        # 使用SHA512哈希公钥，然后取前32字节作为地址（与Rust版本一致）
        sha512_hash = hashlib.sha512(public_key_bytes).digest()
        
        # 取前32字节作为地址
        address_bytes = sha512_hash[:32]
        
        return Address(address_bytes)
    
    def sign(self, message: bytes) -> bytes:
        """
        签名消息 - 使用Ed25519算法
        
        Args:
            message: 要签名的消息
            
        Returns:
            签名结果（64字节的raw Ed25519签名）
        """
        try:
            # Ed25519直接对消息签名，不需要预哈希
            signature = self._private_key.sign(message)
            
            return signature
        except Exception as e:
            raise CryptoError(f"Failed to sign message: {e}")
    
    def sign_hex(self, message_hex: str) -> str:
        """
        签名十六进制消息
        
        Args:
            message_hex: 十六进制消息字符串
            
        Returns:
            十六进制签名结果
        """
        if message_hex.startswith("0x"):
            message_hex = message_hex[2:]
        
        message_bytes = bytes.fromhex(message_hex)
        signature_bytes = self.sign(message_bytes)
        
        return "0x" + signature_bytes.hex()
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """
        验证Ed25519签名
        
        Args:
            message: 原始消息
            signature: 签名
            
        Returns:
            验证结果
        """
        try:
            # Ed25519验证签名
            self._public_key.verify(signature, message)
            return True
        except Exception:
            return False
    
    def verify_hex(self, message_hex: str, signature_hex: str) -> bool:
        """
        验证十六进制签名
        
        Args:
            message_hex: 十六进制消息字符串
            signature_hex: 十六进制签名字符串
            
        Returns:
            验证结果
        """
        if message_hex.startswith("0x"):
            message_hex = message_hex[2:]
        if signature_hex.startswith("0x"):
            signature_hex = signature_hex[2:]
        
        message_bytes = bytes.fromhex(message_hex)
        signature_bytes = bytes.fromhex(signature_hex)
        
        return self.verify(message_bytes, signature_bytes)
    
    def __str__(self) -> str:
        return f"Signer(address={self._address})"
    
    def __repr__(self) -> str:
        return self.__str__() 