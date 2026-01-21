import os #操作系统接口
import secrets #生成安全随机数，可以生成临时的安全密钥
from typing import List, Optional, Dict, Any #类型提示
from dataclasses import dataclass, field #数据类装饰器？
from enum import Enum #枚举
from pathlib import Path #路经处理
from dotenv import load_dotenv #加载.env文件
# 加载 .env 文件中的环境变量
load_dotenv()

class Environment(str, Enum):
    """运行环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    """
    数据库配置
    负责数据库连接和配置
    """
    url: str = "sqlite:///./ai_images.db"
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.url:
            raise ValueError("数据库URL不能为空")
        
        # 如果是SQLite，确保数据库文件目录存在
        if self.url.startswith("sqlite:///"):
            db_path = self.url.replace("sqlite:///", "")
            if db_path != ":memory:" and not db_path.startswith("/"):
                # 相对路径，确保目录存在
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)

@dataclass
class DoubaoConfig:
    """
    豆包AI配置
    负责豆包API的配置
    """
    api_key: str = ""
    api_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    default_model: str = "doubao-seedream-4-5-251128"
    timeout: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.api_key or "your-" in self.api_key:
            print("⚠️  警告: DOUBAO_API_KEY 未配置或使用默认值")
        
        if self.timeout <= 0:
            raise ValueError("超时时间必须大于0")
        
        if self.max_retries < 0:
            raise ValueError("重试次数不能为负数")
        
@dataclass
class AppConfig:
    """
    应用配置
    负责Web应用的基本配置
    """
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

@dataclass
class FileStorageConfig:
    """
    文件存储配置
    负责图片存储相关配置
    """
    image_storage_path: str = "./static/images"
    max_image_size_mb: int = 5
    allowed_image_types: List[str] = field(default_factory=lambda: [
        "jpg", "png", "jpeg", "webp"
    ])

@dataclass
class SecurityConfig:
    """
    安全配置
    负责加密和认证相关配置
    """
    encryption_key: str = ""
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.encryption_key or "your-" in self.encryption_key:
            if os.getenv("APP_ENV") == "production":
                raise ValueError("生产环境必须配置ENCRYPTION_KEY")
            else:
                # 在开发环境生成一个临时密钥
                self.encryption_key = secrets.token_urlsafe(32)
                print("⚠️  警告: 在开发环境使用临时生成的ENCRYPTION_KEY")
        
        if len(self.encryption_key) != 32:
            raise ValueError(f"ENCRYPTION_KEY必须是32个字符，当前长度: {len(self.encryption_key)}")
        
@dataclass
class Config:
    """
    总配置类
    聚合所有子配置，提供统一的配置接口
    """
    # 子配置
    database: DatabaseConfig
    doubao: DoubaoConfig
    app: AppConfig
    file_storage: FileStorageConfig
    security: SecurityConfig
    task: TaskConfig
    
    # 主配置
    ai_provider: AIProvider = AIProvider.DOUBAO

@classmethod
def load(cls) -> "Config":
    """
    从环境变量加载配置
    这是工厂方法，创建配置实例
    """
    # 处理逗号分隔的允许来源
    origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    allowed_origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

def validate(self) -> List[str]:
    """
    验证配置的完整性
    返回错误信息列表，空列表表示验证通过
    """
    errors = []
    
    # 验证必要配置
    if not self.doubao.api_key or "your-" in self.doubao.api_key:
        errors.append("DOUBAO_API_KEY 未配置或使用默认值")
    
    if len(self.security.encryption_key) != 32:
        errors.append(f"ENCRYPTION_KEY 必须是32个字符，当前长度: {len(self.security.encryption_key)}")
    
    return errors

def to_dict(self) -> Dict[str, Any]:
    """将配置转换为字典（隐藏敏感信息）"""
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
        # ... 其他配置
    }

# 创建全局配置实例
config = Config.load()