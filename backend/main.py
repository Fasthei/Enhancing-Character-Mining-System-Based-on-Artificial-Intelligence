from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .api import entity_routes, file_routes, conversation_routes
from .services.cosmos_service import CosmosDBService
from .services.ai_search_service import AISearchService
import logging
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="人物关系挖掘系统API",
    description="基于Azure OpenAI、Cosmos DB和AI Search的人物关系挖掘系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应当指定确切的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(entity_routes.router)
app.include_router(file_routes.router)
app.include_router(conversation_routes.router)

# 依赖项
def get_cosmos_service():
    return CosmosDBService()

def get_search_service():
    return AISearchService()

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    # 初始化数据库
    cosmos_service = get_cosmos_service()
    if cosmos_service.initialize_database():
        logger.info("Cosmos DB 初始化成功")
    else:
        logger.error("Cosmos DB 初始化失败")
    
    # 初始化搜索服务
    search_service = get_search_service()
    if search_service.initialize_search_service():
        logger.info("AI Search 初始化成功")
    else:
        logger.error("AI Search 初始化失败")

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 主入口
if __name__ == "__main__":
    # 使用相对导入路径时需要使用Python模块方式运行
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True) 