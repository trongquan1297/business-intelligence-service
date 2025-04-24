import requests
import os
from typing import Dict
from app.utils.redis import redis_client
from config import MAX_ATTEMPTS, LOCKOUT_TIME, BI_FRONTEND_URL
import bcrypt
import redis
from app.utils.database import get_mysql_connection

URL_AUTHENICATION_SERVICE = os.getenv('URL_AUTHENICATION_SERVICE', 'https://appota.example.com')
AUTHENTICATION_API_KEY = os.getenv('AUTHENTICATION_API_KEY')
AUTHENTICATION_CLIENT_ID = os.getenv('AUTHENTICATION_CLIENT_ID')
AUTHENTICATION_CLIENT_SECRET = os.getenv('AUTHENTICATION_CLIENT_SECRET')
APP_URL = os.getenv('APP_URL', 'http://localhost:8501')

class AppotaSSO:
    def get_redirect_url(self) -> str:
        url = f"{URL_AUTHENICATION_SERVICE}/api/token"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': AUTHENTICATION_API_KEY
        }
        
        # Thay đổi redirect_uri để trỏ đến trang callback của frontend
        frontend_url = BI_FRONTEND_URL
        
        payload = {
            'client_id': str(AUTHENTICATION_CLIENT_ID),
            'redirect_uri': f"{frontend_url}/auth/callback",  # Thay đổi ở đây
            'response_type': 'code'
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get('redirect_uri')

    def request_access_token(self, code: str) -> str:
        url = f"{URL_AUTHENICATION_SERVICE}/api/generate/access_token"
        headers = {'Authorization': AUTHENTICATION_API_KEY}
        payload = {
            'client_id': str(AUTHENTICATION_CLIENT_ID),
            'client_secret': AUTHENTICATION_CLIENT_SECRET,
            'authorization_code': code
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get('access_token')

    def get_me(self, token: str) -> Dict:
        url = f"{URL_AUTHENICATION_SERVICE}/api/token/valid"
        headers = {'Authorization': AUTHENTICATION_API_KEY}
        payload = {
            'client_id': str(AUTHENTICATION_CLIENT_ID),
            'access_token': token
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get('user_info')
    
    
def authenticate_user(username: str, password: str) -> bool:
    """
    Xác thực người dùng dựa trên username và password.
    
    Args:
        username (str): Tên đăng nhập của người dùng.
        password (str): Mật khẩu chưa mã hóa để so sánh với mật khẩu đã hash trong DB.
    
    Returns:
        bool: True nếu xác thực thành công, False nếu thất bại.
    
    Raises:
        Exception: Nếu có lỗi khi truy cập cơ sở dữ liệu hoặc Redis.
    """
    try:
        # Kiểm tra giới hạn số lần đăng nhập thất bại
        attempts_key = f"failed_attempts:{username}"
        attempts = int(redis_client.get(attempts_key) or 0)
        if attempts >= MAX_ATTEMPTS:
            remaining_time = redis_client.ttl(attempts_key)
            if remaining_time > 0:
                raise Exception(f"Account locked. Try again in {remaining_time} seconds")
            else:
                redis_client.delete(attempts_key)  # Xóa khóa nếu đã hết thời gian khóa

        # Kết nối tới cơ sở dữ liệu và lấy mật khẩu đã hash
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        # Đóng kết nối
        cursor.close()
        conn.close()

        # Kiểm tra kết quả truy vấn
        if not result:
            # Tăng số lần thử thất bại nếu username không tồn tại
            redis_client.incr(attempts_key)
            redis_client.expire(attempts_key, LOCKOUT_TIME)
            return False

        # So sánh mật khẩu
        hashed_password = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            # Xóa số lần thử thất bại nếu đăng nhập thành công
            redis_client.delete(attempts_key)
            return True
        else:
            # Tăng số lần thử thất bại nếu mật khẩu sai
            redis_client.incr(attempts_key)
            if attempts + 1 >= MAX_ATTEMPTS:
                redis_client.expire(attempts_key, LOCKOUT_TIME)
            return False

    except redis.RedisError as e:
        raise Exception(f"Redis error: {str(e)}")
    except Exception as e:
        raise Exception(f"Authentication error: {str(e)}")