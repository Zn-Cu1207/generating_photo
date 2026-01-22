"""
工具函数库 - 简化版
包含项目最核心的工具函数
"""

import secrets
import string
import uuid
from datetime import datetime
from pathlib import Path
import re
import hashlib
import json
from typing import Optional, Dict, Any


# ==================== 1. 安全工具 ====================
def generate_token(length: int = 32) -> str:
    """生成随机令牌"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str) -> str:
    """哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()


# ==================== 2. 文件工具 ====================
def is_image_file(filename: str) -> bool:
    """检查是否是图片文件"""
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    return Path(filename).suffix.lower() in image_exts


def unique_filename(original: str) -> str:
    """生成唯一文件名: 时间_随机码.扩展名"""
    path = Path(original)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_code = str(uuid.uuid4())[:8]
    return f"{timestamp}_{random_code}{path.suffix}"


def ensure_dir(path: str) -> Path:
    """确保目录存在"""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


# ==================== 3. 验证工具 ====================
def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """验证URL格式"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


# ==================== 4. 字符串工具 ====================
def truncate(text: str, max_len: int = 100) -> str:
    """截断字符串"""
    return text[:max_len] + '...' if len(text) > max_len else text


def to_snake_case(text: str) -> str:
    """转换为蛇形命名: CamelCase -> camel_case"""
    text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
    return text.lower()


# ==================== 5. 时间工具 ====================
def now_str() -> str:
    """当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_time(dt: datetime) -> str:
    """格式化时间"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ==================== 6. 数据工具 ====================
def safe_json_loads(data: str) -> Optional[Dict[str, Any]]:
    """安全解析JSON"""
    try:
        return json.loads(data)
    except:
        return None


def remove_none(data: Dict[str, Any]) -> Dict[str, Any]:
    """移除字典中的None值"""
    return {k: v for k, v in data.items() if v is not None}


# ==================== 7. 导出接口 ====================
__all__ = [
    # 安全工具
    "generate_token",
    "hash_password",
    
    # 文件工具
    "is_image_file",
    "unique_filename",
    "ensure_dir",
    
    # 验证工具
    "is_valid_email",
    "is_valid_url",
    
    # 字符串工具
    "truncate",
    "to_snake_case",
    
    # 时间工具
    "now_str",
    "format_time",
    
    # 数据工具
    "safe_json_loads",
    "remove_none",
]


# ==================== 8. 测试代码 ====================
if __name__ == "__main__":
    print("🔧 工具函数测试")
    print("=" * 50)
    
    # 测试安全工具
    print(f"随机令牌: {generate_token(16)}")
    print(f"密码哈希: {hash_password('mypassword')}")
    
    # 测试文件工具
    print(f"\n是否图片: {is_image_file('photo.jpg')}")
    print(f"唯一文件名: {unique_filename('my_photo.jpg')}")
    
    # 测试验证工具
    print(f"\n邮箱验证: {is_valid_email('test@example.com')}")
    print(f"URL验证: {is_valid_url('https://example.com')}")
    
    # 测试字符串工具
    print(f"\n字符串截断: {truncate('这是一个很长的字符串', 5)}")
    print(f"蛇形命名: {to_snake_case('CamelCaseString')}")
    
    # 测试时间工具
    print(f"\n当前时间: {now_str()}")
    
    # 测试数据工具
    data = '{"name": "Alice", "age": 25}'
    print(f"\nJSON解析: {safe_json_loads(data)}")
    
    clean_data = remove_none({"a": 1, "b": None, "c": "hello"})
    print(f"清理字典: {clean_data}")
    
    print("\n" + "=" * 50)
    print("✅ 工具函数测试完成")
