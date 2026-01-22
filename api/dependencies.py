"""
API 依赖注入
为 FastAPI 提供数据库会话、认证等依赖
"""

from typing import Generator, Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Header
from sqlmodel import Session
import logging
import hashlib
import hmac
import time

from db.session import get_session
from infra.config import config
from library.utils import generate_token

# 获取日志器
logger = logging.getLogger(__name__)


# ==================== 数据库依赖 ====================
def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话依赖
    每个请求获取一个独立的数据库会话
    """
    logger.debug("📊 创建数据库会话")
    with get_session() as session:
        yield session
        logger.debug("📊 数据库会话关闭")


# 类型别名，方便在路由中使用
DatabaseDep = Depends(get_db)


# ==================== 认证依赖 ====================
def get_current_user(
    x_api_key: Optional[str] = Header(None, description="API密钥"),
    authorization: Optional[str] = Header(None, description="Bearer令牌"),
) -> Dict[str, Any]:
    """
    获取当前用户（简化版）
    
    在实际项目中，这里应该验证JWT或API密钥
    现在只返回模拟的用户信息
    """
    # 如果没有提供认证信息，返回匿名用户
    if not x_api_key and not authorization:
        logger.debug("👤 匿名用户访问")
        return {
            "id": 0,
            "username": "anonymous",
            "is_authenticated": False
        }
    
    # 如果有API密钥，验证它
    if x_api_key:
        # 这里应该验证API密钥的有效性
        # 现在只是简单检查格式
        if x_api_key.startswith("sk_"):
            logger.debug(f"🔑 API密钥验证通过: {x_api_key[:10]}...")
            return {
                "id": 1001,
                "username": "api_user",
                "is_authenticated": True,
                "api_key": x_api_key
            }
    
    # 如果有Bearer令牌，验证它
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # 去掉 "Bearer "
        logger.debug(f"🔐 Bearer令牌验证: {token[:10]}...")
        return {
            "id": 1002,
            "username": "bearer_user",
            "is_authenticated": True,
            "token": token
        }
    
    # 如果认证信息无效
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证信息",
        headers={"WWW-Authenticate": "Bearer"},
    )


# 类型别名
CurrentUserDep = Depends(get_current_user)


# ==================== 速率限制依赖 ====================
class RateLimiter:
    """
    简单的速率限制器
    
    在实际项目中，应该使用更健壮的方案，如Redis
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # client_ip: [timestamps]
    
    def is_allowed(self, client_ip: str) -> bool:
        """检查是否允许请求"""
        now = time.time()
        
        # 清理过期请求
        if client_ip in self.requests:
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if now - t < 60  # 只保留最近60秒的请求
            ]
        
        # 检查请求次数
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        # 记录本次请求
        self.requests[client_ip].append(now)
        return True


# 创建全局速率限制器实例
rate_limiter = RateLimiter(requests_per_minute=30)

def get_rate_limiter() -> RateLimiter:
    """获取速率限制器实例"""
    return rate_limiter


# ==================== 签名验证依赖 ====================
def verify_signature(
    x_signature: str = Header(..., description="请求签名"),
    x_timestamp: str = Header(..., description="时间戳"),
    body: bytes = b"",
) -> bool:
    """
    验证请求签名
    
    用于保护API请求不被篡改
    实际项目中使用HMAC-SHA256签名
    """
    try:
        # 计算签名
        secret = config.security.encryption_key.encode()
        message = x_timestamp.encode() + b"|" + body
        expected_signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        
        # 验证签名
        if not hmac.compare_digest(x_signature, expected_signature):
            logger.warning("❌ 签名验证失败")
            return False
        
        # 验证时间戳（防止重放攻击）
        timestamp = int(x_timestamp)
        now = int(time.time())
        if abs(now - timestamp) > 300:  # 5分钟内有效
            logger.warning("❌ 请求已过期")
            return False
        
        logger.debug("✅ 签名验证通过")
        return True
        
    except Exception as e:
        logger.error(f"签名验证异常: {e}")
        return False


# ==================== 工具函数 ====================
def get_client_ip(request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"


def generate_request_id() -> str:
    """生成请求ID"""
    return f"req_{generate_token(8)}"


# 导出
__all__ = [
    "get_db",
    "DatabaseDep",
    "get_current_user", 
    "CurrentUserDep",
    "get_rate_limiter",
    "verify_signature",
    "get_client_ip",
    "generate_request_id",
]
