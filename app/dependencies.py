from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.database import get_clickhouse_client, get_mysql_connection
from app.utils.redis import redis_client
from app.services.user_service import get_user_role
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from config import APP_SECRET_KEY, APP_ALGORITHM, APP_ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# def get_current_user(token: str = Depends(oauth2_scheme)):
#     if not token:
#         raise HTTPException(status_code=401, detail="Invalid token")
#     return token

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=APP_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, APP_SECRET_KEY, algorithm=APP_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, APP_SECRET_KEY, algorithms=[APP_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

def get_admin_user(username: str = Depends(get_current_user)):
    role = get_user_role(username)
    if role != "superadmin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return username

def init_clients():
    global clickhouse_client, mysql_conn
    clickhouse_client = get_clickhouse_client()
    mysql_conn = get_mysql_connection()