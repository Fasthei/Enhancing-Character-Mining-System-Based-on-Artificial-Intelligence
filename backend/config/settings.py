import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Azure OpenAI配置
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_GPT4O_DEPLOYMENT_NAME = os.getenv("AZURE_GPT4O_DEPLOYMENT_NAME")
AZURE_GPT4O_MINI_DEPLOYMENT_NAME = os.getenv("AZURE_GPT4O_MINI_DEPLOYMENT_NAME")

# Azure Cosmos DB配置
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE")
COSMOS_ENTITIES_CONTAINER = os.getenv("COSMOS_ENTITIES_CONTAINER")
COSMOS_RELATIONSHIPS_CONTAINER = os.getenv("COSMOS_RELATIONSHIPS_CONTAINER")

# Azure AI Search配置
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
AZURE_SEARCH_SKILLSET_NAME = os.getenv("AZURE_SEARCH_SKILLSET_NAME")

# Azure Blob Storage配置
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER")

# 人物实体字段映射
ENTITY_FIELDS = [
    "domain", "name", "photo", "gender", "birthDate", "country", "position", 
    "address", "phone", "email", "fax", "idCard", "passportNumber", 
    "researchFields", "personalDescription", "weiboUrl", "socialAccounts", 
    "familyStatus", "socialRelationships", "workExperience", "educationExperience", 
    "skills", "volunteerExperience", "languages", "personalHonors", "publications", 
    "patents", "projects", "certificates", "relatedPersons", "academicAchievements", 
    "politicalStance", "socialActivities", "chinaRelated", "relatedUrls", "notes"
]

# 关系类型定义
RELATIONSHIP_TYPES = {
    "STRONG": {
        "color": "red",
        "keywords": ["认识", "亲戚", "朋友", "夫妻", "兄弟", "姐妹", "父母", "子女", "同学", "密友"]
    },
    "WEAK": {
        "color": "blue",
        "keywords": ["同事", "同公司", "合作", "项目伙伴", "同行业", "同领域", "联系人"]
    }
} 