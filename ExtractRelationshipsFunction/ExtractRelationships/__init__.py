import logging
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('关系提取函数收到请求')
    
    try:
        # 检查请求是否包含JSON数据
        req_body = req.get_json()
        
        # 处理技能组输入格式 (values数组)
        values = req_body.get('values', [])
        
        # 准备结果数组
        results = []
        
        # 处理每条记录
        for value in values:
            record_id = value['recordId']
            data = value['data']
            
            # 提取输入数据
            persons = data.get('persons', [])
            organizations = data.get('organizations', [])
            text = data.get('text', '')
            
            # 记录日志便于调试
            logging.info(f'处理记录ID: {record_id}')
            logging.info(f'发现人物实体: {persons}')
            logging.info(f'发现组织实体: {organizations}')
            
            # 实现关系提取逻辑
            relationships = extract_relationships(persons, organizations, text)
            
            logging.info(f'提取到关系数量: {len(relationships)}')
            
            # 返回处理结果
            results.append({
                "recordId": record_id,
                "data": {
                    "relationships": relationships
                }
            })
        
        # 返回与Azure AI Search兼容的响应格式
        response_body = {
            "values": results
        }
        
        return func.HttpResponse(
            body=json.dumps(response_body),
            mimetype="application/json"
        )
            
    except Exception as e:
        error_message = str(e)
        logging.error(f'处理关系提取请求时出错: {error_message}')
        
        # 返回错误响应
        error_response = {
            "error": error_message
        }
        
        return func.HttpResponse(
            body=json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )

def extract_relationships(persons, organizations, text):
    """提取人物之间的关系"""
    # 示例关系提取逻辑
    relationships = []
    
    # 强关系关键词
    strong_keywords = ["认识", "亲戚", "朋友", "夫妻", "兄弟", "姐妹", "父母", "子女", "同学", "密友"]
    # 弱关系关键词
    weak_keywords = ["同事", "同公司", "合作", "项目伙伴", "同行业", "同领域", "联系人"]
    
    # 简单实现: 根据人物共现和关键词判断关系
    for i, person1 in enumerate(persons):
        for j, person2 in enumerate(persons):
            if i == j or not person1 or not person2:
                continue
                
            # 判断两个人物之间是否存在文本共现
            if are_co_occurring(person1, person2, text):
                # 判断关系类型
                is_strong = False
                relationship_description = ""
                
                # 查找强关系关键词
                for keyword in strong_keywords:
                    if keyword in text and near_names(person1, person2, keyword, text, 50):
                        is_strong = True
                        relationship_description = f"{keyword}关系"
                        break
                        
                # 如果没找到强关系，查找弱关系
                if not is_strong:
                    for keyword in weak_keywords:
                        if keyword in text and near_names(person1, person2, keyword, text, 50):
                            relationship_description = f"{keyword}关系"
                            break
                
                if relationship_description:
                    relationships.append({
                        "source_name": person1,
                        "target_name": person2,
                        "relationship_type": "STRONG" if is_strong else "WEAK",
                        "relationship_description": relationship_description,
                        "confidence": 0.8 if is_strong else 0.6
                    })
    
    return relationships

def are_co_occurring(name1, name2, text, window_size=100):
    """判断两个名字是否在文本的同一窗口内共现"""
    if not text:
        return False
        
    for i in range(max(0, len(text) - window_size + 1)):
        window = text[i:i + window_size]
        if name1 in window and name2 in window:
            return True
    return False

def near_names(name1, name2, keyword, text, window_size=50):
    """判断关键词是否出现在两个名字附近"""
    if not text:
        return False
        
    for i in range(max(0, len(text) - window_size + 1)):
        window = text[i:i + window_size]
        if keyword in window and (name1 in window or name2 in window):
            return True
    return False 