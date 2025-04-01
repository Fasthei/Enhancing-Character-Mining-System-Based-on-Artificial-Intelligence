import autogen
import asyncio
import logging
from typing import List, Dict, Any, Optional
from ..config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_GPT4O_DEPLOYMENT_NAME,
    AZURE_GPT4O_MINI_DEPLOYMENT_NAME
)
from ..models.entity import Entity, Relationship
import json

logger = logging.getLogger(__name__)

class AutoGenService:
    def __init__(self):
        # 配置 OpenAI
        self.config_list = [
            {
                "model": AZURE_GPT4O_DEPLOYMENT_NAME,
                "api_key": AZURE_OPENAI_API_KEY,
                "api_base": AZURE_OPENAI_ENDPOINT,
                "api_type": "azure",
                "api_version": AZURE_OPENAI_API_VERSION
            },
            {
                "model": AZURE_GPT4O_MINI_DEPLOYMENT_NAME,
                "api_key": AZURE_OPENAI_API_KEY,
                "api_base": AZURE_OPENAI_ENDPOINT,
                "api_type": "azure",
                "api_version": AZURE_OPENAI_API_VERSION
            }
        ]
        
        # 初始化智能体
        self.initialize_agents()
    
    def initialize_agents(self):
        """初始化智能体组"""
        # 配置 GPT-4o
        gpt4o_config = {"config_list": [self.config_list[0]]}
        
        # 配置 GPT-4o mini
        gpt4o_mini_config = {"config_list": [self.config_list[1]]}
        
        # 创建智能体
        self.user_proxy = autogen.UserProxyAgent(
            name="用户代理",
            system_message="你是用户的代理，负责将用户问题传达给助手团队，并整理他们的回答。",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: "TERMINATE" in x.get("content")
        )
        
        self.relationship_analyst = autogen.AssistantAgent(
            name="关系分析师",
            system_message="""你是一位专业的人物关系分析师。你的职责是分析人物之间的关系模式，识别强关系和弱关系。
            强关系是指文本中明确指出的直接关系，如亲戚、朋友、夫妻等。
            弱关系是指间接关系，如同事、同学、同一组织的成员等。
            请基于提供的信息和对话内容，深入分析人物关系网络，并提供有见地的分析。""",
            llm_config=gpt4o_config
        )
        
        self.entity_specialist = autogen.AssistantAgent(
            name="实体专家",
            system_message="""你是一位实体信息专家。你的职责是理解和解释人物实体的各种属性和背景信息。
            你需要关注人物的背景、职业、技能、教育等方面的信息，并根据这些信息推断潜在的关系网络。
            请提供详细而准确的实体信息分析，支持关系分析师的工作。""",
            llm_config=gpt4o_mini_config
        )
        
        self.graph_visualizer = autogen.AssistantAgent(
            name="图表可视化师",
            system_message="""你是一位图表可视化专家。你的职责是提出关系图的可视化建议。
            你需要考虑如何最有效地展示强关系和弱关系，包括使用不同的线条颜色、粗细、节点大小等视觉元素。
            请根据对话内容，提出如何动态调整关系图以反映新发现的关系。""",
            llm_config=gpt4o_mini_config
        )
        
        self.summary_agent = autogen.AssistantAgent(
            name="总结专家",
            system_message="""你是一位信息总结专家。你的职责是对关系分析结果和对话内容进行简明扼要的总结。
            请提取关键信息，特别是新发现的强关系和弱关系，以及这些关系的重要性。
            你的总结应当清晰、结构化，便于用户理解复杂的关系网络。""",
            llm_config=gpt4o_mini_config
        )
    
    async def run_conversation(self, query: str, entities: List[Entity], history: List[str] = None) -> Dict[str, Any]:
        """运行多智能体对话，分析人物关系"""
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
            
            # 初始化结果变量
            result = {
                "conversation": [],
                "relationships": [],
                "summary": "",
                "visualization_suggestions": {}
            }
            
            # 设置对话记录回调
            def store_conversation(recipient, messages, sender, config):
                if sender and recipient and messages:
                    for message in messages:
                        result["conversation"].append({
                            "sender": sender.name,
                            "recipient": recipient.name,
                            "message": message.get("content", "")
                        })
                return False, None
            
            # 注册回调
            self.user_proxy.register_reply(
                [self.relationship_analyst, self.entity_specialist, self.graph_visualizer, self.summary_agent],
                store_conversation
            )
            
            # 启动对话
            chat_result = await asyncio.to_thread(
                self.user_proxy.initiate_chat,
                self.relationship_analyst,
                message=initial_message,
                clear_history=True,
                silent=False
            )
            
            # 添加多智能体团队讨论
            groupchat = autogen.GroupChat(
                agents=[self.relationship_analyst, self.entity_specialist, self.graph_visualizer, self.summary_agent, self.user_proxy],
                messages=[],
                max_round=10
            )
            manager = autogen.GroupChatManager(groupchat=groupchat)
            
            await asyncio.to_thread(
                self.user_proxy.initiate_chat,
                manager,
                message="请对以上信息进行团队分析，识别所有可能的强关系和弱关系，并提供关系图可视化建议和总结。",
                clear_history=False,
                silent=False
            )
            
            # 请求总结
            summary_request = "请总结我们的对话，特别是新发现的关系和关系图的调整建议。"
            await asyncio.to_thread(
                self.user_proxy.initiate_chat,
                self.summary_agent,
                message=summary_request,
                clear_history=False,
                silent=False
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
            
            return result
        except Exception as e:
            logger.error(f"运行对话失败: {str(e)}")
            raise 