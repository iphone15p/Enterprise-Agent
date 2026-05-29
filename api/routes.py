"""
API 路由模块
FastAPI 接口定义
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from graph.workflow import Workflow


# 创建路由器
router = APIRouter()

# 创建工作流实例
workflow = Workflow()


# 请求模型
class ProjectRequest(BaseModel):
    """项目请求模型"""
    requirements: str
    language: Optional[str] = "python"


class TaskRequest(BaseModel):
    """任务请求模型"""
    task_description: str
    language: Optional[str] = "python"


class CodeReviewRequest(BaseModel):
    """代码审查请求模型"""
    code: str
    language: Optional[str] = "python"


# API 接口
@router.post("/execute-project")
async def execute_project(request: ProjectRequest):
    """
    执行完整项目流程
    
    Args:
        request: 项目请求
        
    Returns:
        项目执行结果
    """
    try:
        result = workflow.execute_project(request.requirements)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-report")
async def generate_report(request: ProjectRequest):
    """
    生成项目报告
    
    Args:
        request: 项目请求
        
    Returns:
        格式化的项目报告
    """
    try:
        report = workflow.execute_task_pipeline(request.requirements)
        return {
            "status": "success",
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan-tasks")
async def plan_tasks(request: TaskRequest):
    """
    任务规划
    
    Args:
        request: 任务请求
        
    Returns:
        任务规划结果
    """
    try:
        plan = workflow.planner.generate_plan(request.task_description)
        return {
            "status": "success",
            "plan": plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-code")
async def generate_code(request: TaskRequest):
    """
    生成代码
    
    Args:
        request: 任务请求
        
    Returns:
        生成的代码
    """
    try:
        code = workflow.coder.generate_code(request.task_description, request.language)
        return {
            "status": "success",
            "code": code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review-code")
async def review_code(request: CodeReviewRequest):
    """
    代码审查
    
    Args:
        request: 代码审查请求
        
    Returns:
        审查报告
    """
    try:
        review = workflow.reviewer.generate_report(request.code, request.language)
        return {
            "status": "success",
            "review": review
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow-history")
async def get_workflow_history():
    """
    获取工作流历史记录
    
    Returns:
        工作流历史记录
    """
    try:
        history = workflow.get_workflow_history()
        return {
            "status": "success",
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-workflow")
async def reset_workflow():
    """
    重置工作流状态
    
    Returns:
        重置结果
    """
    try:
        workflow.reset()
        return {
            "status": "success",
            "message": "工作流已重置"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/weather")
async def get_weather(city: str):
    """
    查询天气
    
    Args:
        city: 城市名称
        
    Returns:
        天气信息
    """
    try:
        from tools.weather_tool import query_weather
        weather = query_weather(city)
        return {
            "status": "success",
            "weather": weather
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/search")
async def web_search(query: str, count: int = 5):
    """
    联网搜索
    
    Args:
        query: 搜索关键词
        count: 返回结果数量
        
    Returns:
        搜索结果
    """
    try:
        from tools.web_search import web_search
        results = web_search(query, count)
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    健康检查
    
    Returns:
        系统健康状态
    """
    return {
        "status": "healthy",
        "service": "Enterprise Agent System API"
    }
