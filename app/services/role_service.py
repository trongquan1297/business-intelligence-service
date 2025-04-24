from app.utils.database import get_mysql_connection
from typing import List, Optional, Dict

def get_role_group_permissions(role_name):
    """Lấy danh sách group_id mà role có quyền truy cập"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT group_id
            FROM role_group_permissions
            JOIN roles ON roles.id = role_group_permissions.role_id
            WHERE roles.role_name = %s
        """, (role_name,))
        group_ids = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return group_ids
    except Exception as e:
        return []
    
def update_role_group_permissions(role_name, group_ids):
    """Cập nhật quyền truy cập của role vào các group"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        # Xóa tất cả quyền cũ của role
        cursor.execute("DELETE FROM role_group_permissions WHERE role_id = (SELECT id FROM roles WHERE role_name = %s)", (role_name,))
        
        # Thêm quyền mới
        cursor.execute("SELECT id FROM roles WHERE role_name = %s", (role_name,))
        role_id = cursor.fetchone()
        if role_id:
            role_id = role_id[0]
            for group_id in group_ids:
                cursor.execute(
                    "INSERT INTO role_group_permissions (role_id, group_id) VALUES (%s, %s)",
                    (role_id, group_id)
                )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False
    
def delete_role(role_name):
    """Xóa role khỏi database và các quyền liên quan, bao gồm xóa user_roles liên kết"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        # Lấy role_id dựa trên role_name
        cursor.execute("SELECT id FROM roles WHERE role_name = %s", (role_name,))
        role_id = cursor.fetchone()
        if not role_id:
            return False
        role_id = role_id[0]

        # Xóa các bản ghi trong user_roles liên kết với role_id
        cursor.execute("DELETE FROM user_roles WHERE role_id = %s", (role_id,))

        # Xóa các quyền liên quan trong role_group_permissions
        cursor.execute("DELETE FROM role_group_permissions WHERE role_id = %s", (role_id,))

        # Xóa role khỏi bảng roles
        cursor.execute("DELETE FROM roles WHERE id = %s", (role_id,))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False
    
def add_role(role_name):
    """Thêm role mới vào database"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Kiểm tra nếu role đã tồn tại
        cursor.execute("SELECT COUNT(*) FROM roles WHERE role_name = %s", (role_name,))
        if cursor.fetchone()[0] > 0:
            return False
        
        # Thêm role mới
        cursor.execute("INSERT INTO roles (role_name) VALUES (%s)", (role_name,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False
    
def get_available_roles() -> List[str]:
    """Lấy danh sách các role có sẵn từ database"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role_name FROM roles")
        roles = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return roles
    except Exception as e:
        return ["user"]