from azure.cosmos import CosmosClient, exceptions
from ..config.settings import (
    COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE,
    COSMOS_ENTITIES_CONTAINER, COSMOS_RELATIONSHIPS_CONTAINER
)
from ..models.entity import Entity, Relationship
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CosmosDBService:
    def __init__(self):
        self.client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
        self.database = self.client.get_database_client(COSMOS_DATABASE)
        self.entities_container = self.database.get_container_client(COSMOS_ENTITIES_CONTAINER)
        self.relationships_container = self.database.get_container_client(COSMOS_RELATIONSHIPS_CONTAINER)
    
    def initialize_database(self):
        """初始化数据库和容器"""
        try:
            # 创建数据库(如果不存在)
            try:
                self.database = self.client.create_database(COSMOS_DATABASE)
                logger.info(f"创建数据库 {COSMOS_DATABASE} 成功")
            except exceptions.CosmosResourceExistsError:
                self.database = self.client.get_database_client(COSMOS_DATABASE)
                logger.info(f"数据库 {COSMOS_DATABASE} 已存在")
            
            # 创建实体容器(如果不存在)
            try:
                self.entities_container = self.database.create_container(
                    id=COSMOS_ENTITIES_CONTAINER,
                    partition_key="/name"
                )
                logger.info(f"创建容器 {COSMOS_ENTITIES_CONTAINER} 成功")
            except exceptions.CosmosResourceExistsError:
                self.entities_container = self.database.get_container_client(COSMOS_ENTITIES_CONTAINER)
                logger.info(f"容器 {COSMOS_ENTITIES_CONTAINER} 已存在")
            
            # 创建关系容器(如果不存在)
            try:
                self.relationships_container = self.database.create_container(
                    id=COSMOS_RELATIONSHIPS_CONTAINER,
                    partition_key="/source_id"
                )
                logger.info(f"创建容器 {COSMOS_RELATIONSHIPS_CONTAINER} 成功")
            except exceptions.CosmosResourceExistsError:
                self.relationships_container = self.database.get_container_client(COSMOS_RELATIONSHIPS_CONTAINER)
                logger.info(f"容器 {COSMOS_RELATIONSHIPS_CONTAINER} 已存在")
                
            return True
        except Exception as e:
            logger.error(f"初始化数据库失败: {str(e)}")
            return False
    
    def create_entity(self, entity: Entity) -> Dict[str, Any]:
        """创建一个新的实体"""
        try:
            return self.entities_container.create_item(entity.dict())
        except Exception as e:
            logger.error(f"创建实体失败: {str(e)}")
            raise
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """根据ID获取实体"""
        try:
            query = f"SELECT * FROM c WHERE c.id = @id"
            params = [{"name": "@id", "value": entity_id}]
            items = list(self.entities_container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            if items:
                return Entity(**items[0])
            return None
        except Exception as e:
            logger.error(f"获取实体失败: {str(e)}")
            raise
    
    def update_entity(self, entity_id: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新实体信息"""
        try:
            # 先获取当前实体
            item = self.get_entity(entity_id)
            if not item:
                raise ValueError(f"实体 {entity_id} 不存在")
            
            # 更新字段
            item_dict = item.dict()
            item_dict.update(entity_data)
            
            # 保存更新后的实体
            return self.entities_container.upsert_item(item_dict)
        except Exception as e:
            logger.error(f"更新实体失败: {str(e)}")
            raise
    
    def delete_entity(self, entity_id: str) -> None:
        """删除实体"""
        try:
            item = self.get_entity(entity_id)
            if not item:
                raise ValueError(f"实体 {entity_id} 不存在")
                
            self.entities_container.delete_item(item.id, partition_key=item.name)
        except Exception as e:
            logger.error(f"删除实体失败: {str(e)}")
            raise
    
    def list_entities(self, query_filter: str = None) -> List[Entity]:
        """列出所有实体，可选过滤条件"""
        try:
            if query_filter:
                query = f"SELECT * FROM c WHERE {query_filter}"
            else:
                query = "SELECT * FROM c"
                
            items = list(self.entities_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return [Entity(**item) for item in items]
        except Exception as e:
            logger.error(f"列出实体失败: {str(e)}")
            raise
    
    def add_relationship(self, source_id: str, relationship: Relationship) -> Dict[str, Any]:
        """添加实体之间的关系"""
        try:
            # 更新源实体的关系列表
            source_entity = self.get_entity(source_id)
            if not source_entity:
                raise ValueError(f"源实体 {source_id} 不存在")
            
            # 检查目标实体是否存在
            target_entity = self.get_entity(relationship.target_id)
            if not target_entity:
                raise ValueError(f"目标实体 {relationship.target_id} 不存在")
            
            # 添加关系到源实体
            relationships = source_entity.relationships
            relationship_exists = False
            
            for i, rel in enumerate(relationships):
                if rel.target_id == relationship.target_id:
                    # 更新现有关系
                    relationships[i] = relationship
                    relationship_exists = True
                    break
            
            if not relationship_exists:
                relationships.append(relationship)
            
            # 更新实体
            source_entity.relationships = relationships
            return self.update_entity(source_id, {"relationships": [r.dict() for r in relationships]})
        except Exception as e:
            logger.error(f"添加关系失败: {str(e)}")
            raise
    
    def get_relationships(self, entity_id: str) -> List[Relationship]:
        """获取实体的所有关系"""
        try:
            entity = self.get_entity(entity_id)
            if not entity:
                raise ValueError(f"实体 {entity_id} 不存在")
            return entity.relationships
        except Exception as e:
            logger.error(f"获取关系失败: {str(e)}")
            raise 