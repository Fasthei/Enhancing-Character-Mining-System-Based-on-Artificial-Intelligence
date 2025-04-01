from fastapi import APIRouter, HTTPException, Depends
from ..services.cosmos_service import CosmosDBService
from ..services.ai_search_service import AISearchService
from ..models.entity import Entity, Relationship
import logging
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/entities", tags=["entities"])
logger = logging.getLogger(__name__)

# 服务依赖
def get_cosmos_service():
    return CosmosDBService()

def get_search_service():
    return AISearchService()

@router.get("/")
async def list_entities(
    search_text: Optional[str] = None,
    domain: Optional[str] = None,
    cosmos_service: CosmosDBService = Depends(get_cosmos_service),
    search_service: AISearchService = Depends(get_search_service)
):
    """获取实体列表，支持搜索和过滤"""
    try:
        if search_text:
            # 使用AI Search搜索
            filter_condition = f"domain eq '{domain}'" if domain else None
            entities = search_service.search_entities(search_text, filter_condition)
        else:
            # 直接从Cosmos DB获取
            query_filter = f"c.domain = '{domain}'" if domain else None
            entity_models = cosmos_service.list_entities(query_filter)
            entities = [entity.dict() for entity in entity_models]
        
        return {"entities": entities, "count": len(entities)}
    except Exception as e:
        logger.error(f"列出实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实体列表失败: {str(e)}")

@router.get("/{entity_id}")
async def get_entity(
    entity_id: str,
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """获取单个实体的详细信息"""
    try:
        entity = cosmos_service.get_entity(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail=f"实体 {entity_id} 不存在")
        
        return entity.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实体失败: {str(e)}")

@router.post("/")
async def create_entity(
    entity: Entity,
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """创建新实体"""
    try:
        result = cosmos_service.create_entity(entity)
        return {"id": result["id"], "message": "实体创建成功"}
    except Exception as e:
        logger.error(f"创建实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建实体失败: {str(e)}")

@router.put("/{entity_id}")
async def update_entity(
    entity_id: str,
    entity_data: Dict[str, Any],
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """更新实体信息"""
    try:
        result = cosmos_service.update_entity(entity_id, entity_data)
        return {"id": result["id"], "message": "实体更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新实体失败: {str(e)}")

@router.delete("/{entity_id}")
async def delete_entity(
    entity_id: str,
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """删除实体"""
    try:
        cosmos_service.delete_entity(entity_id)
        return {"message": f"实体 {entity_id} 删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除实体失败: {str(e)}")

@router.get("/{entity_id}/relationships")
async def get_entity_relationships(
    entity_id: str,
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """获取实体的关系列表"""
    try:
        relationships = cosmos_service.get_relationships(entity_id)
        return {"entity_id": entity_id, "relationships": [r.dict() for r in relationships]}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取实体关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实体关系失败: {str(e)}")

@router.post("/{entity_id}/relationships")
async def add_entity_relationship(
    entity_id: str,
    relationship: Relationship,
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """添加实体关系"""
    try:
        result = cosmos_service.add_relationship(entity_id, relationship)
        return {"entity_id": entity_id, "message": "关系添加成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"添加实体关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加实体关系失败: {str(e)}") 