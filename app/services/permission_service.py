from app.utils.database import get_mysql_connection
from clickhouse_driver import Client
from app.services.group_service import get_table_groups
from app.services.user_service import get_user_role
import pandas as pd
import re
from typing import List, Optional, Dict

def get_allowed_tables_prompt(role: str) -> str:
    """Tạo phần prompt về các bảng được phép truy cập theo role"""
    table_groups = get_role_table_groups(role)
    
    if not table_groups:
        return "Không có quyền truy cập bảng nào."
        
    prompt = "Các bảng có sẵn:\n\n"
    
    for group in table_groups:
        prompt += f"Nhóm {group['group_name'].capitalize()}:\n"
        for table in group['tables']:
            prompt += f"- {table['table_name']} ({table['description']})\n"
        prompt += "\n"
        
    return prompt

def get_allowed_tables(role: str) -> List[str]:
    """Lấy danh sách tên bảng được phép truy cập theo role"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        if role == 'admin':
            cursor.execute("SELECT table_name FROM tables")
        else:
            cursor.execute("""
                SELECT DISTINCT t.table_name
                FROM tables t
                JOIN table_groups tg ON t.group_id = tg.id
                JOIN role_group_permissions rgp ON rgp.group_id = tg.id
                JOIN roles r ON r.id = rgp.role_id
                WHERE r.role_name = %s
            """, (role,))
            
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return tables
    except Exception as e:
        return []

def check_table_access(sql_query: str, role: str) -> bool:
    """Kiểm tra quyền truy cập các bảng trong câu query"""
    if role == 'admin':
        return True
        
    allowed_tables = get_allowed_tables(role)
    
    # Tìm tất cả các bảng trong câu query
    table_pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
    tables = re.findall(table_pattern, sql_query, re.IGNORECASE)
    
    # Kiểm tra từng bảng
    for table in tables:
        table = table.strip()
        if table not in allowed_tables:
            return False
    
    return True

def get_role_table_groups(role: str) -> List[Dict]:
    """Lấy các nhóm bảng và bảng mà role có quyền truy cập"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        if role == 'admin':
            # Admin có quyền truy cập tất cả
            return get_table_groups()
            
        # Lấy các nhóm được phép theo role
        cursor.execute("""
            SELECT tg.id, tg.group_name
            FROM table_groups tg
            JOIN role_group_permissions rgp ON rgp.group_id = tg.id
            JOIN roles r ON r.id = rgp.role_id
            WHERE r.role_name = %s
        """, (role,))
        groups = cursor.fetchall()
        
        # Lấy bảng cho mỗi nhóm
        for group in groups:
            cursor.execute("""
                SELECT table_name, description
                FROM tables
                WHERE group_id = %s
            """, (group['id'],))
            group['tables'] = cursor.fetchall()
            
        cursor.close()
        conn.close()
        return groups
    except Exception as e:
        return []

def execute_query_with_permission(client: Client, sql_query: str, username: str) -> Optional[pd.DataFrame]:
    """Thực thi query sau khi kiểm tra quyền"""
    role = get_user_role(username)
    if not role:
        raise Exception("Không tìm thấy role của user")
        
    if not check_table_access(sql_query, role):
        raise Exception("Bạn không có quyền truy cập các bảng này")
        
    # Thực thi query nếu có quyền
    return client.execute(sql_query, with_column_types=True)