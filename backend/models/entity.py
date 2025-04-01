from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uuid

class Relationship(BaseModel):
    target_id: str
    target_name: str
    relationship_type: str = Field(description="关系类型: STRONG或WEAK")
    relationship_description: str = Field(description="关系描述")
    confidence: float = Field(description="关系置信度", ge=0.0, le=1.0)

class Entity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: Optional[str] = None
    name: str
    photo: Optional[str] = None
    gender: Optional[str] = None
    birthDate: Optional[str] = None
    country: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    idCard: Optional[str] = None
    passportNumber: Optional[str] = None
    researchFields: Optional[List[str]] = None
    personalDescription: Optional[str] = None
    weiboUrl: Optional[str] = None
    socialAccounts: Optional[Dict[str, str]] = None
    familyStatus: Optional[str] = None
    socialRelationships: Optional[str] = None
    workExperience: Optional[List[Dict[str, Any]]] = None
    educationExperience: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None
    volunteerExperience: Optional[List[Dict[str, Any]]] = None
    languages: Optional[List[str]] = None
    personalHonors: Optional[List[str]] = None
    publications: Optional[List[Dict[str, Any]]] = None
    patents: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    certificates: Optional[List[str]] = None
    relatedPersons: Optional[List[str]] = None
    academicAchievements: Optional[List[Dict[str, Any]]] = None
    politicalStance: Optional[str] = None
    socialActivities: Optional[List[Dict[str, Any]]] = None
    chinaRelated: Optional[str] = None
    relatedUrls: Optional[List[str]] = None
    notes: Optional[str] = None
    relationships: List[Relationship] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "张三",
                "gender": "男",
                "country": "中国",
                "position": "研究员",
                "researchFields": ["人工智能", "数据挖掘"],
                "relationships": [
                    {
                        "target_id": "123456",
                        "target_name": "李四",
                        "relationship_type": "STRONG",
                        "relationship_description": "大学同学",
                        "confidence": 0.9
                    }
                ]
            }
        } 