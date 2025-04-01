import React, { useState, useEffect, useRef } from 'react';
import { Card, Input, Button, List, Typography, Avatar, Space, Tag, Spin, Empty } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined } from '@ant-design/icons';
import { conversationApi } from '../services/api';

const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;

const ConversationPanel = ({ entities, onNewRelationships }) => {
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversationStatus, setConversationStatus] = useState(null);
  const [pollingInterval, setPollingInterval] = useState(null);
  const [summary, setSummary] = useState('');
  const messagesEndRef = useRef(null);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // 滚动到最新消息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 处理发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    
    const userMessage = {
      role: 'user',
      content: inputValue
    };
    
    setMessages(msgs => [...msgs, userMessage]);
    setInputValue('');
    setLoading(true);
    
    try {
      // 如果还没有对话ID，创建新对话
      if (!conversationId) {
        if (!entities || entities.length === 0) {
          setMessages(msgs => [...msgs, {
            role: 'system',
            content: '请先上传人物数据或选择人物实体'
          }]);
          setLoading(false);
          return;
        }
        
        // 开始新对话
        const entityIds = entities.map(entity => entity.id);
        const response = await conversationApi.startConversation(entityIds, inputValue);
        
        setConversationId(response.data.conversation_id);
        setConversationStatus('initializing');
        
        // 轮询对话状态
        pollConversationStatus(response.data.conversation_id);
      } else {
        // 向现有对话添加消息
        await conversationApi.addMessage(conversationId, inputValue);
        
        // 更新对话状态
        setConversationStatus('processing');
        
        // 如果没有轮询，启动轮询
        if (!pollingInterval) {
          pollConversationStatus(conversationId);
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      setMessages(msgs => [...msgs, {
        role: 'system',
        content: '发送消息失败，请重试'
      }]);
      setLoading(false);
    }
  };

  // 轮询对话状态
  const pollConversationStatus = (convId) => {
    const interval = setInterval(async () => {
      try {
        const response = await conversationApi.getConversation(convId);
        const { status, messages: convMessages, summary: convSummary } = response.data;
        
        // 更新状态
        setConversationStatus(status);
        
        // 更新消息
        if (convMessages && convMessages.length > 0) {
          setMessages(convMessages);
        }
        
        // 更新总结
        if (convSummary) {
          setSummary(convSummary);
        }
        
        // 如果对话完成或失败，停止轮询
        if (status === 'completed' || status === 'failed') {
          clearInterval(interval);
          setPollingInterval(null);
          setLoading(false);
          
          // 获取关系
          if (status === 'completed') {
            try {
              const relationshipsResponse = await conversationApi.getConversationRelationships(convId);
              const { relationships } = relationshipsResponse.data;
              
              // 通知父组件新的关系
              if (relationships && relationships.length > 0 && onNewRelationships) {
                onNewRelationships(relationships);
              }
            } catch (error) {
              console.error('获取关系失败:', error);
            }
          }
        }
      } catch (error) {
        console.error('轮询对话状态失败:', error);
        clearInterval(interval);
        setPollingInterval(null);
        setLoading(false);
      }
    }, 2000);
    
    setPollingInterval(interval);
  };

  // 获取角色头像
  const getAvatar = (role) => {
    switch (role) {
      case 'user':
        return <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />;
      case '用户代理':
        return <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />;
      case 'system':
        return <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />;
      case '关系分析师':
        return <Avatar style={{ backgroundColor: '#f56a00' }}>关系</Avatar>;
      case '实体专家':
        return <Avatar style={{ backgroundColor: '#7265e6' }}>实体</Avatar>;
      case '图表可视化师':
        return <Avatar style={{ backgroundColor: '#ffbf00' }}>图表</Avatar>;
      case '总结专家':
        return <Avatar style={{ backgroundColor: '#00a2ae' }}>总结</Avatar>;
      default:
        return <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />;
    }
  };

  return (
    <Card title="人物关系对话分析" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ flex: 1, overflowY: 'auto', marginBottom: '16px', minHeight: '300px', maxHeight: '500px' }}>
          {messages.length > 0 ? (
            <List
              dataSource={messages}
              renderItem={message => (
                <List.Item>
                  <List.Item.Meta
                    avatar={getAvatar(message.role)}
                    title={
                      <Space>
                        <Text strong>{message.role === 'user' ? '用户' : message.role}</Text>
                        {message.role !== 'user' && message.role !== 'system' && (
                          <Tag color="blue">AI</Tag>
                        )}
                      </Space>
                    }
                    description={<Paragraph ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}>{message.content}</Paragraph>}
                  />
                </List.Item>
              )}
            />
          ) : (
            <Empty 
              description="开始对话以分析人物关系" 
              image={Empty.PRESENTED_IMAGE_SIMPLE} 
              style={{ margin: '100px auto' }}
            />
          )}
          <div ref={messagesEndRef} />
        </div>
        
        {summary && (
          <Card 
            title="对话总结" 
            size="small" 
            style={{ marginBottom: '16px' }}
          >
            <Paragraph>{summary}</Paragraph>
          </Card>
        )}
        
        <div style={{ display: 'flex', marginTop: 'auto' }}>
          <TextArea
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            placeholder="输入问题进行人物关系分析..."
            autoSize={{ minRows: 2, maxRows: 4 }}
            onPressEnter={e => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            style={{ marginRight: '8px' }}
            disabled={loading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            loading={loading}
            style={{ alignSelf: 'flex-end' }}
          >
            发送
          </Button>
        </div>
        
        {loading && (
          <div style={{ textAlign: 'center', marginTop: '8px' }}>
            <Spin size="small" />
            <Text type="secondary" style={{ marginLeft: '8px' }}>
              AI思考中...
            </Text>
          </div>
        )}
      </div>
    </Card>
  );
};

export default ConversationPanel; 