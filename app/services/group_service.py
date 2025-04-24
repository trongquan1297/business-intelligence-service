from app.utils.database import get_mysql_connection
from typing import List, Dict

def get_table_groups() -> List[Dict]:
    """Lấy tất cả các nhóm bảng và bảng trong mỗi nhóm"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all groups
        cursor.execute("""
            SELECT id, group_name
            FROM table_groups
        """)
        groups = cursor.fetchall()
        
        # Get tables for each group
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
        raise Exception(f"Error: {str(e)}")
        return []
    
# Hàm lấy danh sách group và bảng (từ file đầu tiên)
def get_table_groups():
    """Lấy tất cả các nhóm bảng và bảng trong mỗi nhóm"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, group_name
            FROM table_groups
        """)
        groups = cursor.fetchall()
        
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
        raise Exception(f"Error: {str(e)}")
        return []

# Hàm thêm mới group
def add_table_group(group_name):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO table_groups (group_name)
            VALUES (%s)
        """, (group_name,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False

# Hàm thêm bảng vào group
def add_table_to_group(group_id, table_name, description):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tables (group_id, table_name, description)
            VALUES (%s, %s, %s)
        """, (group_id, table_name, description))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False
    
def get_available_table_groups() -> List[str]:
    """Lấy danh sách các role có sẵn từ database"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT group_name FROM table_groups")
        groups = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return groups
    except Exception as e:
        return ["user"]
    
def get_table_group(group_name):
    """Lấy danh sách table_id mà group có quyền truy cập"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id
            FROM tables
            JOIN table_group ON table_group.id = tables.group_id
            WHERE table_group.group_name = %s
        """, (group_name,))
        tables_ids = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return tables_ids
    except Exception as e:
        return []
    
# Hàm mới: Lấy tất cả bảng trong database
def get_all_tables():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT table_name, description FROM tables")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        return tables
    except Exception as e:
        return []
    
def update_group(group_id, new_group_name, selected_tables):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Cập nhật tên group
        cursor.execute("""
            UPDATE table_groups SET group_name = %s WHERE id = %s
        """, (new_group_name, group_id))
        
        # Cập nhật bảng thuộc group
        # Đặt group_id = NULL cho tất cả bảng không được chọn
        cursor.execute("""
            UPDATE tables SET group_id = NULL WHERE group_id = %s AND table_name NOT IN (%s)
        """, (group_id, ','.join(['%s'] * len(selected_tables))), *selected_tables)
        
        # Gán group_id cho các bảng được chọn
        for table_name in selected_tables:
            cursor.execute("""
                UPDATE tables SET group_id = %s WHERE table_name = %s
            """, (group_id, table_name))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False
    
def delete_group(group_id):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Đặt group_id = NULL cho tất cả bảng thuộc group trước khi xóa
        cursor.execute("""
            UPDATE tables SET group_id = NULL WHERE group_id = %s
        """, (group_id,))
        
        # Xóa group
        cursor.execute("""
            DELETE FROM table_groups WHERE id = %s
        """, (group_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False