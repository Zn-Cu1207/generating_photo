"""
Prompt 相关数据模式 - 兼容 Pydantic V2
定义图片生成相关的请求和响应数据结构
"""

from typing import Optional, List, Annotated
from datetime import datetime
from pydantic import Field, field_validator
from sqlmodel import SQLModel


# ==================== 1. 基础模式 ====================
class BasePrompt(SQLModel):
    """提示基础模式"""
    prompt: Annotated[str, Field(min_length=3, max_length=1000, description="图片描述")]
    
    @field_validator('prompt')
    @classmethod
    def clean_prompt(cls, v: str) -> str:
        """清理提示：去除首尾空格"""
        return v.strip()


# ==================== 2. 生成相关模式 ====================
class GenerateRequest(BasePrompt):
    """生成图片请求"""
    width: int = Field(default=512, ge=256, le=1024, description="图片宽度")
    height: int = Field(default=512, ge=256, le=1024, description="图片高度")
    style: Optional[str] = Field(default=None, description="图片风格")


class GenerateResponse(SQLModel):
    """生成图片响应"""
    task_id: int
    prompt: str
    status: str
    estimated_time: Optional[int] = None
    image_url: Optional[str] = None


# ==================== 3. 任务相关模式 ====================
class TaskCreate(BasePrompt):
    """创建任务请求"""
    pass


class TaskUpdate(SQLModel):
    """更新任务请求"""
    status: Optional[str] = None
    image_url: Optional[str] = None
    error_message: Optional[str] = None


class TaskResponse(SQLModel):
    """任务响应"""
    id: int
    prompt: str
    status: str
    image_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True  # 替代原来的 orm_mode


class TaskList(SQLModel):
    """任务列表响应"""
    total: int
    tasks: List[TaskResponse]


# ==================== 4. 批处理模式 ====================
class BatchGenerateRequest(SQLModel):
    """批量生成请求"""
    prompts: Annotated[List[str], Field(min_length=1, max_length=10, description="提示列表")]
    width: int = Field(default=512, ge=256, le=1024)
    height: int = Field(default=512, ge=256, le=1024)


class BatchGenerateResponse(SQLModel):
    """批量生成响应"""
    total: int
    tasks: List[GenerateResponse]


# ==================== 5. 导出接口 ====================
__all__ = [
    # 生成相关
    "GenerateRequest",
    "GenerateResponse",
    "BatchGenerateRequest", 
    "BatchGenerateResponse",
    
    # 任务相关
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskList",
    
    # 基础
    "BasePrompt",
]


# ==================== 6. 测试代码 ====================
if __name__ == "__main__":
    print("🧪 测试 Prompt Schema (Pydantic V2)")
    print("=" * 50)
    
    try:
        # 1. 生成请求测试
        print("1. 生成请求测试:")
        gen_req = GenerateRequest(prompt="一只可爱的猫咪在花园里玩耍")
        print(f"   提示: {gen_req.prompt}")
        print(f"   尺寸: {gen_req.width}x{gen_req.height}")
        
        # 2. 验证提示清理
        print("\n2. 验证提示清理:")
        cleaned = GenerateRequest(prompt="  有空格  ")
        print(f"   清理前: '  有空格  '")
        print(f"   清理后: '{cleaned.prompt}'")
        
        # 3. 批量生成测试
        print("\n3. 批量生成测试:")
        batch_req = BatchGenerateRequest(prompts=["猫", "狗", "鸟"])
        print(f"   提示数量: {len(batch_req.prompts)}")
        print(f"   提示: {batch_req.prompts}")
        
        # 4. 响应测试
        print("\n4. 响应测试:")
        response = GenerateResponse(
            task_id=1,
            prompt="测试提示",
            status="processing"
        )
        print(f"   任务ID: {response.task_id}")
        print(f"   状态: {response.status}")
        print(f"   图片URL: {response.image_url}")  # 应该是 None
        
        # 5. 任务列表测试
        print("\n5. 任务列表测试:")
        task1 = TaskResponse(
            id=1, 
            prompt="任务1",
            status="completed",
            image_url=None,  # 明确设置为 None
            created_at=datetime.now()
        )
        task2 = TaskResponse(
            id=2,
            prompt="任务2", 
            status="pending",
            image_url="https://example.com/image.jpg",
            created_at=datetime.now()
        )
        task_list = TaskList(total=2, tasks=[task1, task2])
        print(f"   总任务数: {task_list.total}")
        print(f"   第一个任务状态: {task_list.tasks[0].status}")
        print(f"   第一个任务图片URL: {task_list.tasks[0].image_url}")
        print(f"   第二个任务图片URL: {task_list.tasks[1].image_url}")
        
        # 6. 测试验证
        print("\n6. 测试验证:")
        try:
            invalid_req = GenerateRequest(prompt="ab")  # 太短
            print("   ❌ 应该失败但没有")
        except Exception as e:
            print(f"   ✅ 正确失败: 提示太短")
        
        try:
            invalid_req = GenerateRequest(prompt="有效的提示", width=2000)  # 宽度太大
            print("   ❌ 应该失败但没有")
        except Exception as e:
            print(f"   ✅ 正确失败: 宽度超出范围")
        
        print("\n" + "=" * 50)
        print("✅ Schema 测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
