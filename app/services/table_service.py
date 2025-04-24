from app.utils.database import get_mysql_connection

def get_all_tables():
    """Lấy tất cả bảng trong hệ thống"""
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

def add_table(table_name, description):
    """Thêm bảng mới"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tables (table_name, description)
            VALUES (%s, %s)
        """, (table_name, description))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False

def update_table(old_table_name, new_table_name, description):
    """Cập nhật thông tin bảng"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tables 
            SET table_name = %s, description = %s 
            WHERE table_name = %s
        """, (new_table_name, description, old_table_name))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False

def delete_table(table_name):
    """Xóa bảng"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM tables 
            WHERE table_name = %s
        """, (table_name,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False
