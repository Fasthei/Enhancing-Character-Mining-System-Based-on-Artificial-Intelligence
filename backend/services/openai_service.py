from openai import AzureOpenAI
import json
import logging
from typing import List, Dict, Any, Optional
from ..config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_GPT4O_DEPLOYMENT_NAME,
    AZURE_GPT4O_MINI_DEPLOYMENT_NAME,
    RELATIONSHIP_TYPES
)

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
    
    async def extract_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取人物实体"""
        try:
            system_message = """
            你是一个专业的信息提取助手。请从提供的文本中提取所有人物实体信息，包括以下字段(如文本中提及):
            - 姓名(name): 必填
            - 所属领域(domain): 可选
            - 性别(gender): 可选
            - 出生日期(birthDate): 可选
            - 国家(country): 可选
            - 职位(position): 可选
            - 地址(address): 可选
            - 电话(phone): 可选
            - 邮箱(email): 可选
            - 研究领域(researchFields): 可选，列表形式
            - 个人简介(personalDescription): 可选
            - 社交账号(socialAccounts): 可选
            - 工作经历(workExperience): 可选
            - 教育经历(educationExperience): 可选
            - 技能技巧(skills): 可选，列表形式
            - 社会关系(socialRelationships): 可选

            请以JSON数组格式返回结果，每个人物为一个对象。如果文本中没有明确提及某个字段，请不要填写该字段。
            """
            
            response = self.client.chat.completions.create(
                model=AZURE_GPT4O_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("entities", [])
        except Exception as e:
            logger.error(f"提取实体失败: {str(e)}")
            return []
    
    async def extract_relationships(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取文本中实体之间的关系"""
        try:
            # 构建提示
            entity_names = [entity.get("name") for entity in entities if entity.get("name")]
            entity_names_str = ", ".join(entity_names)
            
            strong_keywords = ", ".join(RELATIONSHIP_TYPES["STRONG"]["keywords"])
            weak_keywords = ", ".join(RELATIONSHIP_TYPES["WEAK"]["keywords"])
            
            system_message = f"""
            你是一个专业的关系提取助手。请分析提供的文本，提取以下人物之间的关系: {entity_names_str}

            关系分为两类:
            1. 强关系: 直接指出的关系，如{strong_keywords}。
            2. 弱关系: 间接关系，如{weak_keywords}。

            请以JSON数组格式返回结果，每个关系为一个对象，包含以下字段:
            - source_name: 关系源实体名称
            - target_name: 关系目标实体名称
            - relationship_type: 关系类型，"STRONG"或"WEAK"
            - relationship_description: 关系描述
            - confidence: 关系置信度(0-1之间的小数)
            
            只提取文本中明确提及的实体之间的关系。如果文本中没有提及某两个实体之间的关系，请不要生成该关系。
            """
            
            response = self.client.chat.completions.create(
                model=AZURE_GPT4O_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("relationships", [])
        except Exception as e:
            logger.error(f"提取关系失败: {str(e)}")
            return []
    
    async def analyze_entity_document(self, text: str) -> Dict[str, Any]:
        """分析包含人物信息的文档，提取实体和关系"""
        try:
            # 1. 提取实体
            entities = await self.extract_entities_from_text(text)
            
            # 2. 如果找到实体，提取关系
            relationships = []
            if entities:
                relationships = await self.extract_relationships(text, entities)
            
            return {
                "entities": entities,
                "relationships": relationships
            }
        except Exception as e:
            logger.error(f"分析文档失败: {str(e)}")
            raise 