import React, { useState, useEffect } from 'react';
import { Card, List, Avatar, Input, Button, Tag, Typography, Space, Empty, Checkbox, Select } from 'antd';
import { UserOutlined, SearchOutlined, TeamOutlined } from '@ant-design/icons';
import { entityApi } from '../services/api';

const { Text } = Typography;
const { Option } = Select;

const EntityList = ({ entities, onEntitySelect, selectedEntityIds = [] }) => {
  const [searchText, setSearchText] = useState('');
  const [domain, setDomain] = useState(null);
  const [filteredEntities, setFilteredEntities] = useState(entities || []);
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(false);
  const [allEntities, setAllEntities] = useState(entities || []);

  // 当传入的实体列表变化时更新
  useEffect(() => {
    if (entities && entities.length > 0) {
      setAllEntities(entities);
      applyFilters(entities);
      
      // 提取领域选项
      const domainSet = new Set();
      entities.forEach(entity => {
        if (entity.domain) {
          domainSet.add(entity.domain);
        }
      });
      setDomains(Array.from(domainSet));
    }
  }, [entities]);

  // 应用过滤器
  const applyFilters = (entitiesToFilter) => {
    let result = [...entitiesToFilter];
    
    // 应用搜索过滤
    if (searchText) {
      result = result.filter(
        entity => entity.name.toLowerCase().includes(searchText.toLowerCase()) ||
                 (entity.position && entity.position.toLowerCase().includes(searchText.toLowerCase())) ||
                 (entity.domain && entity.domain.toLowerCase().includes(searchText.toLowerCase()))
      );
    }
    
    // 应用领域过滤
    if (domain) {
      result = result.filter(entity => entity.domain === domain);
    }
    
    setFilteredEntities(result);
  };

  // 处理搜索
  const handleSearch = () => {
    if (!searchText && !domain) {
      // 如果没有过滤条件，使用初始实体列表
      setFilteredEntities(allEntities);
      return;
    }
    
    applyFilters(allEntities);
  };

  // 处理API搜索
  const handleApiSearch = async () => {
    try {
      setLoading(true);
      const response = await entityApi.getEntities(searchText, domain);
      const apiEntities = response.data.entities;
      
      setAllEntities(apiEntities);
      setFilteredEntities(apiEntities);
    } catch (error) {
      console.error('搜索实体失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 处理实体选择
  const handleEntitySelect = (entityId, checked) => {
    if (!onEntitySelect) return;
    
    if (checked) {
      // 添加到选中列表
      const entity = allEntities.find(e => e.id === entityId);
      if (entity) {
        onEntitySelect([...selectedEntityIds, entityId], [...entities, entity]);
      }
    } else {
      // 从选中列表中移除
      onEntitySelect(
        selectedEntityIds.filter(id => id !== entityId),
        entities.filter(e => e.id !== entityId)
      );
    }
  };

  return (
    <Card title="人物实体列表" style={{ height: '100%' }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索人物名称/职位..."
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="选择领域"
            style={{ width: 150 }}
            allowClear
            value={domain}
            onChange={value => setDomain(value)}
          >
            {domains.map(d => (
              <Option key={d} value={d}>{d}</Option>
            ))}
          </Select>
          <Button 
            type="primary" 
            icon={<SearchOutlined />} 
            onClick={handleSearch}
          >
            筛选
          </Button>
          <Button 
            onClick={handleApiSearch} 
            loading={loading}
          >
            从服务器搜索
          </Button>
        </Space>

        {filteredEntities.length > 0 ? (
          <List
            dataSource={filteredEntities}
            renderItem={entity => (
              <List.Item
                actions={[
                  <Checkbox
                    checked={selectedEntityIds.includes(entity.id)}
                    onChange={e => handleEntitySelect(entity.id, e.target.checked)}
                  />
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <Avatar icon={<UserOutlined />} style={{ backgroundColor: entity.gender === '女' ? '#ff6b81' : '#5352ed' }} />
                  }
                  title={
                    <Space>
                      <Text strong>{entity.name}</Text>
                      {entity.gender && (
                        <Tag color={entity.gender === '女' ? 'pink' : 'blue'}>
                          {entity.gender}
                        </Tag>
                      )}
                      {selectedEntityIds.includes(entity.id) && (
                        <Tag color="green">已选择</Tag>
                      )}
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size={0}>
                      {entity.position && <Text>职位: {entity.position}</Text>}
                      {entity.domain && <Text>领域: {entity.domain}</Text>}
                      {entity.country && <Text>国家: {entity.country}</Text>}
                    </Space>
                  }
                />
              </List.Item>
            )}
            style={{ maxHeight: '500px', overflowY: 'auto' }}
          />
        ) : (
          <Empty 
            description="暂无实体数据" 
            image={Empty.PRESENTED_IMAGE_SIMPLE} 
          />
        )}
        
        {selectedEntityIds.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Text strong>
              <TeamOutlined /> 已选择 {selectedEntityIds.length} 个人物实体
            </Text>
          </div>
        )}
      </Space>
    </Card>
  );
};

export default EntityList; 