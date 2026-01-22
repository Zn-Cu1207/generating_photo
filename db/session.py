"""
数据库会话管理模块 - 修复 DetachedInstanceError
"""

import sys
import os
from contextlib import contextmanager
from typing import Generator, Optional, Any, List, Dict, Type, TypeVar
from datetime import datetime

# 设置Python导入路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入SQLModel
from sqlmodel import create_engine, SQLModel, Session, select, Field
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

# 导入配置
try:
    from infra.config import config
except ImportError as e:
    print(f"❌ 配置导入失败: {e}")
    class SimpleConfig:
        database = type('obj', (object,), {'url': 'sqlite:///./ai_images.db'})()
        app = type('obj', (object,), {'debug': True})()
    config = SimpleConfig()


# ==================== 数据库引擎管理 ====================
class DatabaseEngine:
    """数据库引擎管理器"""
    
    _instance: Optional[Engine] = None
    
    @classmethod
    def get_engine(cls) -> Engine:
        """获取数据库引擎"""
        if cls._instance is None:
            engine_config = {
                "echo": config.app.debug,
                "poolclass": QueuePool,
                "pool_size": 5,
                "max_overflow": 10,
            }
            
            if "sqlite" in config.database.url:
                engine_config["connect_args"] = {"check_same_thread": False}
            
            cls._instance = create_engine(config.database.url, **engine_config)
        
        return cls._instance
    
    @classmethod
    def dispose(cls):
        """关闭所有数据库连接"""
        if cls._instance:
            cls._instance.dispose()
            cls._instance = None


# 便捷函数
get_engine = DatabaseEngine.get_engine


# ==================== Session管理 ====================
@contextmanager
def get_session() -> Generator[Session, None, None]:
    """获取数据库会话"""
    session = None
    
    try:
        engine = get_engine()
        session = Session(engine, expire_on_commit=False)  # 修复：防止对象过期
        yield session
        session.commit()
    except Exception as e:
        if session:
            session.rollback()
        raise
    finally:
        if session:
            session.close()


# ==================== CRUD操作 ====================
def create_one(model_instance: SQLModel) -> SQLModel:
    """创建单个记录"""
    with get_session() as session:
        session.add(model_instance)
        session.flush()  # 获取ID但不提交
        session.commit()
        session.refresh(model_instance)  # 刷新以获取数据库生成的值
        return model_instance


def read_one(model_class: Type[SQLModel], id: Any) -> Optional[SQLModel]:
    """按ID读取单个记录"""
    with get_session() as session:
        instance = session.get(model_class, id)
        if instance:
            # 在返回前访问属性，确保它们被加载
            _ = instance.id, instance.__dict__
        return instance


def read_many(
    model_class: Type[SQLModel], 
    filters: Optional[Dict] = None,
    limit: Optional[int] = None
) -> List[SQLModel]:
    """读取多个记录"""
    with get_session() as session:
        query = select(model_class)
        
        if filters:
            for key, value in filters.items():
                field = getattr(model_class, key, None)
                if field is not None:
                    query = query.where(field == value)
        
        if limit:
            query = query.limit(limit)
        
        result = session.exec(query)
        instances = result.all()
        
        # 确保属性被加载
        for instance in instances:
            _ = instance.__dict__
        
        return instances


def update_one(
    model_class: Type[SQLModel],
    id: Any,
    update_data: Dict[str, Any]
) -> Optional[SQLModel]:
    """更新单个记录"""
    with get_session() as session:
        instance = session.get(model_class, id)
        if not instance:
            return None
        
        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        session.add(instance)
        session.commit()
        session.refresh(instance)  # 刷新以获取更新后的值
        return instance


def delete_one(model_class: Type[SQLModel], id: Any) -> bool:
    """删除单个记录"""
    with get_session() as session:
        instance = session.get(model_class, id)
        if not instance:
            return False
        
        session.delete(instance)
        session.commit()
        return True


# ==================== FastAPI支持 ====================
def get_db() -> Generator[Session, None, None]:
    """FastAPI依赖注入"""
    with get_session() as session:
        yield session


# ==================== 数据库健康检查 ====================
def health_check() -> Dict[str, Any]:
    """数据库健康检查"""
    try:
        with get_session() as session:
            result = session.exec(select(1))
            data = result.first()
            
            if data == 1:
                return {"status": "healthy"}
            else:
                return {"status": "unhealthy", "error": f"查询结果异常: 期望 1，实际得到 {data}"}
                
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ==================== 数据库初始化 ====================
def init_database(create_tables: bool = False):
    """初始化数据库"""
    health = health_check()
    if health["status"] != "healthy":
        raise RuntimeError(f"数据库连接失败: {health.get('error')}")
    
    if create_tables:
        try:
            SQLModel.metadata.create_all(get_engine())
        except Exception as e:
            raise RuntimeError(f"创建表失败: {e}")


# ==================== 导出接口 ====================
__all__ = [
    "get_engine", "get_session", "get_db",
    "create_one", "read_one", "read_many", "update_one", "delete_one",
    "health_check", "init_database",
    "Session", "select", "SQLModel", "Field"
]


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("🧪 测试数据库会话管理 (修复DetachedInstanceError)")
    print("=" * 60)
    
    from typing import Optional
    
    # 定义测试模型
    class TestUser(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        email: str
    
    try:
        # 1. 健康检查
        print("1. 数据库健康检查...")
        health = health_check()
        print(f"   结果: {health}")
        
        if health["status"] != "healthy":
            print(f"   ❌ 数据库不健康: {health.get('error')}")
            raise RuntimeError("数据库连接失败")
        
        print("   ✅ 数据库健康")
        
        # 2. 初始化数据库
        print("\n2. 初始化数据库...")
        init_database(create_tables=True)
        print("   ✅ 数据库初始化完成")
        
        # 3. 测试CRUD
        print("\n3. 测试CRUD操作...")
        
        # Create
        print("   🔧 Create 测试...")
        user = TestUser(name="测试用户", email="test@example.com")
        created_user = create_one(user)
        print(f"   ✅ Create 成功, ID: {created_user.id}")
        
        # Read
        print("   🔍 Read 测试...")
        read_user = read_one(TestUser, 1)
        if read_user:
            # 在访问属性前，确保我们有正确的实例
            print(f"   ✅ Read 成功: ID={read_user.id}, 姓名={read_user.name}, 邮箱={read_user.email}")
        else:
            print("   ❌ Read 失败: 未找到用户")
            raise RuntimeError("Read 操作失败")
        
        # Update
        print("   ✏️  Update 测试...")
        updated = update_one(TestUser, 1, {"name": "更新后的用户"})
        if updated:
            print(f"   ✅ Update 成功: {updated.name}")
        else:
            print("   ❌ Update 失败")
            raise RuntimeError("Update 操作失败")
        
        # Delete
        print("   🗑️  Delete 测试...")
        deleted = delete_one(TestUser, 1)
        if deleted:
            print("   ✅ Delete 成功")
        else:
            print("   ❌ Delete 失败")
            raise RuntimeError("Delete 操作失败")
        
        # 验证删除
        print("   🔍 验证删除...")
        user = read_one(TestUser, 1)
        if not user:
            print("   ✅ 验证: 记录已成功删除")
        
        print("\n" + "=" * 60)
        print("🎉 所有CRUD测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
