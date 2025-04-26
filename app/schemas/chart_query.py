from pydantic import BaseModel, validator, ValidationError
from typing import Dict, List, Optional, Union
import re
from datetime import datetime

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

class DatasetItem(BaseModel):
    label: str
    data: List[float]

class ChartQueryRequest(BaseModel):
    dataset_id: int
    chart_type: str
    label_fields: List[str]
    value_fields: List[str]
    filters: Dict[str, FilterItem] = {}
    limit: Optional[int] = 10
    sort_order: Optional[str] = "desc"
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

    @validator('limit')
    def validate_limit(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Limit must be a positive integer")
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v is not None:
            valid_orders = ['asc', 'desc']
            if v.lower() not in valid_orders:
                raise ValueError(f"Sort order must be one of {valid_orders}")
            return v.lower()
        return v

    @validator('dimension_field')
    def validate_dimension_field(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Dimension field must be alphanumeric with underscores")
        return v

class ChartQueryResponse(BaseModel):
    labels: List[str]
    values: Optional[List[float]] = None
    datasets: Optional[List[DatasetItem]] = None

    @validator('datasets', always=True)
    def check_response_format(cls, v, values):
        if values.get('values') is None and v is None:
            raise ValueError("Either 'values' or 'datasets' must be provided")
        if values.get('values') is not None and v is not None:
            raise ValueError("Cannot provide both 'values' and 'datasets'")
        return v