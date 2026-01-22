"""
图片相关路由
处理图片生成、查询、管理等所有操作
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Path, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
import logging
import asyncio
import time
import os
from pathlib import Path as FPath

from sqlmodel import Session, select
from db.models import Task, TaskStatus
from schema.prompt import GenerateRequest, GenerateResponse, TaskResponse, TaskList
from services.task_service import TaskService
from services.ai_service import get_ai_service
from services.image_service import get_image_service
from api.dependencies import DatabaseDep, CurrentUserDep, get_client_ip

# 获取日志器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


# ==================== 图片生成 ====================
@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_image(
    request: Request,
    data: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = DatabaseDep,
    current_user: Dict = CurrentUserDep,
) -> GenerateResponse:
    """
    生成AI图片
    
    接收描述，创建异步任务，在后台生成图片
    """
    logger.info(f"🎨 生成图片请求: {data.prompt[:50]}...")
    logger.info(f"   用户: {current_user.get('username')}, IP: {get_client_ip(request)}")
    
    try:
        # 1. 创建任务
        task = TaskService.create_task(
            prompt=data.prompt,
            user_id=current_user.get("id")
        )
        logger.info(f"✅ 任务创建成功: id={task.id}")
        
        # 2. 添加到后台任务
        background_tasks.add_task(
            process_image_task,
            task_id=task.id,
            prompt=data.prompt,
            width=data.width,
            height=data.height,
            style=data.style,
            user_id=current_user.get("id")
        )
        
        # 3. 返回响应
        return GenerateResponse(
            task_id=task.id,
            prompt=data.prompt,
            status="pending",
            estimated_time=20,  # 预估20秒完成
        )
        
    except Exception as e:
        logger.error(f"❌ 生成图片失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成图片失败: {e}"
        )


async def process_image_task(
    task_id: int,
    prompt: str,
    width: int = 512,
    height: int = 512,
    style: Optional[str] = None,
    user_id: Optional[int] = None
):
    """
    处理图片生成的后台任务
    """
    start_time = time.time()
    
    try:
        logger.info(f"🚀 开始处理图片任务: id={task_id}")
        
        # 1. 更新状态为处理中
        TaskService.update_task_status(task_id, TaskStatus.PROCESSING.value)
        
        # 2. 调用AI服务
        ai_service = get_ai_service()
        image_service = get_image_service()
        
        # 检查API密钥
        if not ai_service.api_key or "your-" in ai_service.api_key:
            logger.warning(f"🤖 AI API密钥未配置，使用模拟数据")
            
            # 模拟AI处理
            await asyncio.sleep(2)
            
            # 生成模拟结果
            import hashlib
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
            image_url = f"http://localhost:8000/static/images/mock_{prompt_hash}.jpg"
            
            # 创建模拟图片文件
            mock_path = f"./static/images/mock_{prompt_hash}.jpg"
            with open(mock_path, "w") as f:
                f.write("mock image data")
                
        else:
            # 实际调用AI
            logger.info(f"�� 调用AI服务生成图片")
            result = ai_service.generate_image(prompt, width, height, style)
            
            if not result.get("success"):
                raise Exception(f"AI生成失败: {result}")
            
            image_url = result.get("image_url", "")
            if not image_url:
                raise Exception("AI未返回图片URL")
        
        # 3. 保存图片
        logger.info(f"💾 保存图片")
        saved_path = image_service.save_image_from_url(image_url)
        
        # 4. 标记任务完成
        TaskService.mark_task_completed(task_id, image_url)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ 图片生成完成: id={task_id}, 耗时: {elapsed:.1f}秒")
        
    except Exception as e:
        logger.error(f"❌ 图片生成失败: id={task_id}, 错误: {e}")
        TaskService.mark_task_failed(task_id, str(e))


# ==================== 任务管理 ====================
@router.get("/tasks", response_model=TaskList)
async def get_tasks(
    db: Session = DatabaseDep,
    status: Optional[str] = Query(None, description="筛选状态"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    page: int = Query(1, ge=1, description="页码"),
    user_id: Optional[int] = Query(None, description="用户ID（管理员用）"),
    current_user: Dict = CurrentUserDep,
) -> TaskList:
    """
    获取任务列表
    
    支持分页、状态筛选
    """
    logger.info(f"📋 获取任务列表: page={page}, status={status}")
    
    try:
        offset = (page - 1) * limit
        
        # 构建查询
        query = select(Task)
        
        # 状态筛选
        if status:
            query = query.where(Task.status == status)
        
        # 用户筛选（普通用户只能看自己的）
        if not current_user.get("is_authenticated") or current_user.get("id", 0) < 1000:
            query = query.where(Task.user_id == current_user.get("id"))
        elif user_id:
            query = query.where(Task.user_id == user_id)
        
        # 获取总数
        total = len(db.exec(query).all())
        
        # 应用分页
        query = query.offset(offset).limit(limit)
        
        # 执行查询
        tasks = db.exec(query).all()
        
        logger.info(f"📊 返回 {len(tasks)} 个任务，总数: {total}")
        
        return TaskList(
            total=total,
            tasks=[TaskResponse.from_orm(task) for task in tasks],
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error(f"❌ 获取任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {e}"
        )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int = Path(..., ge=1, description="任务ID"),
    db: Session = DatabaseDep,
    current_user: Dict = CurrentUserDep,
) -> TaskResponse:
    """
    获取任务详情
    """
    logger.info(f"🔍 获取任务详情: id={task_id}")
    
    try:
        task = db.get(Task, task_id)
        
        if not task:
            logger.warning(f"⚠️ 任务不存在: id={task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {task_id}"
            )
        
        # 权限检查
        if (not current_user.get("is_authenticated") or 
            current_user.get("id", 0) < 1000) and task.user_id != current_user.get("id"):
            logger.warning(f"⛔ 无权访问任务: id={task_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此任务"
            )
        
        logger.info(f"✅ 找到任务: id={task_id}, status={task.status}")
        return TaskResponse.from_orm(task)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取任务详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务详情失败: {e}"
        )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int = Path(..., ge=1, description="任务ID"),
    db: Session = DatabaseDep,
    current_user: Dict = CurrentUserDep,
):
    """
    删除任务
    """
    logger.info(f"🗑️ 删除任务: id={task_id}")
    
    try:
        task = db.get(Task, task_id)
        
        if not task:
            logger.warning(f"⚠️ 任务不存在: id={task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {task_id}"
            )
        
        # 权限检查
        if (not current_user.get("is_authenticated") or 
            current_user.get("id", 0) < 1000) and task.user_id != current_user.get("id"):
            logger.warning(f"⛔ 无权删除任务: id={task_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此任务"
            )
        
        db.delete(task)
        db.commit()
        
        logger.info(f"✅ 任务删除成功: id={task_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除任务失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除任务失败: {e}"
        )


# ==================== 图片文件 ====================
@router.get("/images/{filename}")
async def get_image(
    filename: str = Path(..., description="图片文件名"),
    thumbnail: bool = Query(False, description="是否返回缩略图"),
):
    """
    获取图片文件
    """
    logger.info(f"🖼️ 获取图片: {filename}, thumbnail={thumbnail}")
    
    try:
        image_service = get_image_service()
        file_path = image_service.get_image_path(filename)
        
        if not file_path or not file_path.exists():
            logger.warning(f"⚠️ 图片不存在: {filename}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"图片不存在: {filename}"
            )
        
        # 如果是缩略图，返回小版本
        if thumbnail:
            thumb_path = file_path.with_stem(f"{file_path.stem}_thumb")
            if thumb_path.exists():
                return FileResponse(thumb_path)
        
        return FileResponse(file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取图片失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取图片失败: {e}"
        )


@router.delete("/images/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    filename: str = Path(..., description="图片文件名"),
    current_user: Dict = CurrentUserDep,
):
    """
    删除图片文件
    """
    logger.info(f"🗑️ 删除图片: {filename}")
    
    try:
        # 权限检查（只允许管理员）
        if not current_user.get("is_authenticated") or current_user.get("id", 0) < 1000:
            logger.warning(f"⛔ 无权删除图片: {filename}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除图片"
            )
        
        image_service = get_image_service()
        success = image_service.delete_image(filename)
        
        if not success:
            logger.warning(f"⚠️ 图片不存在: {filename}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"图片不存在: {filename}"
            )
        
        logger.info(f"✅ 图片删除成功: {filename}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除图片失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除图片失败: {e}"
        )


# ==================== 系统状态 ====================
@router.get("/status")
async def get_status(
    db: Session = DatabaseDep,
    current_user: Dict = CurrentUserDep,
) -> Dict[str, Any]:
    """
    获取系统状态
    """
    logger.info("📊 获取系统状态")
    
    try:
        # 获取任务统计
        task_stats = TaskService.get_task_stats()
        
        # 获取图片服务状态
        image_service = get_image_service()
        storage_info = image_service.get_storage_info()
        
        # 获取AI服务状态
        ai_service = get_ai_service()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "running",
            "tasks": task_stats,
            "storage": storage_info,
            "ai_service": {
                "configured": bool(ai_service.api_key and "your-" not in ai_service.api_key),
                "connected": ai_service.test_connection(),
            },
            "current_user": {
                "id": current_user.get("id"),
                "username": current_user.get("username"),
                "authenticated": current_user.get("is_authenticated", False)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 获取系统状态失败: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }


@router.get("/health")
async def health_check(
    db: Session = DatabaseDep,
) -> Dict[str, Any]:
    """
    健康检查
    """
    try:
        # 测试数据库连接
        from db.session import health_check as db_health
        db_status = db_health()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": db_status.get("status", "unknown"),
            "database": db_status.get("status") == "healthy",
            "version": "1.0.0"
        }
        
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }


# 导出路由器
__all__ = ["router"]
