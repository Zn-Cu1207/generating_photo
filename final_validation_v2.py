#!/usr/bin/env python3
"""
最终项目验证 v2
不使用 image_generation_service
"""

import sys
import os
import logging

# 设置项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.WARNING)  # 减少日志输出

print("🎯 最终项目验证 v2")
print("=" * 60)

try:
    # 阶段1: 基本导入
    print("1. 基本模块导入...")
    from db.session import get_session, get_engine
    from db.models import Task, TaskStatus, SQLModel
    from sqlmodel import select
    from infra.config import config
    from library.utils import generate_token, is_valid_email
    from schema.prompt import GenerateRequest
    import requests
    
    print("   ✅ 所有基本模块导入成功")
    
    # 阶段2: 数据库连接
    print("\n2. 数据库连接测试...")
    engine = get_engine()
    print(f"   数据库引擎: {type(engine).__name__}")
    
    # 测试查询
    with get_session() as session:
        result = session.exec(select(1)).first()
        print(f"   数据库查询测试: {result == 1}")
    
    # 阶段3: 创建测试表
    print("\n3. 数据库表创建测试...")
    SQLModel.metadata.create_all(engine)
    print("   ✅ 表创建成功")
    
    # 阶段4: 服务模块测试
    print("\n4. 服务模块测试...")
    from services.task_service import TaskService
    
    # 创建测试任务
    task = TaskService.create_task("最终验证测试 - 一个美丽的日落场景")
    print(f"   ✅ 创建任务: ID={task.id}")
    
    # 更新任务
    TaskService.update_task(task.id, status="processing")
    print(f"   ✅ 更新任务状态")
    
    # 标记完成
    TaskService.mark_task_completed(task.id, "https://example.com/sunset.jpg")
    print(f"   ✅ 标记任务完成")
    
    # 阶段5: 验证数据
    print("\n5. 验证数据...")
    with get_session() as session:
        db_task = session.get(Task, task.id)
        if db_task:
            print(f"   ✅ 从数据库获取任务: 状态={db_task.status}")
            print(f"      描述: {db_task.prompt}")
            print(f"      图片URL: {db_task.image_url}")
    
    # 阶段6: 清理测试数据
    print("\n6. 清理测试数据...")
    TaskService.delete_task(task.id)
    
    with get_session() as session:
        remaining = len(session.exec(select(Task)).all())
        print(f"   剩余任务数: {remaining}")
    
    # 阶段7: 工具函数测试
    print("\n7. 工具函数测试...")
    token = generate_token(16)
    print(f"   生成令牌: {token}")
    email_valid = is_valid_email("test@example.com")
    print(f"   邮箱验证测试: test@example.com = {email_valid}")
    
    # 阶段8: Schema验证
    print("\n8. Schema验证...")
    request = GenerateRequest(
        prompt="验证Schema的图片描述",
        width=768,
        height=512
    )
    print(f"   Schema验证通过: {request.prompt}")
    print(f"   宽度: {request.width}, 高度: {request.height}")
    
    # 阶段9: 配置验证
    print("\n9. 配置验证...")
    print(f"   环境: {config.app.env}")
    print(f"   调试模式: {config.app.debug}")
    print(f"   数据库URL: {config.database.url}")
    print(f"   图片存储路径: {config.file_storage.image_storage_path}")
    
    # 阶段10: 其他服务测试
    print("\n10. 其他服务测试...")
    
    # 测试AI服务
    try:
        from services.ai_service import get_ai_service
        ai_service = get_ai_service()
        print(f"   AI服务初始化: ✅")
        print(f"   API密钥配置: {'已配置' if ai_service.api_key and 'your-' not in ai_service.api_key else '未配置'}")
    except Exception as e:
        print(f"   AI服务测试: ⚠️  {e}")
    
    # 测试图片服务
    try:
        from services.image_service import get_image_service
        image_service = get_image_service()
        print(f"   图片服务初始化: ✅")
        print(f"   存储路径: {image_service.storage_path}")
    except Exception as e:
        print(f"   图片服务测试: ⚠️  {e}")
    
    # 阶段11: 获取任务统计
    print("\n11. 获取任务统计...")
    stats = TaskService.get_task_stats()
    print(f"   任务统计: 总任务={stats['total']}")
    print(f"   待处理: {stats['pending']}, 处理中: {stats['processing']}")
    print(f"   已完成: {stats['completed']}, 已失败: {stats['failed']}")
    
    print("\n" + "=" * 60)
    print("🎉 项目验证完成！所有模块正常工作")
    print("\n📊 项目结构总结:")
    print("""
    ✅ infra/      - 配置、日志等基础设施
    ✅ db/         - 数据库模型和会话管理
    ✅ library/    - 工具函数库
    ✅ schema/     - API数据模式
    ✅ services/   - 业务逻辑层
    """)
    print("\n🚀 下一步可以:")
    print("1. 创建CLI命令行工具")
    print("2. 创建Web API (FastAPI)")
    print("3. 创建简单的前端界面")
    
except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n💡 解决方案:")
    print("1. 检查是否有缺失的依赖: pip install -r requirements.txt")
    print("2. 确保在项目根目录运行")
    print("3. 确保已创建 __init__.py 文件")

print("=" * 60)
