"""
数据模型定义
定义数据库表结构和关系
"""

from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field


# ==================== 第一步：基础模型类 ====================
# 为什么需要基础类？
# 1. 所有模型共享的字段（如id、创建时间）
# 2. 统一的时间戳处理
# 3. 便于扩展公共功能

class BaseModel(SQLModel):
    """
    基础模型类
    所有模型都继承这个类，获得公共字段
    """
    
    # 主键：每个表都需要，用于唯一标识记录
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 创建时间：记录什么时候创建的
    created_at: datetime = Field(
        default_factory=datetime.utcnow,  # 自动设置当前时间
        description="创建时间"
    )
    
    # 更新时间：记录最后一次修改的时间
    updated_at: Optional[datetime] = Field(
        default=None,
        description="更新时间"
    )


# ==================== 第二步：任务状态枚举 ====================
# 为什么用枚举？
# 1. 限制状态值，避免无效状态
# 2. 代码可读性好
# 3. 数据库存储一致

from enum import Enum

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"       # 失败


# ==================== 第三步：核心模型定义 ====================
# 这是最重要的部分，定义实际的数据表

class Task(BaseModel, table=True):
    """
    图片生成任务模型
    存储用户提交的图片生成请求
    """
    
    # 用户输入的描述
    prompt: str = Field(
        description="用户输入的描述文字",
        max_length=1000  # 限制长度，防止数据库过载
    )
    
    # 任务状态
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="任务状态"
    )
    
    # 生成的图片URL
    image_url: Optional[str] = Field(
        default=None,
        description="生成的图片链接"
    )
    
    # 错误信息（如果任务失败）
    error_message: Optional[str] = Field(
        default=None,
        description="错误信息"
    )
    
    # 元信息
    __tablename__ = "tasks"  # 指定表名
    __table_args__ = {
        "comment": "AI图片生成任务表"  # 表注释
    }
    
    def is_completed(self) -> bool:
        """检查任务是否完成"""
        return self.status == TaskStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == TaskStatus.FAILED
    
    def can_process(self) -> bool:
        """检查任务是否可以处理"""
        return self.status == TaskStatus.PENDING


# ==================== 第四步：（可选）用户模型 ====================
# 如果需要用户系统，可以添加这个模型
# 但为了简化，我们先注释掉

'''
class User(BaseModel, table=True):
    """用户模型"""
    
    username: str = Field(
        unique=True,  # 用户名唯一
        index=True,   # 创建索引，加快查询
        description="用户名"
    )
    
    email: str = Field(
        unique=True,
        description="邮箱"
    )
    
    hashed_password: str = Field(
        description="加密后的密码"
    )
    
    is_active: bool = Field(
        default=True,
        description="是否激活"
    )
    
    __tablename__ = "users"
'''


# ==================== 第五步：关系模型（如果需要） ====================
# 如果多个模型有关联，可以定义关系
# 比如：一个用户有多个任务

'''
from sqlmodel import Relationship

# 修改User模型，添加关系
class User(BaseModel, table=True):
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    
    # 一对多关系：一个用户有多个任务
    tasks: List["Task"] = Relationship(back_populates="user")
    
    __tablename__ = "users"


# 修改Task模型，添加外键和关系
class Task(BaseModel, table=True):
    prompt: str
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    image_url: Optional[str] = None
    error_message: Optional[str] = None
    
    # 外键：关联到用户
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="user.id",  # 关联到users表的id字段
        description="用户ID"
    )
    
    # 多对一关系：一个任务属于一个用户
    user: Optional[User] = Relationship(back_populates="tasks")
    
    __tablename__ = "tasks"
'''


# ==================== 第六步：模型工具函数 ====================
# 一些有用的函数，便于使用模型

def get_model_fields(model_class) -> List[str]:
    """获取模型的所有字段名"""
    return list(model_class.__fields__.keys())


def get_required_fields(model_class) -> List[str]:
    """获取模型必须的字段（没有默认值的）"""
    required = []
    for field_name, field in model_class.__fields__.items():
        # 如果没有默认值，且不是主键，且不是Optional类型
        if (field.default is None and 
            field_name != "id" and 
            not str(field.annotation).startswith("Optional")):
            required.append(field_name)
    return required


# ==================== 第七步：模型验证 ====================
# 可以添加数据验证逻辑

def validate_task_data(data: dict) -> List[str]:
    """验证任务数据"""
    errors = []
    
    # 检查必填字段
    if "prompt" not in data or not data["prompt"]:
        errors.append("prompt 不能为空")
    
    # 检查长度
    if "prompt" in data and len(data["prompt"]) > 1000:
        errors.append("prompt 不能超过1000个字符")
    
    return errors


# ==================== 第八步：导出接口 ====================
# 明确导出哪些类和函数

__all__ = [
    # 基础类
    "BaseModel",
    
    # 枚举
    "TaskStatus",
    
    # 模型
    "Task",
    # "User",  # 如果需要用户模型，取消注释
    
    # 工具函数
    "get_model_fields",
    "get_required_fields",
    "validate_task_data",
]


# ==================== 第九步：测试代码 ====================
# 模型定义的测试

if __name__ == "__main__":
    print("🧪 测试数据模型")
    print("=" * 50)
    
    try:
        # 测试1：创建模型实例
        print("1. 创建任务实例...")
        task = Task(
            prompt="一只可爱的猫咪在花园里玩耍",
            status=TaskStatus.PENDING
        )
        
        print(f"   任务ID: {task.id} (应该是None，因为还没保存)")
        print(f"   描述: {task.prompt}")
        print(f"   状态: {task.status}")
        print(f"   创建时间: {task.created_at}")
        
        # 测试2：模型方法
        print("\n2. 测试模型方法...")
        print(f"   是否可以处理: {task.can_process()}")
        print(f"   是否完成: {task.is_completed()}")
        print(f"   是否失败: {task.is_failed()}")
        
        # 测试3：工具函数
        print("\n3. 测试工具函数...")
        print(f"   所有字段: {get_model_fields(Task)}")
        print(f"   必填字段: {get_required_fields(Task)}")
        
        # 测试4：数据验证
        print("\n4. 测试数据验证...")
        test_data = {"prompt": "测试"}
        errors = validate_task_data(test_data)
        print(f"   有效数据验证: {errors}")
        
        invalid_data = {"prompt": ""}
        errors = validate_task_data(invalid_data)
        print(f"   无效数据验证: {errors}")
        
        print("\n" + "=" * 50)
        print("✅ 模型定义测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
