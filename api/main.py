
from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from sqlmodel import Session
# from fastapi import Depends
# from typing import Optional, Dict
# from ..db.session import get_session


app = FastAPI(title="AI图片生成API")

# ==================== 数据模型定义 ====================

# class CreateTaskRequest(BaseModel):
#     """创建任务API的请求体格式"""
#     model_config_id: int
#     prompt: str
#     parameters: Optional[Dict[str, str]] = None  # 可选参数

# class CreateTaskResponse(BaseModel):
#     """创建任务API的响应格式"""
#     task_id: int
#     status: str
#     message: str

# ==================== API端点定义 ====================

# from ..api.pic import router as pic_router
# app.include_router(pic_router)

# 第1步：接收POST请求的代码写在这里！
# @app.post("/api/tasks", response_model=CreateTaskResponse)
# async def create_task(
#     request: CreateTaskRequest,  # FastAPI会自动解析请求体
#     session: Session = Depends(get_session),  # 数据库会话
#     current_user_id: int = 1  # 简化：用户认证
# ):
    
    
#     print(f"收到生成请求：用户{current_user_id},prompt: {request.prompt}")
    
#     try:
#         # 调用服务层处理业务逻辑
#         result = services.TaskService.create_generation_task(
#             session=session,
#             user_id=current_user_id,
#             model_config_id=request.model_config_id,
#             prompt=request.prompt,
#             params_override=request.parameters or {}
#         )
        
#         return result
        
#     except ValueError as e:
#         # 业务逻辑错误，返回400
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         # 服务器内部错误，返回500
#         print(f"服务器错误：{e}")
#         raise HTTPException(status_code=500, detail="内部服务器错误")



@app.get("/")
async def root():
   
    return {"message": "AI图片生成API服务运行正常"}

@app.get("/health")
async def health_check(page: int=0):
 
    return {"status": "healthy", "page": page}


if __name__ == '__main__': 
    import uvicorn
    uvicorn.run(app, reload=True)