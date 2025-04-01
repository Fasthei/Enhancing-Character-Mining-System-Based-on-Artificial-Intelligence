import React, { useState } from 'react';
import { Layout, Row, Col, Typography, Menu, Button, Divider } from 'antd';
import { UploadOutlined, TeamOutlined, CommentOutlined, ApartmentOutlined } from '@ant-design/icons';
import FileUpload from '../components/FileUpload';
import EntityList from '../components/EntityList';
import RelationshipGraph from '../components/RelationshipGraph';
import ConversationPanel from '../components/ConversationPanel';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const MainPage = () => {
  const [entities, setEntities] = useState([]);
  const [selectedEntityIds, setSelectedEntityIds] = useState([]);
  const [selectedEntities, setSelectedEntities] = useState([]);
  const [conversationRelationships, setConversationRelationships] = useState([]);
  const [currentView, setCurrentView] = useState('upload');

  // 处理文件上传后的实体加载
  const handleEntitiesLoaded = (loadedEntities) => {
    setEntities(prev => {
      // 合并新实体，避免重复
      const newEntities = [...prev];
      loadedEntities.forEach(entity => {
        if (!newEntities.some(e => e.id === entity.id)) {
          newEntities.push(entity);
        }
      });
      return newEntities;
    });
    
    // 自动切换到实体列表视图
    setCurrentView('entities');
  };

  // 处理实体选择
  const handleEntitySelect = (entityIds, entities) => {
    setSelectedEntityIds(entityIds);
    setSelectedEntities(entities);
  };

  // 处理对话中发现的新关系
  const handleNewRelationships = (relationships) => {
    setConversationRelationships(relationships);
  };

  // 渲染菜单
  const renderMenu = () => (
    <Menu 
      mode="inline"
      selectedKeys={[currentView]}
      style={{ height: '100%' }}
      onClick={({ key }) => setCurrentView(key)}
    >
      <Menu.Item key="upload" icon={<UploadOutlined />}>
        上传文件
      </Menu.Item>
      <Menu.Item key="entities" icon={<TeamOutlined />}>
        实体列表
      </Menu.Item>
      <Menu.Item key="graph" icon={<ApartmentOutlined />}>
        关系图
      </Menu.Item>
      <Menu.Item key="conversation" icon={<CommentOutlined />}>
        对话分析
      </Menu.Item>
    </Menu>
  );

  // 渲染当前视图内容
  const renderContent = () => {
    switch (currentView) {
      case 'upload':
        return <FileUpload onEntitiesLoaded={handleEntitiesLoaded} />;
      case 'entities':
        return (
          <EntityList
            entities={entities}
            onEntitySelect={handleEntitySelect}
            selectedEntityIds={selectedEntityIds}
          />
        );
      case 'graph':
        return <RelationshipGraph entities={selectedEntities} relationships={conversationRelationships} />;
      case 'conversation':
        return <ConversationPanel entities={selectedEntities} onNewRelationships={handleNewRelationships} />;
      default:
        return <FileUpload onEntitiesLoaded={handleEntitiesLoaded} />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px' }}>
        <Row align="middle" style={{ height: '100%' }}>
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              人物关系挖掘系统
            </Title>
          </Col>
        </Row>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          {renderMenu()}
        </Sider>
        <Content style={{ padding: '24px', background: '#fff' }}>
          {renderContent()}
          
          {currentView !== 'graph' && currentView !== 'conversation' && selectedEntities.length > 0 && (
            <>
              <Divider>已选择 {selectedEntities.length} 个实体</Divider>
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <RelationshipGraph entities={selectedEntities} relationships={conversationRelationships} />
                </Col>
              </Row>
            </>
          )}
          
          {currentView !== 'conversation' && selectedEntities.length > 0 && (
            <>
              <Divider>对话分析</Divider>
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <ConversationPanel entities={selectedEntities} onNewRelationships={handleNewRelationships} />
                </Col>
              </Row>
            </>
          )}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainPage; 