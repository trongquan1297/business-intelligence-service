# from fastapi import APIRouter, Depends, HTTPException
# from app.models import (
#     TableGroup, CreateGroupRequest, AddTableToGroupRequest, UpdateGroupRequest,
#     User, CreateUserRequest, UpdateUserRequest,
#     CreateTableRequest, UpdateTableRequest
# )
# from app.dependencies import get_admin_user
# from app.services.group_service import (
#     get_table_groups, add_table_group, add_table_to_group, update_group, delete_group
# )
# from app.services.user_service import (
#     create_user, get_users, update_user_role_and_active, delete_user
# )
# from app.services.table_service import (
#     add_table, get_all_tables, update_table, delete_table
# )
# from typing import List

# router = APIRouter()

# # Groups
# @router.get("/groups", response_model=List[TableGroup])
# async def list_groups(admin: str = Depends(get_admin_user)):
#     return get_table_groups()

# @router.post("/groups", response_model=dict)
# async def create_group(request: CreateGroupRequest, admin: str = Depends(get_admin_user)):
#     if add_table_group(request.group_name):
#         return {"message": "Group created successfully"}
#     raise HTTPException(status_code=500, detail="Failed to create group")

# @router.post("/groups/add-table", response_model=dict)
# async def add_table_to_group_endpoint(request: AddTableToGroupRequest, admin: str = Depends(get_admin_user)):
#     if add_table_to_group(request.group_id, request.table_name, request.description):
#         return {"message": "Table added to group successfully"}
#     raise HTTPException(status_code=500, detail="Failed to add table to group")

# @router.put("/groups/{group_id}", response_model=dict)
# async def update_group_endpoint(group_id: int, request: UpdateGroupRequest, admin: str = Depends(get_admin_user)):
#     if update_group(request.group_id, request.new_group_name, request.selected_tables):
#         return {"message": "Group updated successfully"}
#     raise HTTPException(status_code=500, detail="Failed to update group")

# @router.delete("/groups/{group_id}", response_model=dict)
# async def delete_group_endpoint(group_id: int, admin: str = Depends(get_admin_user)):
#     if delete_group(group_id):
#         return {"message": "Group deleted successfully"}
#     raise HTTPException(status_code=500, detail="Failed to delete group")

# # Users
# @router.post("/users", response_model=dict)
# async def create_user_endpoint(request: CreateUserRequest, admin: str = Depends(get_admin_user)):
#     if create_user(request.username, request.password, request.email):
#         return {"message": "User created successfully"}
#     raise HTTPException(status_code=500, detail="Failed to create user")

# @router.get("/users", response_model=List[User])
# async def list_users(admin: str = Depends(get_admin_user)):
#     return get_users()

# @router.put("/users/{username}", response_model=dict)
# async def update_user_endpoint(username: str, request: UpdateUserRequest, admin: str = Depends(get_admin_user)):
#     if update_user_role_and_active(request.username, request.role, request.active):
#         return {"message": "User updated successfully"}
#     raise HTTPException(status_code=500, detail="Failed to update user")

# @router.delete("/users/{username}", response_model=dict)
# async def delete_user_endpoint(username: str, admin: str = Depends(get_admin_user)):
#     if delete_user(username):
#         return {"message": "User deleted successfully"}
#     raise HTTPException(status_code=500, detail="Failed to delete user")

# # Tables
# @router.post("/tables", response_model=dict)
# async def create_table(request: CreateTableRequest, admin: str = Depends(get_admin_user)):
#     if add_table(request.table_name, request.description):
#         return {"message": "Table created successfully"}
#     raise HTTPException(status_code=500, detail="Failed to create table")

# @router.get("/tables", response_model=List[Table])
# async def list_tables(admin: str = Depends(get_admin_user)):
#     return get_all_tables()

# @router.put("/tables/{table_name}", response_model=dict)
# async def update_table_endpoint(table_name: str, request: UpdateTableRequest, admin: str = Depends(get_admin_user)):
#     if update_table(request.old_table_name, request.new_table_name, request.description):
#         return {"message": "Table updated successfully"}
#     raise HTTPException(status_code=500, detail="Failed to update table")

# @router.delete("/tables/{table_name}", response_model=dict)
# async def delete_table_endpoint(table_name: str, admin: str = Depends(get_admin_user)):
#     if delete_table(table_name):
#         return {"message": "Table deleted successfully"}
#     raise HTTPException(status_code=500, detail="Failed to delete table")