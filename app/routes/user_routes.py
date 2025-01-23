from crud.prompt import create_prompt, get_prompts_by_user
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
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
from schemas import PromptCreate, UserCreate, UserResponse, UserUpdate
from utils import (
    create_jwt,
    add_token_to_device_list,
    get_current_user,
    oauth2_scheme,
    decode_jwt,
    add_to_blacklist,
    is_token_valid_for_user,
)
from database import get_db, get_delay, redis_client
from config import settings
from mylogger import logger

# 初始化 APIRouter
router = APIRouter()

# 用户注册
@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    new_user = await create_user(db, user)

    # 创建默认 Prompt
    default_prompt = await create_prompt(
        db,
        prompt=PromptCreate(
            content="""
            请根据以下结构回答问题：\n \
            1. 简要回应问题，明确目标和原则。\n \
            2. 详细展开行动方案，每个要点不超过 3 行，逻辑清晰，层次分明。\n \
            3. 引用相关政策或讲话作为支持性论据，不要显得刻意。\n \
            4. 使用朴实流畅的语言，控制答案在 250-300 字范围内，时长约 3 分钟。 \n \
            问题是：
            """
,
            user_id=new_user.id,
        )
    )
    
    return new_user

# 用户登录
@router.post("/login", summary="用户登录")
async def login(user: UserCreate, db: AsyncSession = Depends(get_db)):

    # 检查 Redis 中的延迟
    delay = await get_delay(user.username)
    if delay > 0:
        raise HTTPException(
            status_code=429,
            detail=f"登录尝试过多，请等待 {delay} 秒后再试"
        )
    
    db_user = await get_user_by_username(db, user.username)

    if not db_user:
        # 增加尝试次数
        await redis_client.incr(f"{user.username}:attempts")
        await redis_client.expire(f"{user.username}:attempts", 300)  # 设置过期时间为5分钟
        raise HTTPException(status_code=400, detail="用户不存在")

    if not verify_password(user.password, db_user.password_hash):
        # 增加尝试次数
        await redis_client.incr(f"{user.username}:attempts")
        await redis_client.expire(f"{user.username}:attempts", 300)  # 设置过期时间为5分钟
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    if db_user.status == 'blacklisted':
        raise HTTPException(status_code=400, detail="该账号无法使用")

    # 登录成功，清除 Redis 中的尝试记录
    await redis_client.delete(f"{user.username}:attempts")

    token = create_jwt({"sub": db_user.id})

    max_devices = settings.max_devices
    await add_token_to_device_list(db_user.id, token, max_devices)

    # 查询用户的默认 Prompt（最新添加的）
    prompts = await get_prompts_by_user(db, db_user.id, limit=1)
    prompt_ids = [prompt.id for prompt in prompts]  # 提取所有 prompt 的 ID 列表

    user_info = {
        "user_id": db_user.id,
        "username": db_user.username,
        "user_type": db_user.user_type,
        "status": db_user.status,
        "model_quota": db_user.model_quota,
        "membership_type": db_user.membership_type,
        "prompt_ids": prompt_ids,
    }
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_info,
    }

# 用户登出
@router.post("/logout", summary="用户登出")
async def logout(token: str = Depends(oauth2_scheme)):
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的 Token")

    jti = payload.get("jti")
    expiration = payload.get("exp") - datetime.now().timestamp()
    await add_to_blacklist(jti, int(expiration))

    return {"msg": "已成功登出"}

# 获取当前用户信息
@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

# 受保护的路由
@router.get("/protected", summary="受保护的路由")
async def protected_route(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = decode_jwt(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的 Token")

    if not await is_token_valid_for_user(user_id, token):
        raise HTTPException(status_code=401, detail="Token 已失效或被移除")

    return {"msg": f"欢迎, 用户 {user_id}"}

# 创建用户（管理员功能）
@router.post("/", response_model=UserResponse, summary="创建用户")
async def create_user_api(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return await create_user(db, user)

# 获取用户详情
@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return db_user

# 列出所有用户
@router.get("/", response_model=list[UserResponse], summary="列出用户")
async def list_users(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    return await get_users(db, skip, limit)

# 更新用户信息
@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    db_user = await crud_update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return db_user

# 删除用户
@router.delete("/{user_id}", response_model=UserResponse, summary="删除用户")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await crud_delete_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return db_user
