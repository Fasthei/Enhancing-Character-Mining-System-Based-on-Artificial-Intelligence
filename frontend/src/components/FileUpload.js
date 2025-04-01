import React, { useState, useEffect } from 'react';
import { Upload, Button, message, Progress, Card, List, Typography, Space } from 'antd';
import { UploadOutlined, FileOutlined, FileExcelOutlined, FileTextOutlined } from '@ant-design/icons';
import { fileApi } from '../services/api';

const { Title, Text } = Typography;

const FileUpload = ({ onEntitiesLoaded }) => {
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [checkingInterval, setCheckingInterval] = useState(null);
  const [entities, setEntities] = useState([]);

  // 清除定时器
  useEffect(() => {
    return () => {
      if (checkingInterval) {
        clearInterval(checkingInterval);
      }
    };
  }, [checkingInterval]);

  // 上传前检查文件类型
  const beforeUpload = (file) => {
    const isValidType = 
      file.type === 'text/csv' || 
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.type === 'application/vnd.ms-excel' ||
      file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
      file.type === 'application/msword' ||
      file.type === 'text/plain';
    
    if (!isValidType) {
      message.error('只支持上传CSV、Excel、Word或TXT文件!');
    }
    
    return isValidType || Upload.LIST_IGNORE;
  };

  // 文件列表变化
  const handleChange = ({ fileList }) => {
    setFileList(fileList);
  };

  // 上传文件
  const handleUpload = async () => {
    const formData = new FormData();
    const file = fileList[0].originFileObj;
    formData.append('file', file);
    
    setUploading(true);
    setProgress(0);
    setStatus('uploading');
    setStatusMessage('正在上传文件...');
    
    try {
      // 上传文件
      const response = await fileApi.uploadFile(file);
      const { job_id } = response.data;
      
      setJobId(job_id);
      setStatus('processing');
      setStatusMessage('文件上传成功，正在处理...');
      setProgress(10);
      
      // 设置定时检查处理状态
      const interval = setInterval(async () => {
        try {
          const statusResponse = await fileApi.getProcessingStatus(job_id);
          const { status, progress, message } = statusResponse.data;
          
          setStatus(status);
          setProgress(progress);
          setStatusMessage(message);
          
          // 处理完成
          if (status === 'completed') {
            clearInterval(interval);
            setCheckingInterval(null);
            
            // 获取处理结果
            const entitiesResponse = await fileApi.getJobEntities(job_id);
            const loadedEntities = entitiesResponse.data.entities;
            setEntities(loadedEntities);
            
            // 通知父组件
            if (onEntitiesLoaded) {
              onEntitiesLoaded(loadedEntities);
            }
            
            message.success('文件处理完成!');
          }
          
          // 处理失败
          if (status === 'failed') {
            clearInterval(interval);
            setCheckingInterval(null);
            message.error(`处理失败: ${message}`);
          }
          
        } catch (error) {
          console.error('检查处理状态失败:', error);
          clearInterval(interval);
          setCheckingInterval(null);
          message.error('检查处理状态失败');
        }
      }, 2000);
      
      setCheckingInterval(interval);
      
    } catch (error) {
      console.error('上传失败:', error);
      message.error('文件上传失败');
      setStatus('error');
      setStatusMessage('上传失败');
    } finally {
      setUploading(false);
    }
  };

  // 获取文件图标
  const getFileIcon = (file) => {
    if (!file) return <FileOutlined />;
    
    const fileName = file.name || '';
    const fileType = fileName.split('.').pop().toLowerCase();
    
    switch (fileType) {
      case 'csv':
      case 'xlsx':
      case 'xls':
        return <FileExcelOutlined style={{ color: '#52c41a' }} />;
      case 'doc':
      case 'docx':
      case 'txt':
        return <FileTextOutlined style={{ color: '#1890ff' }} />;
      default:
        return <FileOutlined />;
    }
  };

  return (
    <Card title="上传人物数据文件" style={{ marginBottom: 20 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Upload
          listType="text"
          fileList={fileList}
          beforeUpload={beforeUpload}
          onChange={handleChange}
          maxCount={1}
          onRemove={() => {
            setFileList([]);
            setStatus('');
            setStatusMessage('');
            setProgress(0);
            setJobId(null);
            setEntities([]);
          }}
        >
          <Button icon={<UploadOutlined />} disabled={fileList.length > 0 || uploading}>
            选择文件
          </Button>
        </Upload>
        
        <Button
          type="primary"
          onClick={handleUpload}
          disabled={fileList.length === 0 || uploading || status === 'processing' || status === 'completed'}
          loading={uploading}
          style={{ marginTop: 16 }}
        >
          {uploading ? '上传中' : '开始上传'}
        </Button>
        
        {(status === 'uploading' || status === 'processing') && (
          <div style={{ marginTop: 16 }}>
            <Progress percent={progress} status="active" />
            <Text>{statusMessage}</Text>
          </div>
        )}
        
        {status === 'completed' && entities.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Title level={5}>提取到的实体：</Title>
            <List
              size="small"
              bordered
              dataSource={entities}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={getFileIcon()}
                    title={item.name}
                    description={`领域: ${item.domain || '未知'}, 职位: ${item.position || '未知'}`}
                  />
                </List.Item>
              )}
            />
          </div>
        )}
      </Space>
    </Card>
  );
};

export default FileUpload; 