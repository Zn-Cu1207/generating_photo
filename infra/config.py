"""
配置管理模块 - 修复 ENCRYPTION_KEY 长度问题
"""

import os
import secrets
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ==================== 枚举定义 ====================
class Environment(str, Enum):
    """运行环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class AIProvider(str, Enum):
    """AI服务提供商枚举"""
    DOUBAO = "doubao"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== 子配置类定义 ====================
@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///./ai_images.db"
    
    def __post_init__(self):
        if not self.url:
            raise ValueError("数据库URL不能为空")
        
        if self.url.startswith("sqlite:///"):
            db_path = self.url.replace("sqlite:///", "")
            if db_path != ":memory:" and not db_path.startswith("/"):
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)


@dataclass
class DoubaoConfig:
    """豆包AI配置"""
    api_key: str = ""
    api_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    default_model: str = "doubao-seedream-4-5-251128"
    timeout: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        if not self.api_key or "your-" in self.api_key:
            print("⚠️  警告: DOUBAO_API_KEY 未配置或使用默认值")
        
        if self.timeout <= 0:
            raise ValueError("超时时间必须大于0")


@dataclass
class AppConfig:
    """应用配置"""
    env: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    port: int = 8000
    host: str = "0.0.0.0"
    debug: bool = True
    secret_key: str = ""
    api_rate_limit: int = 10
    allowed_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ])
    
    def __post_init__(self):
        if not self.secret_key or "your-" in self.secret_key:
            if self.env == Environment.DEVELOPMENT:
                self.secret_key = secrets.token_urlsafe(32)
                print("⚠️  警告: 在开发环境使用临时生成的SECRET_KEY")
        
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"端口号无效: {self.port}")


@dataclass
class FileStorageConfig:
    """文件存储配置"""
    image_storage_path: str = "./static/images"
    max_image_size_mb: int = 5
    allowed_image_types: List[str] = field(default_factory=lambda: [
        "jpg", "png", "jpeg", "webp"
    ])
    max_image_width: int = 2048
    max_image_height: int = 2048
    image_quality: int = 85
    
    def __post_init__(self):
        os.makedirs(self.image_storage_path, exist_ok=True)
        
        if self.max_image_size_mb <= 0:
            raise ValueError("最大图片大小必须大于0")


@dataclass
class SecurityConfig:
    """安全配置"""
    encryption_key: str = ""
    
    def __post_init__(self):
        if not self.encryption_key or "your-" in self.encryption_key:
            if os.getenv("APP_ENV") == "production":
                raise ValueError("生产环境必须配置ENCRYPTION_KEY")
            else:
                # 使用 token_urlsafe(32) 生成 43 个字符的密钥
                self.encryption_key = secrets.token_urlsafe(32)
                print("⚠️  警告: 在开发环境使用临时生成的ENCRYPTION_KEY")
        
        # 重要修改：不再检查 32 个字符，因为 token_urlsafe(32) 生成 43 个字符
        # secrets.token_urlsafe(32) 生成 43 个字符的 URL 安全字符串
        if len(self.encryption_key) < 32:
            # 但至少要有一定长度
            raise ValueError(f"ENCRYPTION_KEY 太短，当前长度: {len(self.encryption_key)}")


@dataclass
class TaskConfig:
    """任务配置"""
    timeout_seconds: int = 120
    max_retries: int = 3
    queue_max_size: int = 100
    cleanup_completed_days: int = 7
    cleanup_failed_days: int = 30
    
    def __post_init__(self):
        if self.timeout_seconds <= 0:
            raise ValueError("任务超时时间必须大于0")


# ==================== 主配置类 ====================
@dataclass
class Config:
    """总配置类"""
    database: DatabaseConfig
    doubao: DoubaoConfig
    app: AppConfig
    file_storage: FileStorageConfig
    security: SecurityConfig
    task: TaskConfig
    ai_provider: AIProvider = AIProvider.DOUBAO
    
    @classmethod
    def load(cls) -> "Config":
        """从环境变量加载配置"""
        # 处理逗号分隔的允许来源
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        allowed_origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
        
        # 处理逗号分隔的图片类型
        types_str = os.getenv("ALLOWED_IMAGE_TYPES", "jpg,png,jpeg,webp")
        allowed_types = [ext.strip().lower() for ext in types_str.split(",") if ext.strip()]
        
        # 解析环境
        env_str = os.getenv("APP_ENV", "development").lower()
        try:
            env = Environment(env_str)
        except ValueError:
            env = Environment.DEVELOPMENT
            print(f"⚠️  未知的环境: {env_str}，使用默认值: development")
        
        # 解析AI提供商
        provider_str = os.getenv("AI_PROVIDER", "doubao").lower()
        try:
            ai_provider = AIProvider(provider_str)
        except ValueError:
            ai_provider = AIProvider.DOUBAO
            print(f"⚠️  未知的AI提供商: {provider_str}，使用默认值: doubao")
        
        # 创建配置实例
        config = cls(
            database=DatabaseConfig(
                url=os.getenv("DATABASE_URL", "sqlite:///./ai_images.db")
            ),
            doubao=DoubaoConfig(
                api_key=os.getenv("DOUBAO_API_KEY", ""),
                api_base_url=os.getenv("DOUBAO_API_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
                default_model=os.getenv("DOUBAO_DEFAULT_MODEL", "doubao-seedream-4-5-251128"),
                timeout=int(os.getenv("DOUBAO_TIMEOUT", "30")),
                max_retries=int(os.getenv("DOUBAO_MAX_RETRIES", "3"))
            ),
            app=AppConfig(
                env=env,
                log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
                port=int(os.getenv("APP_PORT", "8000")),
                host=os.getenv("APP_HOST", "0.0.0.0"),
                debug=os.getenv("APP_DEBUG", "true").lower() == "true",
                secret_key=os.getenv("APP_SECRET_KEY", ""),
                api_rate_limit=int(os.getenv("API_RATE_LIMIT", "10")),
                allowed_origins=allowed_origins
            ),
            file_storage=FileStorageConfig(
                image_storage_path=os.getenv("IMAGE_STORAGE_PATH", "./static/images"),
                max_image_size_mb=int(os.getenv("MAX_IMAGE_SIZE_MB", "5")),
                allowed_image_types=allowed_types,
                max_image_width=int(os.getenv("MAX_IMAGE_WIDTH", "2048")),
                max_image_height=int(os.getenv("MAX_IMAGE_HEIGHT", "2048")),
                image_quality=int(os.getenv("IMAGE_QUALITY", "85"))
            ),
            security=SecurityConfig(
                encryption_key=os.getenv("ENCRYPTION_KEY", "")
            ),
            task=TaskConfig(
                timeout_seconds=int(os.getenv("TASK_TIMEOUT_SECONDS", "120")),
                max_retries=int(os.getenv("TASK_MAX_RETRIES", "3")),
                queue_max_size=int(os.getenv("TASK_QUEUE_MAX_SIZE", "100")),
                cleanup_completed_days=int(os.getenv("CLEANUP_COMPLETED_TASKS_DAYS", "7")),
                cleanup_failed_days=int(os.getenv("CLEANUP_FAILED_TASDS_DAYS", "30"))
            ),
            ai_provider=ai_provider
        )
        
        return config
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if not self.doubao.api_key or "your-" in self.doubao.api_key:
            errors.append("DOUBAO_API_KEY 未配置或使用默认值")
        
        # 修改验证：不检查具体长度，只检查是否太短
        if len(self.security.encryption_key) < 32:
            errors.append(f"ENCRYPTION_KEY 太短，需要至少32个字符，当前长度: {len(self.security.encryption_key)}")
        
        if not self.app.secret_key or "your-" in self.app.secret_key:
            if self.app.env == Environment.PRODUCTION:
                errors.append("生产环境必须配置APP_SECRET_KEY")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（脱敏）"""
        return {
            "database": {
                "url": self.database.url if ":memory:" in self.database.url else "***"
            },
            "doubao": {
                "api_key": "***" if self.doubao.api_key else "",
                "api_base_url": self.doubao.api_base_url,
                "default_model": self.doubao.default_model,
                "timeout": self.doubao.timeout
            },
            "app": {
                "env": self.app.env.value,
                "log_level": self.app.log_level,
                "port": self.app.port,
                "host": self.app.host,
                "debug": self.app.debug,
                "secret_key": "***" if self.app.secret_key else "",
                "api_rate_limit": self.app.api_rate_limit
            },
            "file_storage": {
                "image_storage_path": self.file_storage.image_storage_path,
                "max_image_size_mb": self.file_storage.max_image_size_mb,
                "allowed_image_types": self.file_storage.allowed_image_types
            },
            "security": {
                "encryption_key_length": len(self.security.encryption_key)
            },
            "task": {
                "timeout_seconds": self.task.timeout_seconds,
                "max_retries": self.task.max_retries
            },
            "ai_provider": self.ai_provider.value
        }


# ==================== 创建全局实例 ====================
config = Config.load()


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("🔧 配置模块测试")
    print("=" * 50)
    
    errors = config.validate()
    if errors:
        print("⚠️  配置警告:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 配置验证通过")
    
    print(f"\n📁 数据库URL: {config.database.url}")
    print(f"🤖 AI提供商: {config.ai_provider.value}")
    print(f"🔐 加密密钥长度: {len(config.security.encryption_key)} (应该是43)")
    print(f"🔐 APP密钥长度: {len(config.app.secret_key)}")
    print(f"📷 图片存储: {config.file_storage.image_storage_path}")
    
    print("=" * 50)
