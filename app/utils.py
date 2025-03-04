from datetime import datetime, timedelta
from jose import jwt
from config import settings
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, redis_client
from crud.user import get_user_by_id
from mylogger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    payload = decode_jwt(token)

    if datetime.now() > datetime.fromtimestamp(payload["exp"]):
        raise HTTPException(status_code=401, detail="Token expired")

    user_id = int(payload.get("sub"))
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的 Token")
    
    # 检查 Token 是否在设备列表中
    if not await is_token_valid_for_user(user_id, token):
        raise HTTPException(status_code=401, detail="Token 已失效或被移除")
    
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user

def create_jwt(data: dict):
    """生成 JWT"""
    to_encode = data.copy()
    to_encode["sub"] = str(data.get("sub"))  # 确保 sub 字段是字符串
    expire = datetime.now() + timedelta(minutes=settings.jwt_expiration_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_jwt(token: str):
    """验证并解码 JWT"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        # 检查 Token 是否过期
        if payload.get("exp") and payload.get("exp") < datetime.now().timestamp():
            logger.error("Token 已过期")
            return None
        return payload
    except jwt.JWTError as e:
        logger.error(f"JWT 解码错误: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"其他解码错误: {str(e)}")
        return None
    
async def add_to_blacklist(jti: str, expiration: int):
    """将 JWT 加入黑名单"""
    await redis_client.setex(f"blacklist:{jti}", expiration, "blacklisted")

async def is_blacklisted(jti: str) -> bool:
    """检查 JWT 是否在黑名单中"""
    return await redis_client.exists(f"blacklist:{jti}")

async def add_token_to_device_list(user_id: int, token: str, max_devices: int = 3):
    """
    将用户的 Token 添加到 Redis 的设备列表中，限制最大登录设备数量。
    :param user_id: 用户 ID
    :param token: 用户登录时生成的 JWT
    :param max_devices: 最大允许的设备数量（默认 3）
    """
    # Redis 中的键
    redis_key = f"devices:{user_id}"
    
    # 将 Token 添加到列表
    await redis_client.lpush(redis_key, token)
    
    # 限制设备数量
    await redis_client.ltrim(redis_key, 0, max_devices - 1)  # 保留最新的 max_devices 个 Token

    # 设置过期时间，确保 Token 与 JWT 的有效期一致
    await redis_client.expire(redis_key, settings.jwt_expiration_minutes * 60)

async def is_token_valid_for_user(user_id: int, token: str) -> bool:
    """
    检查某个 Token 是否在用户的设备列表中。
    :param user_id: 用户 ID
    :param token: JWT Token
    :return: True 如果 Token 在设备列表中，否则 False
    """
    redis_key = f"devices:{user_id}"
    tokens = await redis_client.lrange(redis_key, 0, -1)
    return token in tokens
