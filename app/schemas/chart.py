from pydantic import BaseModel, validator
from typing import Optional, Dict, List
import re

class FilterItem(BaseModel):
    operator: str
    value: str

    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = ['=', '!=', '>', '<', '>=', '<=', 'LIKE']
        if v not in valid_operators:
            raise ValueError(f"Operator must be one of {valid_operators}")
        return v

    @validator('value')
    def validate_value(cls, v):
        if not v:
            raise ValueError("Filter value cannot be empty")
        return v

class ChartQuery(BaseModel):
    dataset_id: int
    chart_type: str
    label_fields: List[str]
    value_field: str
    filters: Dict[str, FilterItem] = {}

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

    @validator('value_field')
    def validate_value_field(cls, v):
        if not re.match(r'^(SUM|COUNT|AVG|MIN|MAX)\([a-zA-Z0-9_]+\)$', v, re.IGNORECASE):
            raise ValueError("Value field must be an aggregate function like SUM(column), COUNT(column), etc.")
        return v

    @validator('filters')
    def validate_filters(cls, v):
        for column_name in v.keys():
            if not re.match(r'^[a-zA-Z0-9_]+$', column_name):
                raise ValueError(f"Filter column name '{column_name}' must be alphanumeric with underscores")
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

class ChartUpdate(BaseModel):
    name: Optional[str] = None
    query: Optional[ChartQuery] = None
    config: Optional[ChartConfig] = None

class Chart(BaseModel):
    id: int
    name: str
    dataset_id: int
    schema_name: str
    query: Dict
    config: Dict

class ChartResponse(BaseModel):
    id: int
    name: str
    schema_name: str
    message: str

class ChartDataResponse(BaseModel):
    chart: Chart
    data: Dict[str, List]

class ChartListResponse(BaseModel):
    charts: List[Chart]