from pydantic import BaseModel, validator
from typing import List, Dict, Optional, Union
from datetime import datetime
import re

class LayoutItem(BaseModel):
    i: str  # Unique ID (e.g., "chart_1", "title_1", "text_1")
    x: int
    y: int
    w: int
    h: int
    type: str  # "chart", "title", "text"
    content: Dict  # chart_id for charts, text/style for title/text

    @validator('i')
    def validate_id(cls, v):
        if not re.match(r'^(chart|title|text)_\d+$', v):
            raise ValueError("ID must be in format 'chart_<number>', 'title_<number>', or 'text_<number>'")
        return v

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['chart', 'title', 'text']
        if v.lower() not in valid_types:
            raise ValueError(f"Type must be one of {valid_types}")
        return v.lower()

    @validator('content')
    def validate_content(cls, v, values):
        if 'type' not in values:
            return v
        type_ = values['type']
        if type_ == 'chart':
            if not isinstance(v.get('chart_id'), int):
                raise ValueError("Chart content must include a valid chart_id (integer)")
        elif type_ in ['title', 'text']:
            if not isinstance(v.get('text'), str):
                raise ValueError(f"{type_.capitalize()} content must include a text string")
            if v.get('style') and not isinstance(v['style'], dict):
                raise ValueError(f"{type_.capitalize()} style must be a dictionary")
        return v

    @validator('x', 'y', 'w', 'h')
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError("Layout coordinates and dimensions must be non-negative")
        return v

class DashboardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    layout: List[LayoutItem]

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

class DashboardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[List[LayoutItem]] = None

    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip() if v else v

class Dashboard(BaseModel):
    id: int
    title: str
    description: Optional[str]
    layout: List[Dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DashboardResponse(BaseModel):
    id: int
    title: str
    message: str

class DashboardListResponse(BaseModel):
    dashboards: List[Dashboard]