# Enhancing-Character-Mining-System-Based-on-Artificial-Intelligence

# 人物关系挖掘系统

基于Azure OpenAI、Azure Cosmos DB和Azure AI Search的人物关系挖掘系统。通过AutoGen多智能体框架进行人工智能对话，挖掘人物的强关系和弱关系。

## 系统架构

### 后端服务

- **Azure OpenAI**：提供GPT-4o和GPT-4o mini模型，用于实体提取、关系分析和多智能体对话。
- **Azure Cosmos DB**：存储人物实体和关系数据。
- **Azure AI Search**：建立搜索索引，提供全文搜索和过滤功能。
- **Azure Blob Storage**：存储上传的文件。
- **FastAPI后端**：提供RESTful API接口。
- **AutoGen框架v0.4**：使用Microsoft最新版本的autogen-core、autogen-agentchat和autogen-ext构建多智能体对话系统，包括关系分析师、实体专家、图表可视化师和总结专家。

### 前端界面

- **React**：构建响应式前端界面。
- **Ant Design**：UI组件库。
- **React Force Graph**：人物关系可视化。

## 功能特点

1. **多种数据源支持**：
   - CSV/Excel表格数据
   - Word文档
   - 文本文件

2. **强大的实体提取**：
   - 自动从文档中提取人物实体
   - 支持30+字段的人物信息

3. **智能关系挖掘**：
   - 区分强关系和弱关系
   - 动态调整关系图

4. **多智能体对话**：
   - 关系分析师：分析人物关系模式
   - 实体专家：解释人物实体信息
   - 图表可视化师：提供关系图建议
   - 总结专家：归纳关系发现

5. **交互式关系图**：
   - 使用不同颜色标识关系类型
   - 可调整、缩放和交互

6. **增强版AutoGen功能**：
   - 流式处理对话输出：实时观察AI思考过程
   - 支持取消长时间运行的对话
   - 智能上下文管理：自动处理长对话
   - 对话状态保存与恢复

## 安装部署

### Azure服务配置

1. **创建Azure资源**：
   - Azure OpenAI资源并部署GPT-4o和GPT-4o mini模型
   - Azure Cosmos DB账户
   - Azure AI Search资源
   - Azure Blob Storage账户

2. **AI Search配置**：
   - 创建索引与人物实体字段对应
   - 配置技能组，包括实体识别技能、关键短语提取技能等
   - 设置数据源连接到Cosmos DB

### 后端部署

1. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入Azure服务的密钥和终结点
```

3. 启动服务：
```bash
# 使用模块方式运行
python -m backend.main
```

### 前端部署

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 配置API地址：
```bash
# 创建.env文件
echo "REACT_APP_API_BASE_URL=http://localhost:8000" > .env
```

3. 启动开发服务器：
```bash
npm start
```

4. 构建生产版本：
```bash
npm run build
```

## 使用指南

1. **上传数据**：
   - 通过上传页面上传CSV、Excel、Word或TXT文件
   - 系统会自动提取人物实体

2. **实体管理**：
   - 在实体列表中查看和选择感兴趣的人物实体
   - 筛选特定领域或搜索特定人物

3. **关系可视化**：
   - 查看选定实体的关系图
   - 调整显示强关系或弱关系

4. **智能对话**：
   - 输入问题进行人物关系分析
   - 多智能体团队会分析并发现潜在关系
   - 实时观察AI思考过程（流式输出）
   - 可随时取消耗时长的分析
   - 自动更新关系图和提供总结

## 技术详情

- 使用FastAPI构建异步API
- 使用Azure AI Search技能组处理文档
- 使用AutoGen v0.4框架构建多智能体系统
- 利用CancellationToken实现对话取消
- 使用BufferedChatCompletionContext管理长上下文
- 使用React Force Graph实现动态关系图

## Azure配置详情

### 1. Azure OpenAI 配置

#### 配置步骤：
1. 在Azure门户创建OpenAI资源
2. 部署两个模型：
   - **GPT-4o**：部署名称设为`gpt-4o`
   - **GPT-4o mini**：部署名称设为`gpt-4o-mini`
3. 获取API密钥和终结点

#### 环境变量配置：
```
AZURE_OPENAI_API_KEY=你的API密钥
AZURE_OPENAI_ENDPOINT=https://你的资源名称.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_GPT4O_DEPLOYMENT_NAME=gpt-4o
AZURE_GPT4O_MINI_DEPLOYMENT_NAME=gpt-4o-mini
```

### 2. Azure Cosmos DB 配置

#### 配置步骤：
1. 创建Cosmos DB账户（选择NoSQL API）
2. 创建数据库`RelationshipMining`
3. 创建两个容器：
   - **Entities容器**：
     - 名称：`Entities`
     - 分区键：`/name`
   - **Relationships容器**：
     - 名称：`Relationships`
     - 分区键：`/source_id`

#### 环境变量配置：
```
COSMOS_ENDPOINT=https://你的cosmosdb账户.documents.azure.com:443/
COSMOS_KEY=你的cosmos访问密钥
COSMOS_DATABASE=RelationshipMining
COSMOS_ENTITIES_CONTAINER=Entities
COSMOS_RELATIONSHIPS_CONTAINER=Relationships
```

### 3. Azure AI Search 配置

#### 配置步骤：
1. 创建AI Search资源
2. 配置索引`person-relationships`
3. 创建数据源连接到Cosmos DB
4. 配置技能组`relationship-mining-skillset`
5. 创建索引器

#### 索引字段配置详情：
索引包含所有实体字段（共35个字段）：

| 字段名 | 字段类型 | 属性 | 说明 |
|-------|----------|------|------|
| id | String | 键字段，可过滤 | 实体ID |
| name | String | 可搜索，可过滤，可排序 | 人物姓名 |
| domain | String | 可搜索，可过滤 | 所属领域 |
| gender | String | 可搜索，可过滤 | 性别 |
| birthDate | String | 可搜索 | 出生日期 |
| country | String | 可搜索，可过滤 | 国家 |
| position | String | 可搜索，可过滤 | 职位 |
| address | String | 可搜索 | 地址 |
| phone | String | 可搜索 | 电话 |
| email | String | 可搜索 | 邮箱 |
| fax | String | 可搜索 | 传真 |
| idCard | String | 可搜索 | 身份证 |
| passportNumber | String | 可搜索 | 护照号 |
| researchFields | String集合 | 可搜索，可过滤 | 研究领域 |
| personalDescription | String | 可搜索 | 个人简介 |
| weiboUrl | String | 可搜索 | 微博地址 |
| socialAccounts | String | 可搜索 | 社交账号 |
| familyStatus | String | 可搜索 | 家庭状况 |
| socialRelationships | String | 可搜索 | 社会关系 |
| workExperience | String | 可搜索 | 工作经历 |
| educationExperience | String | 可搜索 | 教育经历 |
| skills | String集合 | 可搜索，可过滤 | 技能技巧 |
| volunteerExperience | String | 可搜索 | 志愿者经历 |
| languages | String集合 | 可搜索，可过滤 | 掌握语言 |
| personalHonors | String集合 | 可搜索 | 个人荣誉 |
| publications | String | 可搜索 | 出版物 |
| patents | String | 可搜索 | 专利 |
| projects | String | 可搜索 | 项目 |
| certificates | String集合 | 可搜索 | 证书 |
| relatedPersons | String集合 | 可搜索，可过滤 | 关系人 |
| academicAchievements | String | 可搜索 | 学术成果 |
| politicalStance | String | 可搜索，可过滤 | 政治立场 |
| socialActivities | String | 可搜索 | 社会活动 |
| chinaRelated | String | 可搜索 | 涉华相关 |
| relatedUrls | String集合 | 可搜索 | 相关URL |
| notes | String | 可搜索 | 备注 |

#### 关系字段（复杂字段）配置：
```
relationships（复杂字段）包含以下子字段：
  - target_id（String）：可过滤
  - target_name（String）：可搜索，可过滤
  - relationship_type（String）：可过滤，"STRONG"或"WEAK"
  - relationship_description（String）：可搜索
  - confidence（Double）：可过滤，可排序，关系置信度
```

#### 技能组配置：
1. **实体识别技能**（EntityRecognitionSkill）：
   - 输入：文本内容和语言代码
   - 输出：人物、组织和地点实体
   - 类别：Person, Organization, Location
   - 默认语言：中文(zh-CN)

2. **关键短语提取技能**（KeyPhraseExtractionSkill）：
   - 输入：文本内容和语言代码
   - 输出：关键短语
   - 默认语言：中文(zh-CN)

3. **文本拆分技能**（SplitSkill）：
   - 模式：pages
   - 最大页面长度：5000
   - 输入：文本内容
   - 输出：文本片段

4. **自定义关系提取技能**（WebApiSkill）：
   - 需要创建Azure Function：
     - 端点：`https://your-function-app.azurewebsites.net/api/ExtractRelationships`
     - 方法：POST
     - 输入：人物、组织和文本内容
     - 输出：关系

### 4. Azure Blob Storage 配置

#### 配置步骤：
1. 创建存储账户
2. 创建Blob容器`documents`用于存储上传的文件

#### 环境变量配置：
```
AZURE_STORAGE_CONNECTION_STRING=你的存储账户连接字符串
AZURE_STORAGE_CONTAINER=documents
```

### 5. 关系类型定义

系统定义的关系类型：

#### 强关系（红色线条）
关键词包括：认识、亲戚、朋友、夫妻、兄弟、姐妹、父母、子女、同学、密友

#### 弱关系（蓝色线条）
关键词包括：同事、同公司、合作、项目伙伴、同行业、同领域、联系人

### 6. Azure Function部署（关系提取）

需要创建一个Azure Function用于实现关系提取功能，该函数会被AI Search的WebApiSkill调用。

函数应实现以下功能：
1. 接收AI Search传来的人物实体、组织实体和文本内容
2. 分析文本，识别实体间的关系
3. 区分强关系和弱关系
4. 返回关系数据