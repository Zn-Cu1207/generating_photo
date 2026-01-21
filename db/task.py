# db/task.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from uuid import uuid4

class GenerationTaskBase(SQLModel):
    """任务基础字段（创建时可输入的）"""
    user_id: int
    model_config_id: int
    prompt: str = Field(max_length=1000)
    params_override: Optional[dict] = Field(default={}, sa_type=JSON)

class GenerationTask(GenerationTaskBase, table=True):
    """任务表模型"""
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(default="pending")  # pending, processing, succeeded, failed
    result_image_url: Optional[str] = None
    failed_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ModelConfig(SQLModel, table=True):
    """模型配置表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    api_url: str
    api_key: str  # 实际应该加密存储
    default_params: dict = Field(default={}, sa_type=JSON)
    is_active: bool = Field(default=True)