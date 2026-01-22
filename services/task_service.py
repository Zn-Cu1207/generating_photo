"""
任务管理服务
处理任务的创建、查询、更新、删除
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import select

from db.session import get_session
from db.models import Task, TaskStatus
from schema.prompt import TaskResponse, TaskList
import logging

# 设置日志
logger = logging.getLogger(__name__)


class TaskService:
    """
    任务管理服务
    处理所有与任务相关的业务逻辑
    """
    
    @staticmethod
    def create_task(prompt: str, user_id: Optional[int] = None) -> Task:
        """
        创建新任务
        
        参数:
            prompt: 图片描述
            user_id: 用户ID（可选）
            
        返回:
            创建的任务对象
        """
        try:
            logger.info(f"创建任务: prompt={prompt[:50]}...")
            
            # 创建任务对象
            task = Task(
                prompt=prompt,
                status=TaskStatus.PENDING,
                user_id=user_id
            )
            
            # 保存到数据库
            with get_session() as session:
                session.add(task)
                session.commit()
                session.refresh(task)
            
            logger.info(f"任务创建成功: id={task.id}")
            return task
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise
    
    @staticmethod
    def get_task(task_id: int) -> Optional[Task]:
        """
        获取任务
        
        参数:
            task_id: 任务ID
            
        返回:
            任务对象或None
        """
        try:
            with get_session() as session:
                task = session.get(Task, task_id)
                if task:
                    logger.debug(f"获取任务: id={task_id}")
                else:
                    logger.warning(f"任务不存在: id={task_id}")
                return task
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            raise
    
    @staticmethod
    def get_tasks(
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        获取任务列表
        
        参数:
            status: 筛选状态
            limit: 返回数量
            offset: 偏移量
            
        返回:
            任务列表
        """
        try:
            with get_session() as session:
                query = select(Task)
                
                if status:
                    query = query.where(Task.status == status)
                
                query = query.offset(offset).limit(limit)
                
                tasks = session.exec(query).all()
                logger.debug(f"获取任务列表: 总数={len(tasks)}")
                return tasks
                
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            raise
    
    @staticmethod
    def update_task(
        task_id: int,
        status: Optional[str] = None,
        image_url: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        """
        更新任务
        
        参数:
            task_id: 任务ID
            status: 新状态
            image_url: 图片URL
            error_message: 错误信息
            
        返回:
            更新后的任务对象
        """
        try:
            with get_session() as session:
                task = session.get(Task, task_id)
                if not task:
                    logger.warning(f"更新任务失败: 任务不存在 id={task_id}")
                    return None
                
                # 更新字段
                if status:
                    task.status = status
                if image_url:
                    task.image_url = image_url
                if error_message:
                    task.error_message = error_message
                
                task.updated_at = datetime.utcnow()
                session.add(task)
                session.commit()
                session.refresh(task)
                
                logger.info(f"更新任务: id={task_id}, status={status}")
                return task
                
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            raise
    
    @staticmethod
    def update_task_status(task_id: int, status: str) -> bool:
        """
        更新任务状态（快捷方法）
        
        返回:
            是否成功
        """
        task = TaskService.update_task(task_id, status=status)
        return task is not None
    
    @staticmethod
    def mark_task_completed(task_id: int, image_url: str) -> bool:
        """
        标记任务完成（快捷方法）
        
        返回:
            是否成功
        """
        return TaskService.update_task_status(
            task_id, 
            TaskStatus.COMPLETED.value
        ) and TaskService.update_task(task_id, image_url=image_url)
    
    @staticmethod
    def mark_task_failed(task_id: int, error_message: str) -> bool:
        """
        标记任务失败（快捷方法）
        
        返回:
            是否成功
        """
        return TaskService.update_task(
            task_id,
            status=TaskStatus.FAILED.value,
            error_message=error_message
        ) is not None
    
    @staticmethod
    def delete_task(task_id: int) -> bool:
        """
        删除任务
        
        返回:
            是否成功
        """
        try:
            with get_session() as session:
                task = session.get(Task, task_id)
                if not task:
                    logger.warning(f"删除任务失败: 任务不存在 id={task_id}")
                    return False
                
                session.delete(task)
                session.commit()
                
                logger.info(f"删除任务: id={task_id}")
                return True
                
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            raise
    
    @staticmethod
    def get_task_stats() -> Dict[str, Any]:
        """
        获取任务统计信息
        
        返回:
            统计信息字典
        """
        try:
            with get_session() as session:
                # 总数
                total = session.exec(select(Task)).all()
                
                # 按状态统计
                stats = {
                    "total": len(total),
                    "pending": len([t for t in total if t.status == TaskStatus.PENDING]),
                    "processing": len([t for t in total if t.status == TaskStatus.PROCESSING]),
                    "completed": len([t for t in total if t.status == TaskStatus.COMPLETED]),
                    "failed": len([t for t in total if t.status == TaskStatus.FAILED]),
                }
                
                logger.debug(f"任务统计: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            raise


# 便捷函数
def create_task(prompt: str) -> Task:
    """创建任务（便捷函数）"""
    return TaskService.create_task(prompt)


def get_task(task_id: int) -> Optional[Task]:
    """获取任务（便捷函数）"""
    return TaskService.get_task(task_id)


# 测试代码
if __name__ == "__main__":
    print("🧪 测试任务服务")
    print("=" * 50)
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 1. 创建任务
        print("1. 创建任务测试...")
        task = create_task("一只可爱的小猫")
        print(f"   任务ID: {task.id}")
        print(f"   状态: {task.status}")
        print(f"   描述: {task.prompt}")
        
        # 2. 获取任务
        print("\n2. 获取任务测试...")
        fetched = get_task(task.id)
        if fetched:
            print(f"   获取成功: ID={fetched.id}")
        
        # 3. 更新任务状态
        print("\n3. 更新任务状态测试...")
        updated = TaskService.update_task_status(task.id, "processing")
        print(f"   更新结果: {updated}")
        
        fetched = get_task(task.id)
        print(f"   新状态: {fetched.status}")
        
        # 4. 标记完成
        print("\n4. 标记完成测试...")
        completed = TaskService.mark_task_completed(task.id, "https://example.com/cat.jpg")
        print(f"   标记结果: {completed}")
        
        # 5. 获取统计
        print("\n5. 获取统计测试...")
        stats = TaskService.get_task_stats()
        print(f"   统计: {stats}")
        
        # 6. 清理测试数据
        print("\n6. 清理测试数据...")
        deleted = TaskService.delete_task(task.id)
        print(f"   删除结果: {deleted}")
        
        print("\n" + "=" * 50)
        print("✅ 任务服务测试通过")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
