from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from ..services.file_processor import FileProcessor
from ..services.cosmos_service import CosmosDBService
from ..services.openai_service import OpenAIService
from ..models.entity import Entity, Relationship
import logging
from typing import List, Dict, Any, Optional
import uuid
import json
import os

router = APIRouter(prefix="/api/files", tags=["files"])
logger = logging.getLogger(__name__)

# 服务依赖
def get_file_processor():
    return FileProcessor()

def get_cosmos_service():
    return CosmosDBService()

def get_openai_service():
    return OpenAIService()

# 处理状态跟踪
processing_jobs = {}

@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    file_processor: FileProcessor = Depends(get_file_processor),
    cosmos_service: CosmosDBService = Depends(get_cosmos_service),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """上传文件并处理"""
    try:
        # 生成唯一job_id
        job_id = str(uuid.uuid4())
        
        # 创建文件名
        file_name = f"{job_id}_{file.filename}"
        
        # 初始化处理状态
        processing_jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "file_name": file.filename,
            "entities": [],
            "message": "文件已上传，正在处理中..."
        }
        
        # 异步处理文件
        background_tasks.add_task(
            process_file_background,
            job_id,
            file,
            file_name,
            file_processor,
            cosmos_service,
            openai_service
        )
        
        return {"job_id": job_id, "status": "processing", "message": "文件上传成功，开始处理..."}
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/status/{job_id}")
async def get_processing_status(job_id: str):
    """获取文件处理状态"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="处理任务不存在")
    
    return processing_jobs[job_id]

@router.get("/entities/{job_id}")
async def get_job_entities(
    job_id: str,
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """获取处理任务的实体列表"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="处理任务不存在")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed":
        return {"status": job["status"], "message": "处理尚未完成", "entities": []}
    
    entity_ids = job.get("entity_ids", [])
    entities = []
    
    for entity_id in entity_ids:
        entity = cosmos_service.get_entity(entity_id)
        if entity:
            entities.append(entity.dict())
    
    return {"status": "completed", "entities": entities}

# 后台处理任务
async def process_file_background(
    job_id: str,
    file: UploadFile,
    file_name: str,
    file_processor: FileProcessor,
    cosmos_service: CosmosDBService,
    openai_service: OpenAIService
):
    """后台处理文件任务"""
    try:
        # 处理文件
        processing_jobs[job_id]["progress"] = 10
        processing_jobs[job_id]["message"] = "正在解析文件..."
        
        entities, file_url, content_type = await file_processor.process_file(file, file_name)
        
        processing_jobs[job_id]["progress"] = 30
        processing_jobs[job_id]["message"] = "文件解析完成，正在提取实体..."
        
        # 如果是文档类型，需要使用OpenAI提取实体
        if content_type == "document":
            # 读取文档内容
            with open(file_url, "r", encoding="utf-8") as f:
                text_content = f.read()
            
            # 分析文档，提取实体和关系
            processing_jobs[job_id]["progress"] = 50
            processing_jobs[job_id]["message"] = "正在使用AI分析文档..."
            
            analysis_result = await openai_service.analyze_entity_document(text_content)
            
            # 从分析结果中获取实体
            raw_entities = analysis_result.get("entities", [])
            relationships = analysis_result.get("relationships", [])
            
            # 创建实体对象
            for entity_data in raw_entities:
                entity = Entity(
                    name=entity_data.get("name", "未命名"),
                    **{k: v for k, v in entity_data.items() if k != "name"}
                )
                entities.append(entity.dict())
        
        # 保存实体到Cosmos DB
        processing_jobs[job_id]["progress"] = 70
        processing_jobs[job_id]["message"] = "正在保存实体到数据库..."
        
        entity_ids = []
        for entity_data in entities:
            if isinstance(entity_data, dict) and "name" in entity_data:
                entity = Entity(**entity_data)
                result = cosmos_service.create_entity(entity)
                entity_ids.append(result["id"])
        
        # 处理关系(如果存在)
        processing_jobs[job_id]["progress"] = 90
        processing_jobs[job_id]["message"] = "正在处理实体关系..."
        
        # TODO: 处理关系逻辑
        
        # 完成处理
        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["progress"] = 100
        processing_jobs[job_id]["message"] = "处理完成"
        processing_jobs[job_id]["entity_ids"] = entity_ids
        processing_jobs[job_id]["entity_count"] = len(entity_ids)
        
    except Exception as e:
        logger.error(f"处理文件失败: {str(e)}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["message"] = f"处理失败: {str(e)}" 