from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, 
    SimpleField, 
    SearchableField, 
    ComplexField,
    SearchFieldDataType,
    SearchIndexer, 
    SearchIndexerDataSourceConnection,
    SearchIndexerSkillset,
    OcrSkill,
    EntityRecognitionSkill,
    KeyPhraseExtractionSkill,
    SplitSkill,
    WebApiSkill
)
from azure.core.credentials import AzureKeyCredential
from ..config.settings import (
    AZURE_SEARCH_ENDPOINT, 
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME,
    AZURE_SEARCH_SKILLSET_NAME,
    COSMOS_ENDPOINT,
    COSMOS_KEY,
    COSMOS_DATABASE,
    COSMOS_ENTITIES_CONTAINER,
    ENTITY_FIELDS
)
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AISearchService:
    def __init__(self):
        self.credential = AzureKeyCredential(AZURE_SEARCH_KEY)
        self.index_client = SearchIndexClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            credential=self.credential
        )
        self.search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            credential=self.credential,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
    
    def initialize_search_service(self):
        """初始化Azure AI Search服务"""
        try:
            # 1. 创建索引
            self._create_index()
            
            # 2. 创建数据源连接
            self._create_data_source()
            
            # 3. 创建技能组
            self._create_skillset()
            
            # 4. 创建索引器
            self._create_indexer()
            
            return True
        except Exception as e:
            logger.error(f"初始化AI Search失败: {str(e)}")
            return False
    
    def _create_index(self):
        """创建或更新索引"""
        try:
            # 定义索引字段
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
                SearchableField(name="name", type=SearchFieldDataType.String, filterable=True, sortable=True),
                SearchableField(name="domain", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="gender", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="birthDate", type=SearchFieldDataType.String),
                SearchableField(name="country", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="position", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="address", type=SearchFieldDataType.String),
                SearchableField(name="phone", type=SearchFieldDataType.String),
                SearchableField(name="email", type=SearchFieldDataType.String),
                SearchableField(name="fax", type=SearchFieldDataType.String),
                SearchableField(name="idCard", type=SearchFieldDataType.String),
                SearchableField(name="passportNumber", type=SearchFieldDataType.String),
                SearchableField(name="researchFields", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
                SearchableField(name="personalDescription", type=SearchFieldDataType.String),
                SearchableField(name="weiboUrl", type=SearchFieldDataType.String),
                SearchableField(name="socialAccounts", type=SearchFieldDataType.String),
                SearchableField(name="familyStatus", type=SearchFieldDataType.String),
                SearchableField(name="socialRelationships", type=SearchFieldDataType.String),
                SearchableField(name="workExperience", type=SearchFieldDataType.String),
                SearchableField(name="educationExperience", type=SearchFieldDataType.String),
                SearchableField(name="skills", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
                SearchableField(name="volunteerExperience", type=SearchFieldDataType.String),
                SearchableField(name="languages", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
                SearchableField(name="personalHonors", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                SearchableField(name="publications", type=SearchFieldDataType.String),
                SearchableField(name="patents", type=SearchFieldDataType.String),
                SearchableField(name="projects", type=SearchFieldDataType.String),
                SearchableField(name="certificates", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                SearchableField(name="relatedPersons", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
                SearchableField(name="academicAchievements", type=SearchFieldDataType.String),
                SearchableField(name="politicalStance", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="socialActivities", type=SearchFieldDataType.String),
                SearchableField(name="chinaRelated", type=SearchFieldDataType.String),
                SearchableField(name="relatedUrls", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                SearchableField(name="notes", type=SearchFieldDataType.String),
                ComplexField(name="relationships", fields=[
                    SimpleField(name="target_id", type=SearchFieldDataType.String),
                    SearchableField(name="target_name", type=SearchFieldDataType.String, filterable=True),
                    SimpleField(name="relationship_type", type=SearchFieldDataType.String, filterable=True),
                    SearchableField(name="relationship_description", type=SearchFieldDataType.String),
                    SimpleField(name="confidence", type=SearchFieldDataType.Double, filterable=True, sortable=True)
                ])
            ]
            
            # 创建索引定义
            index = SearchIndex(name=AZURE_SEARCH_INDEX_NAME, fields=fields)
            
            # 创建或更新索引
            self.index_client.create_or_update_index(index)
            logger.info(f"索引 {AZURE_SEARCH_INDEX_NAME} 创建或更新成功")
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            raise
    
    def _create_data_source(self):
        """创建数据源连接到Cosmos DB"""
        try:
            data_source_connection = SearchIndexerDataSourceConnection(
                name=f"{AZURE_SEARCH_INDEX_NAME}-datasource",
                type="cosmosdb",
                connection_string=f"AccountEndpoint={COSMOS_ENDPOINT};AccountKey={COSMOS_KEY};Database={COSMOS_DATABASE}",
                container={"name": COSMOS_ENTITIES_CONTAINER}
            )
            
            self.index_client.create_or_update_data_source_connection(data_source_connection)
            logger.info(f"数据源连接 {data_source_connection.name} 创建或更新成功")
        except Exception as e:
            logger.error(f"创建数据源连接失败: {str(e)}")
            raise
    
    def _create_skillset(self):
        """创建技能组"""
        try:
            # 定义技能组合
            skills = [
                # 实体识别技能
                EntityRecognitionSkill(
                    name="entity-recognition",
                    description="从文本中提取人物、组织和地点等实体",
                    context="/document",
                    inputs=[
                        {"name": "text", "source": "/document/content"},
                        {"name": "languageCode", "source": "/document/languageCode"}
                    ],
                    outputs=[
                        {"name": "persons", "targetName": "persons"},
                        {"name": "organizations", "targetName": "organizations"},
                        {"name": "locations", "targetName": "locations"}
                    ],
                    categories=["Person", "Organization", "Location"],
                    default_language_code="zh-CN"
                ),
                
                # 关键短语提取技能
                KeyPhraseExtractionSkill(
                    name="key-phrase-extraction",
                    description="从文本中提取关键短语",
                    context="/document",
                    inputs=[
                        {"name": "text", "source": "/document/content"},
                        {"name": "languageCode", "source": "/document/languageCode"}
                    ],
                    outputs=[
                        {"name": "keyPhrases", "targetName": "keyPhrases"}
                    ],
                    default_language_code="zh-CN"
                ),
                
                # 文本拆分技能(用于处理长文档)
                SplitSkill(
                    name="text-splitter",
                    description="将长文本拆分为小段",
                    context="/document",
                    text_split_mode="pages",
                    maximum_page_length=5000,
                    inputs=[
                        {"name": "text", "source": "/document/content"}
                    ],
                    outputs=[
                        {"name": "textItems", "targetName": "pages"}
                    ]
                ),
                
                # 自定义关系提取技能(这需要一个Web API端点来处理关系提取)
                WebApiSkill(
                    name="relationship-extractor",
                    description="提取人物之间的关系",
                    context="/document",
                    uri="https://your-function-app.azurewebsites.net/api/ExtractRelationships",
                    http_method="POST",
                    timeout="PT30S",
                    batch_size=1,
                    inputs=[
                        {"name": "persons", "source": "/document/persons"},
                        {"name": "organizations", "source": "/document/organizations"},
                        {"name": "text", "source": "/document/content"}
                    ],
                    outputs=[
                        {"name": "relationships", "targetName": "relationships"}
                    ]
                )
            ]
            
            # 创建技能组
            skillset = SearchIndexerSkillset(
                name=AZURE_SEARCH_SKILLSET_NAME,
                description="人物关系挖掘技能组",
                skills=skills
            )
            
            self.index_client.create_or_update_skillset(skillset)
            logger.info(f"技能组 {AZURE_SEARCH_SKILLSET_NAME} 创建或更新成功")
        except Exception as e:
            logger.error(f"创建技能组失败: {str(e)}")
            raise
    
    def _create_indexer(self):
        """创建索引器，将数据源和技能组关联到索引"""
        try:
            # 创建字段映射
            field_mappings = [
                {"sourceFieldName": "id", "targetFieldName": "id"},
            ]
            
            # 为每个实体字段创建映射
            for field in ENTITY_FIELDS:
                field_mappings.append({
                    "sourceFieldName": field, 
                    "targetFieldName": field
                })
            
            # 创建输出字段映射(用于将技能组输出映射到索引字段)
            output_field_mappings = [
                {
                    "sourceFieldName": "/document/relationships",
                    "targetFieldName": "relationships"
                }
            ]
            
            # 创建索引器
            indexer = SearchIndexer(
                name=f"{AZURE_SEARCH_INDEX_NAME}-indexer",
                description="人物关系数据索引器",
                skillset_name=AZURE_SEARCH_SKILLSET_NAME,
                data_source_name=f"{AZURE_SEARCH_INDEX_NAME}-datasource",
                target_index_name=AZURE_SEARCH_INDEX_NAME,
                field_mappings=field_mappings,
                output_field_mappings=output_field_mappings,
                parameters={
                    "configuration": {
                        "dataToExtract": "contentAndMetadata",
                        "parsingMode": "default"
                    }
                }
            )
            
            self.index_client.create_or_update_indexer(indexer)
            logger.info(f"索引器 {indexer.name} 创建或更新成功")
        except Exception as e:
            logger.error(f"创建索引器失败: {str(e)}")
            raise
    
    def search_entities(self, search_text: str, filter_condition: str = None, top: int = 50) -> List[Dict[str, Any]]:
        """搜索实体"""
        try:
            # 执行搜索
            results = self.search_client.search(
                search_text=search_text,
                filter=filter_condition,
                top=top,
                include_total_count=True
            )
            
            # 转换结果
            entities = []
            for result in results:
                entity = dict(result)
                entities.append(entity)
                
            return entities
        except Exception as e:
            logger.error(f"搜索实体失败: {str(e)}")
            raise 