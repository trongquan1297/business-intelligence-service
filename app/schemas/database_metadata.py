from pydantic import BaseModel
from typing import List

class Schema(BaseModel):
    schema_name: str

class SchemaListResponse(BaseModel):
    schemas: List[Schema]

class Table(BaseModel):
    table_name: str
    schema_name: str

class TableListResponse(BaseModel):
    tables: List[Table]

class Column(BaseModel):
    column_name: str
    data_type: str

class ColumnListResponse(BaseModel):
    table_name: str
    schema_name: str
    columns: List[Column]