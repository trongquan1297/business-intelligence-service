from pydantic import BaseModel, validator, ValidationError
from typing import Optional, Dict, List, Union
from datetime import datetime
import re

class FilterItem(BaseModel):
    operator: str
    value: Union[str, List[str]]
    filterType: Optional[str] = None

    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = ['=', '!=', '>', '<', '>=', '<=', 'LIKE', 'between']
        if v.lower() not in valid_operators:
            raise ValueError(f"Operator must be one of {valid_operators}")
        return v.lower()

    @validator('value')
    def validate_value(cls, v, values):
        operator = values.get('operator', '').lower()
        if operator == 'between':
            if not isinstance(v, list) or len(v) != 2:
                raise ValueError("Value for 'between' operator must be a list of two timestamps")
            try:
                start = datetime.fromisoformat(v[0].replace('Z', '+00:00'))
                end = datetime.fromisoformat(v[1].replace('Z', '+00:00'))
                if start > end:
                    raise ValueError("Start timestamp cannot be after end timestamp")
            except ValueError as e:
                if "cannot be after" in str(e):
                    raise
                raise ValueError("Values must be valid ISO 8601 timestamps (e.g., '2024-02-01T00:00:00.000Z')")
        else:
            if isinstance(v, list):
                raise ValueError("Value must be a string for non-'between' operators")
            if not v:
                raise ValueError("Filter value cannot be empty")
        return v

    # @validator('filterType')
    # def validate_filter_type(cls, v, values):
    #     operator = values.get('operator', '').lower()
    #     if operator == 'between' and v != 'custom':
    #         raise ValueError("filterType must be 'custom' for 'between' operator")
    #     if operator != 'between' and v is not None:
    #         raise ValueError("filterType is only allowed for 'between' operator")
    #     return v

class ChartQuery(BaseModel):
    dataset_id: int
    chart_type: str
    label_fields: List[str]
    value_fields: List[str]
    filters: Dict[str, FilterItem] = {}
    dimension_field: Optional[str] = None

    @validator('chart_type')
    def validate_chart_type(cls, v):
        valid_types = ['line', 'bar', 'pie', 'scatter']
        if v.lower() not in valid_types:
            raise ValueError(f"Chart type must be one of {valid_types}")
        return v.lower()

    @validator('label_fields')
    def validate_label_fields(cls, v):
        if not v:
            raise ValueError("At least one label field is required")
        for field in v:
            if not re.match(r'^[a-zA-Z0-9_]+$', field):
                raise ValueError(f"Label field '{field}' must be alphanumeric with underscores")
        return v

    @validator('value_fields')
    def validate_value_fields(cls, v):
        if not v:
            raise ValueError("At least one value field is required")
        for field in v:
            if not re.match(r'^(SUM|COUNT|AVG|MIN|MAX)\([a-zA-Z0-9_]+\)$', field, re.IGNORECASE):
                raise ValueError(f"Value field '{field}' must be an aggregate function like SUM(column), COUNT(column), etc.")
        return v

    @validator('filters')
    def validate_filters(cls, v):
        for column_name in v.keys():
            if not re.match(r'^[a-zA-Z0-9_]+$', column_name):
                raise ValueError(f"Filter column name '{column_name}' must be alphanumeric with underscores")
        return v

    @validator('dimension_field')
    def validate_dimension_field(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Dimension field must be alphanumeric with underscores")
        return v

class ChartConfig(BaseModel):
    colorScheme: str
    showLegend: bool
    limit: int
    sortOrder: str

    @validator('colorScheme')
    def validate_color_scheme(cls, v):
        valid_schemes = ['tableau10', 'category10', 'pastel1', 'set3']
        if v.lower() not in valid_schemes:
            raise ValueError(f"Color scheme must be one of {valid_schemes}")
        return v.lower()

    @validator('limit')
    def validate_limit(cls, v):
        if v <= 0:
            raise ValueError("Limit must be a positive integer")
        return v

    @validator('sortOrder')
    def validate_sort_order(cls, v):
        valid_orders = ['asc', 'desc']
        if v.lower() not in valid_orders:
            raise ValueError(f"Sort order must be one of {valid_orders}")
        return v.lower()

class ChartCreate(BaseModel):
    name: str
    query: ChartQuery
    config: ChartConfig
    who_is_access: Optional[List[str]] = None

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Chart name cannot be empty")
        return v.strip()

    @validator('who_is_access')
    def validate_who_is_access(cls, v):
        if v is not None:
            for user in v:
                if not user.strip():
                    raise ValueError("User or role in who_is_access cannot be empty")
            return [user.strip() for user in v]
        return v

class ChartUpdate(BaseModel):
    name: Optional[str] = None
    query: Optional[ChartQuery] = None
    config: Optional[ChartConfig] = None
    who_is_access: Optional[List[str]] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Chart name cannot be empty")
        return v.strip() if v else v

    @validator('who_is_access')
    def validate_who_is_access(cls, v):
        if v is not None:
            for user in v:
                if not user.strip():
                    raise ValueError("User or role in who_is_access cannot be empty")
            return [user.strip() for user in v]
        return v

class Chart(BaseModel):
    id: int
    name: str
    dataset_id: int
    schema_name: str
    query: Dict
    config: Dict
    owner: str
    who_is_access: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ChartResponse(BaseModel):
    id: int
    name: str
    schema_name: str
    owner: str
    message: str

class ChartDataResponse(BaseModel):
    chart: Chart
    data: Dict

class ChartListResponse(BaseModel):
    charts: List[Chart]