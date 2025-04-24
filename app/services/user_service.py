from app.utils.database import get_mysql_connection
from typing import List, Optional, Dict
import bcrypt

def create_user(username, password, email):
    """Tạo tài khoản mới với mật khẩu đã hash"""
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode()

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        sql = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, hashed_password, email))
        conn.commit()

        print("✅ Tạo tài khoản thành công!")
        return True
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False
    finally:
        conn.close()

def get_user_role(username: str) -> str:
    """Lấy role của user từ database"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        sql = """
        SELECT r.role_name
        FROM roles r
        JOIN user_roles ur ON r.id = ur.role_id
        WHERE ur.username = %s
        """
        cursor.execute(sql, (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        return None

def get_users() -> List[Dict]:
    """Lấy danh sách tất cả user từ database"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, active FROM users")
        users = cursor.fetchall()
        
        # Lấy role cho mỗi user từ user_roles
        for user in users:
            role = get_user_role(user['username'])
            user['role'] = role if role else "user"  # Mặc định là "user" nếu không có role
        cursor.close()
        conn.close()
        return users
    except Exception as e:
        return []

def update_user_role_and_active(username: str, role: str, active: bool) -> bool:
    """Cập nhật role và trạng thái active của user"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        # Cập nhật trạng thái active trong bảng users
        cursor.execute("UPDATE users SET active = %s WHERE username = %s", (int(active), username))

        # Xóa role cũ và thêm role mới trong user_roles
        cursor.execute("DELETE FROM user_roles WHERE username = %s", (username,))
        cursor.execute("SELECT id FROM roles WHERE role_name = %s", (role,))
        role_id = cursor.fetchone()
        if role_id:
            cursor.execute("INSERT INTO user_roles (username, role_id) VALUES (%s, %s)", (username, role_id[0]))
        else:
            return False

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False
    
def delete_user(username: str) -> bool:
    """Xóa user khỏi database"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        # Xóa bản ghi trong user_roles trước
        cursor.execute("DELETE FROM user_roles WHERE username = %s", (username,))
        
        # Xóa user khỏi bảng users
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False

def check_sso_user_exists(profile: Dict) -> Optional[str]:
    """Kiểm tra xem người dùng từ SSO đã tồn tại trong database chưa và trả về username nếu có"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        email = profile.get('email')  # SSO trả về email
        if not email:
            return None

        # Kiểm tra xem user đã tồn tại chưa và lấy username
        cursor.execute("SELECT username FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        # Trả về username nếu tìm thấy, ngược lại trả về None
        return result[0] if result else None
    except Exception as e:
        return None
    
def check_user_exists(username, email):
    """Kiểm tra xem username hoặc email đã tồn tại trong database chưa"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        # Kiểm tra username
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        username_exists = cursor.fetchone()[0] > 0
        
        # Kiểm tra email
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
        email_exists = cursor.fetchone()[0] > 0
        
        cursor.close()
        conn.close()
        return username_exists, email_exists
    except Exception as e:
        return False, False