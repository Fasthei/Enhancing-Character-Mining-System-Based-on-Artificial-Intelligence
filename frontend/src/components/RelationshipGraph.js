import React, { useEffect, useState, useRef } from 'react';
import { Card, Empty, Spin, Typography, Switch, Space, Tag } from 'antd';
import ForceGraph2D from 'react-force-graph-2d';
import { UserOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const RelationshipGraph = ({ entities, relationships }) => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [showStrongRelations, setShowStrongRelations] = useState(true);
  const [showWeakRelations, setShowWeakRelations] = useState(true);
  const fgRef = useRef();

  // 处理实体和关系数据生成图形数据
  useEffect(() => {
    if (!entities || entities.length === 0) {
      setGraphData({ nodes: [], links: [] });
      return;
    }

    setLoading(true);

    try {
      // 构建节点数据
      const nodes = entities.map(entity => ({
        id: entity.id,
        name: entity.name,
        domain: entity.domain || '未知领域',
        position: entity.position || '未知职位',
        gender: entity.gender || '未知',
        country: entity.country || '未知',
        val: 1, // 节点大小
      }));

      // 构建连接数据
      let links = [];
      
      // 处理实体自带的关系
      entities.forEach(entity => {
        if (entity.relationships && entity.relationships.length > 0) {
          entity.relationships.forEach(rel => {
            // 检查目标实体是否存在
            const targetExists = entities.some(e => e.id === rel.target_id);
            if (targetExists) {
              links.push({
                source: entity.id,
                target: rel.target_id,
                type: rel.relationship_type,
                description: rel.relationship_description,
                value: rel.confidence || 0.5,
              });
            }
          });
        }
      });
      
      // 如果提供了额外的关系数据，也添加进来
      if (relationships && relationships.length > 0) {
        relationships.forEach(rel => {
          // 查找源实体和目标实体
          const sourceEntity = entities.find(e => e.name === rel.source);
          if (sourceEntity) {
            // 查找目标实体
            const targetEntities = entities.filter(e => 
              rel.description && rel.description.includes(e.name) && e.name !== sourceEntity.name
            );
            
            // 为每个目标实体创建一个连接
            targetEntities.forEach(targetEntity => {
              // 判断关系类型
              const isStrongRelation = rel.description && 
                ['认识', '亲戚', '朋友', '夫妻', '兄弟', '姐妹', '父母', '子女', '同学', '密友'].some(
                  keyword => rel.description.includes(keyword)
                );
              
              links.push({
                source: sourceEntity.id,
                target: targetEntity.id,
                type: isStrongRelation ? 'STRONG' : 'WEAK',
                description: rel.description,
                value: isStrongRelation ? 0.8 : 0.4,
              });
            });
          }
        });
      }

      // 过滤关系
      if (!showStrongRelations) {
        links = links.filter(link => link.type !== 'STRONG');
      }
      
      if (!showWeakRelations) {
        links = links.filter(link => link.type !== 'WEAK');
      }

      setGraphData({ nodes, links });
    } catch (error) {
      console.error('处理图形数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [entities, relationships, showStrongRelations, showWeakRelations]);

  // 过滤关系类型
  const handleStrongRelationsChange = checked => {
    setShowStrongRelations(checked);
  };

  const handleWeakRelationsChange = checked => {
    setShowWeakRelations(checked);
  };

  // 自动调整图形大小
  useEffect(() => {
    if (fgRef.current && graphData.nodes.length > 0) {
      // 缩放以适应所有节点
      fgRef.current.zoomToFit(400);
    }
  }, [graphData]);

  return (
    <Card title="人物关系图" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Space direction="vertical" style={{ width: '100%', height: '100%' }}>
        <Space>
          <Text>强关系:</Text>
          <Switch checked={showStrongRelations} onChange={handleStrongRelationsChange} />
          <Tag color="red">红色线条</Tag>
          
          <Text style={{ marginLeft: 20 }}>弱关系:</Text>
          <Switch checked={showWeakRelations} onChange={handleWeakRelationsChange} />
          <Tag color="blue">蓝色线条</Tag>
        </Space>
        
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
            <Spin tip="加载关系图中..." />
          </div>
        ) : graphData.nodes.length > 0 ? (
          <div style={{ height: '500px', border: '1px solid #f0f0f0', borderRadius: '2px' }}>
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              nodeLabel={node => `${node.name} (${node.position || '未知职位'}, ${node.domain || '未知领域'})`}
              nodeColor={node => node.gender === '女' ? '#ff6b81' : '#5352ed'}
              nodeRelSize={6}
              linkLabel={link => link.description || (link.type === 'STRONG' ? '强关系' : '弱关系')}
              linkColor={link => link.type === 'STRONG' ? 'red' : 'blue'}
              linkWidth={link => link.value * 3}
              linkDirectionalParticles={2}
              linkDirectionalParticleWidth={link => link.value * 2}
              nodeCanvasObject={(node, ctx, globalScale) => {
                const label = node.name;
                const fontSize = 12/globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                const textWidth = ctx.measureText(label).width;
                const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

                ctx.fillStyle = node.gender === '女' ? '#ff6b81' : '#5352ed';
                ctx.beginPath();
                ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
                ctx.fill();
                
                ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                ctx.fillRect(
                  node.x - bckgDimensions[0] / 2,
                  node.y - bckgDimensions[1] / 2 - fontSize,
                  bckgDimensions[0],
                  bckgDimensions[1]
                );

                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#222';
                ctx.fillText(label, node.x, node.y - fontSize/2);
              }}
              cooldownTicks={100}
              onEngineStop={() => fgRef.current.zoomToFit(400)}
            />
          </div>
        ) : (
          <Empty 
            description="暂无关系数据" 
            image={Empty.PRESENTED_IMAGE_SIMPLE} 
            style={{ margin: '100px auto' }}
          />
        )}
      </Space>
    </Card>
  );
};

export default RelationshipGraph; 