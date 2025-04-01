import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
import json

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.groupchat import GroupChat, GroupChatManager
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.cache import ChatCompletionCache
from autogen_ext.cache_store.diskcache import DiskCacheStore
from diskcache import Cache

from ..config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_GPT4O_DEPLOYMENT_NAME,
    AZURE_GPT4O_MINI_DEPLOYMENT_NAME
)
from ..models.entity import Entity, Relationship

logger = logging.getLogger(__name__)

class AutoGenService:
    def __init__(self):
        # 初始化智能体
        self.initialize_agents()
        self._cache = None  # 懒加载缓存
    
    def _get_or_create_cache(self):
        """懒加载模型缓存"""
        if self._cache is None:
            import os
            # 确保缓存目录存在
            cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            cache_store = DiskCacheStore(Cache(cache_dir))
            self._cache = cache_store
        return self._cache
    
    def initialize_agents(self):
        """初始化智能体组"""
        # 配置 GPT-4o
        self.gpt4o_model = OpenAIChatCompletionClient(
            model=AZURE_GPT4O_DEPLOYMENT_NAME,
            api_key=AZURE_OPENAI_API_KEY,
            api_base=AZURE_OPENAI_ENDPOINT,
            api_type="azure",
            api_version=AZURE_OPENAI_API_VERSION
        )
        
        # 添加缓存支持
        cache_store = self._get_or_create_cache()
        self.cached_model = ChatCompletionCache(self.gpt4o_model, cache_store)
        
        # 配置 GPT-4o mini
        self.gpt4o_mini_model = OpenAIChatCompletionClient(
            model=AZURE_GPT4O_MINI_DEPLOYMENT_NAME,
            api_key=AZURE_OPENAI_API_KEY,
            api_base=AZURE_OPENAI_ENDPOINT,
            api_type="azure",
            api_version=AZURE_OPENAI_API_VERSION
        )
        
        # 创建智能体
        self.user_proxy = UserProxyAgent(
            name="用户代理",
            system_message="你是用户的代理，负责将用户问题传达给助手团队，并整理他们的回答。",
            human_input_mode="NEVER"
        )
        
        # 使用BufferedChatCompletionContext管理上下文长度
        buffer_size = 20  # 保留最近20条消息
        
        self.relationship_analyst = AssistantAgent(
            name="关系分析师",
            system_message="""你是一位专业的人物关系分析师。你的职责是分析人物之间的关系模式，识别强关系和弱关系。
            强关系是指文本中明确指出的直接关系，如亲戚、朋友、夫妻等。
            弱关系是指间接关系，如同事、同学、同一组织的成员等。
            请基于提供的信息和对话内容，深入分析人物关系网络，并提供有见地的分析。""",
            model=self.cached_model,
            model_context=BufferedChatCompletionContext(buffer_size=buffer_size)
        )
        
        self.entity_specialist = AssistantAgent(
            name="实体专家",
            system_message="""你是一位实体信息专家。你的职责是理解和解释人物实体的各种属性和背景信息。
            你需要关注人物的背景、职业、技能、教育等方面的信息，并根据这些信息推断潜在的关系网络。
            请提供详细而准确的实体信息分析，支持关系分析师的工作。""",
            model=self.gpt4o_mini_model,
            model_context=BufferedChatCompletionContext(buffer_size=buffer_size)
        )
        
        self.graph_visualizer = AssistantAgent(
            name="图表可视化师",
            system_message="""你是一位图表可视化专家。你的职责是提出关系图的可视化建议。
            你需要考虑如何最有效地展示强关系和弱关系，包括使用不同的线条颜色、粗细、节点大小等视觉元素。
            请根据对话内容，提出如何动态调整关系图以反映新发现的关系。""",
            model=self.gpt4o_mini_model,
            model_context=BufferedChatCompletionContext(buffer_size=buffer_size)
        )
        
        self.summary_agent = AssistantAgent(
            name="总结专家",
            system_message="""你是一位信息总结专家。你的职责是对关系分析结果和对话内容进行简明扼要的总结。
            请提取关键信息，特别是新发现的强关系和弱关系，以及这些关系的重要性。
            你的总结应当清晰、结构化，便于用户理解复杂的关系网络。""",
            model=self.gpt4o_mini_model,
            model_context=BufferedChatCompletionContext(buffer_size=buffer_size)
        )
    
    async def run_conversation_stream(self, query: str, entities: List[Entity], 
                               history: List[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """运行带流式输出的多智能体对话"""
        try:
            # 准备实体数据
            entities_data = [entity.dict() for entity in entities]
            entities_json = json.dumps(entities_data, ensure_ascii=False, indent=2)
            
            # 准备历史对话
            history_text = "\n".join(history) if history else ""
            
            # 构建初始消息
            initial_message = f"""
            ## 用户查询
            {query}
            
            ## 人物实体数据
            {entities_json}
            
            ## 历史对话
            {history_text}
            
            请分析这些人物之间的关系，识别强关系和弱关系，并根据对话内容动态调整关系图的建议。
            """
            
            # 创建取消令牌
            cancellation_token = CancellationToken()
            
            # 使用流式API
            user_message = TextMessage(content=initial_message, source="user")
            async for message in self.relationship_analyst.on_messages_stream(
                [user_message], 
                cancellation_token
            ):
                yield {
                    "type": "message",
                    "sender": "关系分析师",
                    "content": message.content
                }
            
            # 创建群聊
            group_chat = GroupChat(
                agents=[self.relationship_analyst, self.entity_specialist, self.graph_visualizer, self.summary_agent, self.user_proxy],
                messages=[],
            )
            group_chat_manager = GroupChatManager(group_chat, max_round=10)
            
            # 群聊流式处理
            team_message = "请对以上信息进行团队分析，识别所有可能的强关系和弱关系，并提供关系图可视化建议和总结。"
            async for message in group_chat_manager.run_stream(
                task=team_message,
                cancellation_token=cancellation_token
            ):
                yield {
                    "type": "message",
                    "sender": message.source,
                    "content": message.content
                }
                
            # 请求总结
            summary_task = "请总结我们的对话，特别是新发现的关系和关系图的调整建议。"
            async for message in self.summary_agent.on_messages_stream(
                [TextMessage(content=summary_task, source="user")],
                cancellation_token
            ):
                yield {
                    "type": "summary",
                    "content": message.content
                }
                
        except Exception as e:
            logger.error(f"运行对话失败: {str(e)}")
            yield {
                "type": "error",
                "content": f"处理失败: {str(e)}"
            }
    
    async def run_conversation(self, query: str, entities: List[Entity], 
                              history: List[str] = None, 
                              cancellation_token: Optional[CancellationToken] = None) -> Dict[str, Any]:
        """运行多智能体对话，分析人物关系"""
        try:
            # 如果没有提供取消令牌，创建一个新的
            if cancellation_token is None:
                cancellation_token = CancellationToken()
                
            # 准备实体数据
            entities_data = [entity.dict() for entity in entities]
            entities_json = json.dumps(entities_data, ensure_ascii=False, indent=2)
            
            # 准备历史对话
            history_text = "\n".join(history) if history else ""
            
            # 构建初始消息
            initial_message = f"""
            ## 用户查询
            {query}
            
            ## 人物实体数据
            {entities_json}
            
            ## 历史对话
            {history_text}
            
            请分析这些人物之间的关系，识别强关系和弱关系，并根据对话内容动态调整关系图的建议。
            """
            
            # 初始化结果变量
            result = {
                "conversation": [],
                "relationships": [],
                "summary": "",
                "visualization_suggestions": {}
            }
            
            # 创建消息捕获回调
            async def capture_messages(sender, recipient, message):
                result["conversation"].append({
                    "sender": sender.name,
                    "recipient": recipient.name,
                    "message": message.content if hasattr(message, 'content') else str(message)
                })
                return False
            
            # 设置消息回调
            for agent in [self.relationship_analyst, self.entity_specialist, self.graph_visualizer, self.summary_agent]:
                agent.register_message_callback(capture_messages)
            self.user_proxy.register_message_callback(capture_messages)
            
            # 启动对话
            response = await self.user_proxy.send_message(
                message=initial_message,
                to=self.relationship_analyst,
                cancellation_token=cancellation_token
            )
            
            # 创建群聊
            group_chat = GroupChat(
                agents=[self.relationship_analyst, self.entity_specialist, self.graph_visualizer, self.summary_agent, self.user_proxy],
                messages=[],
            )
            group_chat_manager = GroupChatManager(group_chat, max_round=10)
            
            # 开始群聊分析
            await self.user_proxy.send_message(
                message="请对以上信息进行团队分析，识别所有可能的强关系和弱关系，并提供关系图可视化建议和总结。",
                to=group_chat_manager,
                cancellation_token=cancellation_token
            )
            
            # 请求总结
            summary_response = await self.user_proxy.send_message(
                message="请总结我们的对话，特别是新发现的关系和关系图的调整建议。",
                to=self.summary_agent,
                cancellation_token=cancellation_token
            )
            
            # 提取关系信息和可视化建议
            for conv in result["conversation"]:
                # 提取关系分析师的关系发现
                if conv["sender"] == "关系分析师" and "关系" in conv["message"]:
                    # 解析关系信息
                    for entity in entities:
                        entity_name = entity.name
                        if entity_name in conv["message"]:
                            # 尝试提取关系描述
                            lines = conv["message"].split("\n")
                            for line in lines:
                                if entity_name in line and "关系" in line:
                                    parts = line.split(":")
                                    if len(parts) > 1:
                                        relationship_desc = parts[1].strip()
                                        result["relationships"].append({
                                            "source": entity_name,
                                            "description": relationship_desc
                                        })
                
                # 提取图表可视化师的建议
                if conv["sender"] == "图表可视化师":
                    # 尝试提取可视化建议
                    if "建议" in conv["message"] or "可视化" in conv["message"]:
                        result["visualization_suggestions"] = {
                            "suggestion": conv["message"]
                        }
                
                # 提取总结专家的总结
                if conv["sender"] == "总结专家" and conv["recipient"] == "用户代理":
                    result["summary"] = conv["message"]
            
            # 如果没有获取到总结，使用最后一条总结消息
            if not result["summary"] and summary_response:
                result["summary"] = summary_response.content if hasattr(summary_response, 'content') else str(summary_response)
            
            return result
        except Exception as e:
            logger.error(f"运行对话失败: {str(e)}")
            raise

    async def save_conversation_state(self, file_path: str) -> None:
        """保存对话状态到文件"""
        from autogen_agentchat.serialize import serialize_agent
        
        state = {
            "relationship_analyst": serialize_agent(self.relationship_analyst),
            "entity_specialist": serialize_agent(self.entity_specialist),
            "graph_visualizer": serialize_agent(self.graph_visualizer),
            "summary_agent": serialize_agent(self.summary_agent),
            "user_proxy": serialize_agent(self.user_proxy)
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            
    async def load_conversation_state(self, file_path: str) -> None:
        """从文件加载对话状态"""
        from autogen_agentchat.serialize import deserialize_agent
        
        with open(file_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        # 重新创建智能体但保留历史记录
        buffer_size = 20
        self.relationship_analyst = deserialize_agent(
            state["relationship_analyst"], 
            model=self.cached_model,
            model_context=BufferedChatCompletionContext(buffer_size=buffer_size)
        )
        self.entity_specialist = deserialize_agent(
            state["entity_specialist"], 
            model=self.gpt4o_mini_model,
            model_context=BufferedChatCompletionContext(buffer_size=buffer_size)
        )
        self.graph_visualizer = deserialize_agent(
            state["graph_visualizer"], 
            model=self.gpt4o_mini_model,
            model_context=BufferedChatCompletionContext(buffer_size=buffer_size)
        )
        self.summary_agent = deserialize_agent(
            state["summary_agent"], 
            model=self.gpt4o_mini_model,
            model_context=BufferedChatCompletionContext(buffer_size=buffer_size)
        )
        self.user_proxy = deserialize_agent(
            state["user_proxy"]
        ) 