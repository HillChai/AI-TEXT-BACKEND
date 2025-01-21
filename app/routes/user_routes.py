from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from crud.user import (
    get_user_by_username,
    create_user,
    get_user_by_id,
    get_users,
    update_user as crud_update_user,
    delete_user as crud_delete_user,
    verify_password,
)
from schemas import UserCreate, UserResponse, UserUpdate
from utils import (
    create_jwt, 
    add_token_to_device_list, 
    get_current_user, 
    oauth2_scheme,
    decode_jwt,
    add_to_blacklist,
    is_token_valid_for_user,
)
from database import get_db
from config import settings

# 初始化 APIRouter
router = APIRouter()

# 用户注册
@router.post("/register", response_model=UserResponse, summary="用户注册")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    db_user = create_user(db, user)
    return db_user

# 用户登录
@router.post("/login", summary="用户登录")
def login(user: UserCreate, db: Session = Depends(get_db)):
    # 查询用户
    db_user = get_user_by_username(db, user.username)
    if not db_user:
        raise HTTPException(status_code=400, detail="用户不存在")

    # 验证密码
    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    # 生成 JWT
    token = create_jwt({"sub": db_user.id})

    # 限制登录设备数量
    max_devices = settings.max_devices
    add_token_to_device_list(db_user.id, token, max_devices)

    # 构建用户信息，排除敏感数据
    user_info = {
        "user_id": db_user.id,
        "username": db_user.username,
        "user_type": db_user.user_type,
        "status": db_user.status,
        "model_quota": db_user.model_quota,
        "membership_type": db_user.membership_type,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
    }

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_info,
    }


# 用户登出
@router.post("/logout", summary="用户登出")
def logout(token: str = Depends(oauth2_scheme)):
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的 Token")

    # 将 Token 加入黑名单
    jti = payload.get("jti")
    expiration = payload.get("exp") - datetime.now().timestamp()
    add_to_blacklist(jti, int(expiration))

    return {"msg": "已成功登出"}

# 获取当前用户信息
@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

# 受保护的路由
@router.get("/protected", summary="受保护的路由")
def protected_route(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_jwt(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的 Token")

    # 检查 Token 是否在 Redis 的设备列表中
    if not is_token_valid_for_user(user_id, token):
        raise HTTPException(status_code=401, detail="Token 已失效或被移除")

    return {"msg": f"欢迎, 用户 {user_id}"}

# 创建用户（管理员功能）
@router.post("/", response_model=UserResponse, summary="创建用户")
def create_user_api(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return create_user(db, user)

# 获取用户详情
@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return db_user

# 列出所有用户
@router.get("/", response_model=list[UserResponse], summary="列出用户")
def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_users(db, skip, limit)

# 更新用户信息
@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    db_user = crud_update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return db_user

# 删除用户
@router.delete("/{user_id}", response_model=UserResponse, summary="删除用户")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud_delete_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return db_user
