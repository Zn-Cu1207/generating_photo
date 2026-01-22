#!/usr/bin/env python3
"""
最简单的CLI工具
通过命令行生成AI图片
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.task_service import TaskService
from db.models import TaskStatus


def main():
    parser = argparse.ArgumentParser(description="AI图片生成CLI工具")
    parser.add_argument("prompt", help="图片描述")
    parser.add_argument("--width", type=int, default=512, help="图片宽度")
    parser.add_argument("--height", type=int, default=512, help="图片高度")
    
    args = parser.parse_args()
    
    print(f"🎨 生成图片: {args.prompt}")
    print(f"   尺寸: {args.width}x{args.height}")
    print("-" * 40)
    
    try:
        # 1. 创建任务
        print("1. 创建任务...")
        task = TaskService.create_task(args.prompt)
        print(f"   任务ID: {task.id}")
        
        # 2. 更新状态为处理中
        print("2. 开始处理...")
        TaskService.update_task_status(task.id, TaskStatus.PROCESSING.value)
        
        # 3. 模拟AI处理
        print("3. 调用AI生成图片...")
        # 这里应该调用实际的AI服务
        # 现在只是模拟
        import time
        time.sleep(2)  # 模拟处理时间
        
        # 生成模拟的图片URL
        import hashlib
        import base64
        prompt_hash = hashlib.md5(args.prompt.encode()).hexdigest()[:8]
        image_url = f"https://example.com/ai-images/{prompt_hash}.jpg"
        
        # 4. 标记完成
        print("4. 保存结果...")
        TaskService.mark_task_completed(task.id, image_url)
        
        # 获取最终状态
        final_task = TaskService.get_task(task.id)
        
        print("\n" + "=" * 40)
        print("✅ 图片生成完成！")
        print(f"   任务ID: {final_task.id}")
        print(f"   状态: {final_task.status}")
        print(f"   图片URL: {final_task.image_url}")
        print(f"   创建时间: {final_task.created_at}")
        
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
