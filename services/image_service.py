"""
图片处理服务
处理图片的保存、验证、管理等
"""

import os
import shutil
from typing import Optional, Tuple, BinaryIO
from pathlib import Path
import logging
from urllib.parse import urlparse
import requests

from infra.config import config
from library.utils import unique_filename, ensure_dir, is_valid_url
import mimetypes

# 设置日志
logger = logging.getLogger(__name__)


class ImageService:
    """
    图片处理服务
    管理图片的保存、获取、删除等操作
    """
    
    def __init__(self):
        """初始化图片服务"""
        self.storage_path = Path(config.file_storage.image_storage_path)
        self.max_size_mb = config.file_storage.max_image_size_mb
        self.allowed_types = config.file_storage.allowed_image_types
        
        # 确保存储目录存在
        ensure_dir(self.storage_path)
        logger.info(f"图片存储目录: {self.storage_path}")
    
    def save_image(
        self, 
        image_data: bytes, 
        original_filename: Optional[str] = None
    ) -> str:
        """
        保存图片到本地
        
        参数:
            image_data: 图片二进制数据
            original_filename: 原始文件名（用于确定扩展名）
            
        返回:
            保存后的文件路径
        """
        try:
            # 生成唯一文件名
            if original_filename:
                filename = unique_filename(original_filename)
            else:
                filename = unique_filename("image.jpg")
            
            file_path = self.storage_path / filename
            
            # 检查文件大小
            if len(image_data) > self.max_size_mb * 1024 * 1024:
                raise ValueError(f"图片太大，最大支持 {self.max_size_mb}MB")
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"图片保存成功: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"保存图片失败: {e}")
            raise
    
    def save_image_from_url(self, image_url: str) -> str:
        """
        从URL下载并保存图片
        
        参数:
            image_url: 图片URL
            
        返回:
            保存后的文件路径
        """
        try:
            if not is_valid_url(image_url):
                raise ValueError(f"无效的URL: {image_url}")
            
            logger.info(f"从URL下载图片: {image_url}")
            
            # 下载图片
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if not any(img_type in content_type for img_type in ['image/jpeg', 'image/png', 'image/webp']):
                logger.warning(f"非图片内容类型: {content_type}")
            
            # 从URL获取文件名
            parsed_url = urlparse(image_url)
            url_filename = Path(parsed_url.path).name
            
            # 保存图片
            file_path = self.save_image(response.content, url_filename)
            return file_path
            
        except Exception as e:
            logger.error(f"从URL保存图片失败: {e}")
            raise
    
    def get_image_path(self, filename: str) -> Optional[Path]:
        """
        获取图片路径
        
        参数:
            filename: 文件名
            
        返回:
            图片路径或None
        """
        file_path = self.storage_path / filename
        
        if file_path.exists() and file_path.is_file():
            return file_path
        else:
            logger.warning(f"图片不存在: {filename}")
            return None
    
    def get_image_url(self, filename: str) -> Optional[str]:
        """
        获取图片的HTTP访问URL
        
        参数:
            filename: 文件名
            
        返回:
            图片URL或None
        """
        file_path = self.get_image_path(filename)
        if not file_path:
            return None
        
        # 这里假设图片通过静态文件服务访问
        # 实际URL取决于你的Web服务器配置
        return f"/static/images/{filename}"
    
    def delete_image(self, filename: str) -> bool:
        """
        删除图片
        
        参数:
            filename: 文件名
            
        返回:
            是否成功删除
        """
        try:
            file_path = self.storage_path / filename
            
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info(f"删除图片: {filename}")
                return True
            else:
                logger.warning(f"删除图片失败: 文件不存在 {filename}")
                return False
                
        except Exception as e:
            logger.error(f"删除图片失败: {e}")
            raise
    
    def get_storage_info(self) -> dict:
        """
        获取存储信息
        
        返回:
            存储信息字典
        """
        try:
            if not self.storage_path.exists():
                return {
                    "exists": False,
                    "total_files": 0,
                    "total_size_mb": 0
                }
            
            # 统计文件
            total_files = 0
            total_size = 0
            
            for file_path in self.storage_path.iterdir():
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            return {
                "exists": True,
                "storage_path": str(self.storage_path),
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"获取存储信息失败: {e}")
            raise


# 单例实例
_image_service_instance = None

def get_image_service() -> ImageService:
    """获取图片服务实例（单例）"""
    global _image_service_instance
    if _image_service_instance is None:
        _image_service_instance = ImageService()
    return _image_service_instance


# 便捷函数
def save_image(image_data: bytes, filename: str = None) -> str:
    """保存图片（便捷函数）"""
    service = get_image_service()
    return service.save_image(image_data, filename)


# 测试代码
if __name__ == "__main__":
    print("🧪 测试图片服务")
    print("=" * 50)
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        image_service = get_image_service()
        
        # 1. 测试存储信息
        print("1. 测试存储信息...")
        storage_info = image_service.get_storage_info()
        print(f"   存储路径: {storage_info.get('storage_path', '无')}")
        print(f"   文件数量: {storage_info.get('total_files', 0)}")
        print(f"   总大小: {storage_info.get('total_size_mb', 0)}MB")
        
        # 2. 测试保存图片（模拟）
        print("\n2. 测试保存图片...")
        # 创建一个模拟的图片数据（简单的JPEG文件头）
        mock_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        
        try:
            saved_path = image_service.save_image(mock_image_data, "test.jpg")
            print(f"   保存路径: {saved_path}")
            
            # 3. 测试获取图片路径
            print("\n3. 测试获取图片路径...")
            filename = Path(saved_path).name
            image_path = image_service.get_image_path(filename)
            print(f"   获取路径: {image_path}")
            
            if image_path and image_path.exists():
                print(f"   文件存在: ✅")
                
                # 4. 测试获取图片URL
                print("\n4. 测试获取图片URL...")
                image_url = image_service.get_image_url(filename)
                print(f"   图片URL: {image_url}")
                
                # 5. 测试删除图片
                print("\n5. 测试删除图片...")
                deleted = image_service.delete_image(filename)
                print(f"   删除结果: {deleted}")
            else:
                print("   文件不存在，跳过后续测试")
                
        except ValueError as e:
            print(f"   保存测试跳过: {e}")
        
        print("\n" + "=" * 50)
        print("✅ 图片服务测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
