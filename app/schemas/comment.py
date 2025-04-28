from pydantic import BaseModel, validator
from datetime import datetime
from enum import Enum

class ResourceType(str, Enum):
    dashboard = "dashboard"
    note = "note"

class CommentCreate(BaseModel):
    resource_type: ResourceType = ResourceType.dashboard
    resource_id: int
    content: str

    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Comment content cannot be empty")
        return v.strip()

class Comment(BaseModel):
    id: int
    resource_type: ResourceType
    resource_id: int
    username: str
    content: str
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CommentResponse(BaseModel):
    id: int
    resource_type: ResourceType
    resource_id: int
    username: str
    content: str
    created_at: datetime
    message: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }