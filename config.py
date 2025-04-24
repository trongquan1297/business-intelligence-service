# config.py
from dotenv import load_dotenv
import os

# Load file .env
load_dotenv()

REDSHIFT_CONFIG = {
    "dbname": os.getenv("REDSHIFT_DB", "your_redshift_database"),
    "user": os.getenv("REDSHIFT_USER", "your_redshift_username"),
    "password": os.getenv("REDSHIFT_PASSWORD", "your_redshift_password"),
    "host": os.getenv("REDSHIFT_HOST", "your_redshift_cluster_endpoint"),
    "port": os.getenv("REDSHIFT_PORT", "5439")
}

# Cấu hình Clickhouse
CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'port': int(os.getenv('CLICKHOUSE_PORT', 9000)),
    'user': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', ''),
    'database': os.getenv('CLICKHOUSE_DATABASE', 'analytics')
}

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'mysql'),
    'password': os.getenv('MYSQL_PASSWORD', 'mysql'),
    'database': os.getenv('MYSQL_DATABASE', 'analytics')
}

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'), 
    'port': os.getenv('REDIS_PORT', '6379'),       
    'db': os.getenv('REDIS_DB', '0'),
    'username': os.getenv('REDIS_USERNAME', 'default'),
    'password': os.getenv('REDIS_PASSWORD', 'default')
}

AUTHEN_CONFIG = {
    'authenHost': os.getenv('URL_AUTHENICATION_SERVICE'),
    'appUrl': os.getenv('APP_URL'),
    'authenClientId': os.getenv('AUTHENTICATION_CLIENT_ID'),
    'authenClientSecret': os.getenv('AUTHENTICATION_CLIENT_SECRET'),
    'authenApiKey': os.getenv('AUTHENTICATION_API_KEY')
}

APP_ENV = os.getenv('APP_ENV', 'develop')
APP_URL = os.getenv('APP_URL', 'http://localhost:8501')
APP_SECRET_KEY=os.getenv('APP_SECRET_KEY', '')
APP_ALGORITHM=os.getenv('APP_ALGORITHM', 'HS256')
APP_ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv('APP_ACCESS_TOKEN_EXPIRE_MINUTES', 30))

# OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

MAX_ATTEMPTS =  int(os.getenv('MAX_ATTEMPTS', 5)) # Giới hạn số lần đăng nhập sai
LOCKOUT_TIME = int(os.getenv('LOCKOUT_TIME', 300)) # Thời gian khoá nếu đăng nhập thất bại

BI_FRONTEND_URL = os.environ.get("BI_FRONTEND_URL", "http://localhost:3000")


    
