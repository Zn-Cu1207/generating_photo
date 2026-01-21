# db/session.py
from sqlmodel import create_engine, Session
import os

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./generation.db")
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    """获取数据库会话"""
    with Session(engine) as session:
        yield session

# db/crud/task_crud.py
from sqlmodel import select
from models.task import GenerationTask
from typing import List, Optional

class TaskCRUD:
    """任务数据操作类"""
    
    @staticmethod
    def create_task(session, task_data: dict) -> GenerationTask:
        """创建任务"""
        task = GenerationTask(**task_data)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    
    @staticmethod
    def get_task(session, task_id: int) -> Optional[GenerationTask]:
        """获取单个任务"""
        return session.get(GenerationTask, task_id)
    
    @staticmethod
    def list_tasks(
        session, 
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[GenerationTask]:
        """查询任务列表"""
        query = select(GenerationTask)
        
        if user_id:
            query = query.where(GenerationTask.user_id == user_id)
        if status:
            query = query.where(GenerationTask.status == status)
            
        query = query.offset(offset).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    def update_task(session, task_id: int, update_data: dict) -> Optional[GenerationTask]:
        """更新任务"""
        task = session.get(GenerationTask, task_id)
        if not task:
            return None
            
        for key, value in update_data.items():
            setattr(task, key, value)
        
        task.updated_at = datetime.now()
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    
    @staticmethod
    def delete_task(session, task_id: int) -> bool:
        """删除任务"""
        task = session.get(GenerationTask, task_id)
        if not task:
            return False
            
        session.delete(task)
        session.commit()
        return True