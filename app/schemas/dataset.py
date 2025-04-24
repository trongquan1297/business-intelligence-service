from pydantic import BaseModel
from typing import List

class DatasetCreate(BaseModel):
    table_name: str
    database: str
    schema_name: str

class Dataset(BaseModel):
    id: int
    database: str
    table_name: str
    schema_name: str

class DatasetResponse(BaseModel):
    id: int
    table_name: str
    schema_name: str
    message: str

class DatasetListResponse(BaseModel):
    datasets: List[Dataset]

class DatasetDeleteResponse(BaseModel):
    id: int
    message: str