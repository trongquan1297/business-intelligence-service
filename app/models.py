from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Auth
class LoginRequest(BaseModel):
    username: str
    password: str

class SSORequest(BaseModel):
    authorization_code: str

# Chat
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    sql_query: str
    explanation: str
    chart_title: str
    suggested_chart_type: str
    recommendation: List[str]
    data: Optional[List[Dict[str, Any]]] = None
    chart: Optional[Dict[str, Any]] = None

# History
class HistoryItem(BaseModel):
    id: str
    timestamp: str
    question: str
    explanation: str
    sql_query: str
    chart_type: str
    chart_title: str
    data: Optional[List[Dict[str, Any]]] = None

# Admin - Tables (Định nghĩa Table trước)
class Table(BaseModel):
    table_name: str
    description: str

# Admin - Groups (Sử dụng Table đã định nghĩa)
class TableGroup(BaseModel):
    id: int
    group_name: str
    tables: List[Table]

class CreateGroupRequest(BaseModel):
    group_name: str

class AddTableToGroupRequest(BaseModel):
    group_id: int
    table_name: str
    description: str

class UpdateGroupRequest(BaseModel):
    group_id: int
    new_group_name: str
    selected_tables: List[str]

# Admin - Users
class User(BaseModel):
    username: str
    email: str
    role: str
    active: bool

class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: str

class UpdateUserRequest(BaseModel):
    username: str
    role: str
    active: bool

# Admin - Tables (Các request liên quan đến Table)
class CreateTableRequest(BaseModel):
    table_name: str
    description: str

class UpdateTableRequest(BaseModel):
    old_table_name: str
    new_table_name: str
    description: str