from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from ..services.autogen_service import AutoGenService
from ..services.cosmos_service import CosmosDBService
from ..models.entity import Entity
from autogen_core import CancellationToken
import logging
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
logger = logging.getLogger(__name__)

# 服务依赖
def get_autogen_service():
    return AutoGenService()

def get_cosmos_service():
    return CosmosDBService()

# 存储活跃对话
active_conversations = {}
# 存储取消令牌
active_conversations_tokens = {}

@router.post("/start")
async def start_conversation(
    entity_ids: List[str],
    query: str,
    background_tasks: BackgroundTasks,
    autogen_service: AutoGenService = Depends(get_autogen_service),
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """开始一个新的对话"""
    try:
        # 生成对话ID
        conversation_id = str(uuid.uuid4())
        
        # 获取实体
        entities = []
        for entity_id in entity_ids:
            entity = cosmos_service.get_entity(entity_id)
            if entity:
                entities.append(entity)
            else:
                logger.warning(f"实体 {entity_id} 不存在")
        
        if not entities:
            raise HTTPException(status_code=400, detail="未找到有效实体")
        
        # 创建取消令牌
        cancellation_token = CancellationToken()
        active_conversations_tokens[conversation_id] = cancellation_token
        
        # 初始化对话状态
        active_conversations[conversation_id] = {
            "status": "initializing",
            "query": query,
            "entity_ids": entity_ids,
            "messages": [],
            "relationships": [],
            "summary": "",
            "visualization": {}
        }
        
        # 后台运行对话
        background_tasks.add_task(
            run_conversation_background,
            conversation_id,
            query,
            entities,
            autogen_service,
            cancellation_token
        )
        
        return {
            "conversation_id": conversation_id,
            "status": "initializing",
            "message": "对话初始化中..."
        }
    except Exception as e:
        logger.error(f"开始对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"开始对话失败: {str(e)}")

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取对话状态和内容"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return active_conversations[conversation_id]

@router.post("/{conversation_id}/messages")
async def add_message(
    conversation_id: str,
    message: str,
    background_tasks: BackgroundTasks,
    autogen_service: AutoGenService = Depends(get_autogen_service),
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """向现有对话添加新消息"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    conversation = active_conversations[conversation_id]
    
    # 取消之前的处理（如果还在运行）
    if conversation_id in active_conversations_tokens:
        old_token = active_conversations_tokens[conversation_id]
        old_token.cancel()
    
    # 创建新的取消令牌
    cancellation_token = CancellationToken()
    active_conversations_tokens[conversation_id] = cancellation_token
    
    # 添加用户消息
    conversation["messages"].append({
        "role": "user",
        "content": message
    })
    
    # 获取实体
    entities = []
    for entity_id in conversation["entity_ids"]:
        entity = cosmos_service.get_entity(entity_id)
        if entity:
            entities.append(entity)
    
    # 获取历史消息
    history = [msg["content"] for msg in conversation["messages"]]
    
    # 更新对话状态
    conversation["status"] = "processing"
    
    # 后台继续对话
    background_tasks.add_task(
        run_conversation_background,
        conversation_id,
        message,
        entities,
        autogen_service,
        cancellation_token,
        history
    )
    
    return {
        "conversation_id": conversation_id,
        "status": "processing",
        "message": "处理中..."
    }

@router.get("/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: str,
    query: str,
    autogen_service: AutoGenService = Depends(get_autogen_service),
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """流式处理对话"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    conversation = active_conversations[conversation_id]
    
    # 获取实体
    entities = []
    for entity_id in conversation["entity_ids"]:
        entity = cosmos_service.get_entity(entity_id)
        if entity:
            entities.append(entity)
    
    # 获取历史消息
    history = [msg["content"] for msg in conversation["messages"]]
    
    # 设置事件流响应头
    async def event_generator():
        try:
            async for message in autogen_service.run_conversation_stream(query, entities, history):
                # 将消息转换为SSE格式
                yield f"data: {json.dumps(message)}\n\n"
        except Exception as e:
            logger.error(f"流式处理失败: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            yield "data: {\"type\": \"done\"}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.post("/{conversation_id}/cancel")
async def cancel_conversation(conversation_id: str):
    """取消正在进行的对话"""
    if conversation_id not in active_conversations_tokens:
        raise HTTPException(status_code=404, detail="对话不存在或已完成")
    
    # 触发取消
    active_conversations_tokens[conversation_id].cancel()
    
    # 更新状态
    if conversation_id in active_conversations:
        active_conversations[conversation_id]["status"] = "cancelled"
        active_conversations[conversation_id]["message"] = "对话已取消"
    
    return {"status": "cancelled", "message": "对话已取消"}

@router.post("/{conversation_id}/save")
async def save_conversation(
    conversation_id: str,
    save_path: Optional[str] = None,
    autogen_service: AutoGenService = Depends(get_autogen_service)
):
    """保存对话状态"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if not save_path:
        import os
        save_path = f"conversation_{conversation_id}.json"
    
    try:
        await autogen_service.save_conversation_state(save_path)
        return {"status": "success", "message": f"对话状态已保存到 {save_path}"}
    except Exception as e:
        logger.error(f"保存对话状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存对话状态失败: {str(e)}")

@router.post("/{conversation_id}/load")
async def load_conversation(
    conversation_id: str,
    load_path: str,
    autogen_service: AutoGenService = Depends(get_autogen_service)
):
    """加载对话状态"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    try:
        await autogen_service.load_conversation_state(load_path)
        active_conversations[conversation_id]["status"] = "loaded"
        active_conversations[conversation_id]["message"] = f"对话状态已从 {load_path} 加载"
        return {"status": "success", "message": f"对话状态已从 {load_path} 加载"}
    except Exception as e:
        logger.error(f"加载对话状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加载对话状态失败: {str(e)}")

@router.get("/{conversation_id}/relationships")
async def get_conversation_relationships(conversation_id: str):
    """获取对话中发现的关系"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    conversation = active_conversations[conversation_id]
    
    return {
        "conversation_id": conversation_id,
        "relationships": conversation.get("relationships", [])
    }

@router.get("/{conversation_id}/summary")
async def get_conversation_summary(conversation_id: str):
    """获取对话总结"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    conversation = active_conversations[conversation_id]
    
    return {
        "conversation_id": conversation_id,
        "summary": conversation.get("summary", "")
    }

@router.get("/{conversation_id}/visualization")
async def get_conversation_visualization(conversation_id: str):
    """获取对话可视化建议"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    conversation = active_conversations[conversation_id]
    
    return {
        "conversation_id": conversation_id,
        "visualization": conversation.get("visualization", {})
    }

# 后台对话处理
async def run_conversation_background(
    conversation_id: str,
    query: str,
    entities: List[Entity],
    autogen_service: AutoGenService,
    cancellation_token: CancellationToken,
    history: List[str] = None
):
    """后台运行对话任务"""
    try:
        # 更新对话状态
        active_conversations[conversation_id]["status"] = "processing"
        
        # 运行对话
        result = await autogen_service.run_conversation(
            query, 
            entities, 
            history, 
            cancellation_token
        )
        
        # 更新对话内容
        if not cancellation_token.cancelled:
            active_conversations[conversation_id]["status"] = "completed"
            
            # 添加对话消息
            for message in result.get("conversation", []):
                if message not in active_conversations[conversation_id]["messages"]:
                    active_conversations[conversation_id]["messages"].append(message)
            
            # 更新关系
            active_conversations[conversation_id]["relationships"] = result.get("relationships", [])
            
            # 更新总结
            active_conversations[conversation_id]["summary"] = result.get("summary", "")
            
            # 更新可视化建议
            active_conversations[conversation_id]["visualization"] = result.get("visualization_suggestions", {})
        else:
            # 如果被取消，更新状态
            active_conversations[conversation_id]["status"] = "cancelled"
            active_conversations[conversation_id]["message"] = "对话已被取消"
        
    except Exception as e:
        logger.error(f"对话运行失败: {str(e)}")
        if conversation_id in active_conversations:
            active_conversations[conversation_id]["status"] = "failed"
            active_conversations[conversation_id]["error"] = str(e)
    finally:
        # 清理取消令牌
        if conversation_id in active_conversations_tokens:
            del active_conversations_tokens[conversation_id] 