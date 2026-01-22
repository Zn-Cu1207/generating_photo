"""
AI服务调用
调用豆包AI生成图片
"""

import requests
import time
from typing import Optional, Dict, Any
import logging
from pathlib import Path
import json

from infra.config import config
from library.utils import generate_token

# 设置日志
logger = logging.getLogger(__name__)


class AIService:
    """
    AI图片生成服务
    调用豆包AI生成图片
    """
    
    def __init__(self):
        """初始化AI服务"""
        self.api_key = config.doubao.api_key
        self.api_base = config.doubao.api_base_url
        self.model = config.doubao.default_model
        self.timeout = config.doubao.timeout
        self.max_retries = config.doubao.max_retries
        
        if not self.api_key or "your-" in self.api_key:
            logger.warning("豆包API密钥未配置，AI服务可能无法正常工作")
    
    def generate_image(
        self, 
        prompt: str, 
        width: int = 512, 
        height: int = 512,
        style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        调用AI生成图片
        
        参数:
            prompt: 图片描述
            width: 图片宽度
            height: 图片高度
            style: 图片风格
            
        返回:
            包含图片信息的字典
        """
        logger.info(f"生成图片: prompt={prompt[:50]}..., size={width}x{height}")
        
        # 构建请求
        url = f"{self.api_base}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建消息
        messages = [
            {
                "role": "user",
                "content": f"请生成一张图片，描述是：{prompt}"
            }
        ]
        
        # 构建请求体
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "extra_body": {
                "image_gen": {
                    "width": width,
                    "height": height,
                    "prompt": prompt
                }
            }
        }
        
        # 添加风格（如果有）
        if style:
            data["extra_body"]["image_gen"]["style"] = style
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"调用AI接口，第{attempt+1}次尝试...")
                
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                # 检查响应
                if response.status_code == 200:
                    result = response.json()
                    logger.info("AI接口调用成功")
                    return self._parse_response(result)
                else:
                    error_msg = f"AI接口错误: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # 指数退避
                        logger.info(f"等待{wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(error_msg)
                        
            except requests.exceptions.Timeout:
                error_msg = f"AI接口超时 (第{attempt+1}次)"
                logger.error(error_msg)
                
                if attempt < self.max_retries - 1:
                    continue
                else:
                    raise Exception("AI接口多次调用超时")
                    
            except Exception as e:
                error_msg = f"AI接口调用异常: {e}"
                logger.error(error_msg)
                
                if attempt < self.max_retries - 1:
                    continue
                else:
                    raise
        
        raise Exception("AI服务调用失败")
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析AI接口响应
        
        参数:
            response_data: AI接口返回的原始数据
            
        返回:
            解析后的图片信息
        """
        try:
            # 这里需要根据豆包AI的实际响应格式调整
            # 假设响应格式为：
            # {
            #   "choices": [
            #     {
            #       "message": {
            #         "content": "图片描述或图片URL"
            #       }
            #     }
            #   ]
            # }
            
            choices = response_data.get("choices", [])
            if not choices:
                raise Exception("AI响应中没有choices")
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            # 生成临时的图片URL（实际应该从响应中获取）
            # 这里只是示例
            image_id = generate_token(8)
            image_url = f"https://example.com/generated/{image_id}.jpg"
            
            result = {
                "success": True,
                "image_url": image_url,
                "content": content,
                "raw_response": response_data
            }
            
            logger.debug(f"解析AI响应成功: {result}")
            return result
            
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        测试AI服务连接
        
        返回:
            是否连接成功
        """
        try:
            if not self.api_key or "your-" in self.api_key:
                logger.warning("API密钥未配置，跳过连接测试")
                return False
            
            # 简单的连接测试
            test_prompt = "测试连接"
            result = self.generate_image(test_prompt, 128, 128)
            
            success = result.get("success", False)
            if success:
                logger.info("AI服务连接测试成功")
            else:
                logger.warning("AI服务连接测试失败")
                
            return success
            
        except Exception as e:
            logger.error(f"AI服务连接测试失败: {e}")
            return False


# 单例实例
_ai_service_instance = None

def get_ai_service() -> AIService:
    """获取AI服务实例（单例）"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance


# 便捷函数
def generate_image(prompt: str, width: int = 512, height: int = 512) -> Dict[str, Any]:
    """生成图片（便捷函数）"""
    service = get_ai_service()
    return service.generate_image(prompt, width, height)


# 测试代码
if __name__ == "__main__":
    print("🧪 测试AI服务")
    print("=" * 50)
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        ai_service = get_ai_service()
        
        # 1. 测试连接
        print("1. 测试AI服务连接...")
        connected = ai_service.test_connection()
        print(f"   连接状态: {'✅ 成功' if connected else '❌ 失败'}")
        
        if not connected and (not ai_service.api_key or "your-" in ai_service.api_key):
            print("   跳过实际调用测试（API密钥未配置）")
        else:
            # 2. 测试生成图片
            print("\n2. 测试生成图片...")
            result = generate_image(
                prompt="一只可爱的小猫",
                width=256,
                height=256
            )
            
            print(f"   生成结果: {result.get('success', False)}")
            print(f"   图片URL: {result.get('image_url', '无')}")
            print(f"   内容: {result.get('content', '无')[:50]}...")
        
        print("\n" + "=" * 50)
        print("✅ AI服务测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
