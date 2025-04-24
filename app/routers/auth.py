from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.models import LoginRequest, SSORequest
from app.dependencies import get_current_user, create_access_token
from app.services.auth_service import authenticate_user, AppotaSSO
from app.services.user_service import check_sso_user_exists
import requests
from datetime import timedelta
from typing import Optional
from config import APP_SECRET_KEY, APP_ALGORITHM, APP_ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")





@router.post("/login", response_model=dict)
async def login(request: LoginRequest):
    """
    Đăng nhập bằng username và password.
    Trả về JWT access token nếu xác thực thành công.
    """
    if authenticate_user(request.username, request.password):
        access_token_expires = timedelta(minutes=APP_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": request.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@router.post("/sso", response_model=dict)
async def sso_login(request: SSORequest):
    """
    Đăng nhập qua Appota SSO bằng authorization code.
    Trả về JWT access token nếu xác thực thành công.
    """
    try:
        sso = AppotaSSO()
        # Yêu cầu access token từ authorization code
        access_token = sso.request_access_token(request.authorization_code)
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to obtain access token")

        # Lấy thông tin người dùng từ access token
        user_info = sso.get_me(access_token)
        if not user_info:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to fetch user info from SSO")

        # Kiểm tra xem người dùng có tồn tại trong hệ thống không
        username = check_sso_user_exists(user_info)
        avatar = user_info.get('avatar', None)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User with email {user_info.get('email', 'unknown')} does not exist in the system"
            )

        # Tạo JWT token
        access_token_expires = timedelta(minutes=APP_ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={"sub": username, "avatar_url": avatar}, expires_delta=access_token_expires
        )
        return {"access_token": jwt_token, "token_type": "bearer"}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"SSO request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"SSO authentication failed: {str(e)}")

@router.get("/me", response_model=dict)
async def get_me(current_user: str = Depends(get_current_user)):
    """
    Lấy thông tin người dùng hiện tại dựa trên token.
    """
    return {"username": current_user}

@router.get("/sso/redirect", response_model=dict)
async def get_sso_redirect():
    """
    Lấy URL chuyển hướng để bắt đầu quá trình SSO.
    """
    try:
        sso = AppotaSSO()
        redirect_uri = sso.get_redirect_url()
        if not redirect_uri:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to obtain redirect URL")
        return {"redirect_uri": redirect_uri}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch redirect URL: {str(e)}")