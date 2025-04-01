import pandas as pd
import docx
from io import BytesIO
import logging
from typing import List, Dict, Any, Tuple
from azure.storage.blob import BlobServiceClient
from ..config.settings import AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER
from ..models.entity import Entity

logger = logging.getLogger(__name__)

class FileProcessor:
    def __init__(self):
        # 初始化Blob Storage客户端
        self.blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.container_client = self.blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
        
        # 确保容器存在
        try:
            if not self.container_client.exists():
                self.container_client = self.blob_service_client.create_container(AZURE_STORAGE_CONTAINER)
                logger.info(f"创建容器 {AZURE_STORAGE_CONTAINER} 成功")
        except Exception as e:
            logger.error(f"初始化Blob Storage失败: {str(e)}")
            raise
    
    async def process_file(self, file, file_name: str) -> Tuple[List[Dict[str, Any]], str]:
        """处理上传的文件，根据文件类型调用不同的处理方法"""
        try:
            # 保存文件到Blob Storage
            blob_client = self.container_client.get_blob_client(file_name)
            file_content = await file.read()
            blob_client.upload_blob(file_content, overwrite=True)
            file_url = blob_client.url
            
            # 根据文件扩展名选择不同的处理方法
            file_ext = file_name.lower().split('.')[-1]
            
            if file_ext in ['csv', 'xlsx', 'xls']:
                # 处理表格文件
                entities = await self.process_table_file(BytesIO(file_content), file_ext)
                content_type = "table"
            elif file_ext in ['docx', 'doc']:
                # 处理Word文档
                text_content = await self.process_word_document(BytesIO(file_content))
                entities = []  # 实体将通过AI服务提取，这里先返回空列表
                content_type = "document"
            elif file_ext == 'txt':
                # 处理文本文件
                text_content = file_content.decode('utf-8')
                entities = []  # 实体将通过AI服务提取，这里先返回空列表
                content_type = "document"
            else:
                raise ValueError(f"不支持的文件类型: {file_ext}")
            
            return entities, file_url, content_type
        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            raise
    
    async def process_table_file(self, file_content: BytesIO, file_ext: str) -> List[Dict[str, Any]]:
        """处理表格文件 (CSV或Excel)"""
        try:
            if file_ext == 'csv':
                df = pd.read_csv(file_content)
            else:  # Excel文件
                df = pd.read_excel(file_content)
            
            # 将DataFrame转换为实体列表
            entities = []
            for _, row in df.iterrows():
                entity_data = {}
                for column in df.columns:
                    # 跳过NaN值
                    if pd.notna(row[column]):
                        # 处理列表类型的字段(如研究领域、技能等)
                        if column in ['researchFields', 'skills', 'languages', 'personalHonors', 
                                    'relatedPersons', 'relatedUrls']:
                            if isinstance(row[column], str):
                                entity_data[column] = [item.strip() for item in row[column].split(',')]
                            else:
                                entity_data[column] = [str(row[column])]
                        # 处理复杂字段(如工作经历、教育经历等)
                        elif column in ['workExperience', 'educationExperience', 'volunteerExperience',
                                      'publications', 'patents', 'projects', 'academicAchievements',
                                      'socialActivities']:
                            if isinstance(row[column], str):
                                # 尝试解析为简单列表
                                entity_data[column] = [{"description": item.strip()} for item in row[column].split(';')]
                            else:
                                entity_data[column] = [{"description": str(row[column])}]
                        # 处理社交账号(字典类型)
                        elif column == 'socialAccounts':
                            if isinstance(row[column], str):
                                accounts = {}
                                for account in row[column].split(';'):
                                    if ':' in account:
                                        platform, url = account.split(':', 1)
                                        accounts[platform.strip()] = url.strip()
                                entity_data[column] = accounts
                        else:
                            entity_data[column] = row[column]
                
                # 如果有"name"字段，将创建实体
                if 'name' in entity_data:
                    entity = Entity(**entity_data)
                    entities.append(entity.dict())
            
            return entities
        except Exception as e:
            logger.error(f"处理表格文件失败: {str(e)}")
            raise
    
    async def process_word_document(self, file_content: BytesIO) -> str:
        """处理Word文档，提取文本内容"""
        try:
            doc = docx.Document(file_content)
            text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text_content
        except Exception as e:
            logger.error(f"处理Word文档失败: {str(e)}")
            raise 