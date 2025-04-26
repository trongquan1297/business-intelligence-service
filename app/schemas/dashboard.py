from pydantic import BaseModel, validator
from typing import Optional, Dict, List
from datetime import datetime

class LayoutItem(BaseModel):
    i: str
    x: int
    y: int
    w: int
    h: int
    type: str
    content: Dict

    @validator('i')
    def validate_id(cls, v):
        if not v.strip():
            raise ValueError("Layout item ID cannot be empty")
        return v.strip()

    @validator('x', 'y', 'w', 'h')
    def validate_numeric_fields(cls, v):
        if v < 0:
            raise ValueError("Layout item x, y, w, h must be non-negative")
        return v

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['chart', 'title', 'text']
        if v not in valid_types:
            raise ValueError(f"Layout item type must be one of {valid_types}")
        return v

    @validator('content')
    def validate_content(cls, v, values):
        item_type = values.get('type')
        if item_type == 'chart':
            if not v.get('chart_id') or not isinstance(v.get('chart_id'), int):
                raise ValueError("Chart layout item must have a valid chart_id (integer)")
        elif item_type in ['title', 'text']:
            if not v.get('text') or not isinstance(v.get('text'), str):
                raise ValueError(f"{item_type.capitalize()} layout item must have a valid text (string)")
            if v.get('style') and not isinstance(v.get('style'), dict):
                raise ValueError(f"{item_type.capitalize()} layout item style must be a dictionary")
        return v

class DashboardCreate(BaseModel):
    name: str
    layout: List[LayoutItem]
    description: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Dashboard name cannot be empty")
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip() if v else v

class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    layout: Optional[List[LayoutItem]] = None
    description: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Dashboard name cannot be empty")
        return v.strip() if v else v

    @validator('description')
    def validate_description(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip() if v else v

class Dashboard(BaseModel):
    id: int
    name: str
    layout: List[LayoutItem]
    owner: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DashboardResponse(BaseModel):
    id: int
    name: str
    owner: str
    description: Optional[str] = None
    layout: List[LayoutItem]
    message: str

class DashboardListResponse(BaseModel):
    dashboards: List[Dashboard]