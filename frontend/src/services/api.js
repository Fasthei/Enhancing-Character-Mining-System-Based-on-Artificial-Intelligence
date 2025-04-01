import axios from 'axios';

// API基本URL
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// 创建Axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 文件上传API
export const fileApi = {
  // 上传文件
  uploadFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // 获取处理状态
  getProcessingStatus: (jobId) => {
    return api.get(`/api/files/status/${jobId}`);
  },
  
  // 获取处理结果中的实体
  getJobEntities: (jobId) => {
    return api.get(`/api/files/entities/${jobId}`);
  },
};

// 实体API
export const entityApi = {
  // 获取实体列表
  getEntities: (searchText, domain) => {
    let url = '/api/entities';
    let params = {};
    
    if (searchText) {
      params.search_text = searchText;
    }
    
    if (domain) {
      params.domain = domain;
    }
    
    return api.get(url, { params });
  },
  
  // 获取单个实体
  getEntity: (entityId) => {
    return api.get(`/api/entities/${entityId}`);
  },
  
  // 创建实体
  createEntity: (entityData) => {
    return api.post('/api/entities', entityData);
  },
  
  // 更新实体
  updateEntity: (entityId, entityData) => {
    return api.put(`/api/entities/${entityId}`, entityData);
  },
  
  // 删除实体
  deleteEntity: (entityId) => {
    return api.delete(`/api/entities/${entityId}`);
  },
  
  // 获取实体关系
  getEntityRelationships: (entityId) => {
    return api.get(`/api/entities/${entityId}/relationships`);
  },
  
  // 添加实体关系
  addEntityRelationship: (entityId, relationshipData) => {
    return api.post(`/api/entities/${entityId}/relationships`, relationshipData);
  },
};

// 对话API
export const conversationApi = {
  // 开始对话
  startConversation: (entityIds, query) => {
    return api.post('/api/conversations/start', { entity_ids: entityIds, query });
  },
  
  // 获取对话内容
  getConversation: (conversationId) => {
    return api.get(`/api/conversations/${conversationId}`);
  },
  
  // 添加消息
  addMessage: (conversationId, message) => {
    return api.post(`/api/conversations/${conversationId}/messages`, { message });
  },
  
  // 获取对话中的关系
  getConversationRelationships: (conversationId) => {
    return api.get(`/api/conversations/${conversationId}/relationships`);
  },
  
  // 获取对话总结
  getConversationSummary: (conversationId) => {
    return api.get(`/api/conversations/${conversationId}/summary`);
  },
  
  // 获取可视化建议
  getConversationVisualization: (conversationId) => {
    return api.get(`/api/conversations/${conversationId}/visualization`);
  },
};

export default {
  fileApi,
  entityApi,
  conversationApi,
}; 