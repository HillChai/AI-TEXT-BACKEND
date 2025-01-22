from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
from mylogger import logger

# 引入异步 Redis 客户端
import aioredis

# 异步 Redis 客户端
redis_client = aioredis.from_url(
    settings.redis_url, 
    decode_responses=True, 
    password="cuipi123"
)

# 异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True  # 设置为 True 可用于调试，生产环境建议关闭
)

# 异步会话工厂
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency：获取异步数据库会话
async def get_db():
    async with async_session_maker() as session:
        yield session


# 配置
LOGIN_ATTEMPT_LIMIT = 5  # 最大尝试次数
DELAY_MULTIPLIER = 2     # 延迟时间倍数（秒）
DELAY_BASE = 2
MAX_ATTEMPTS=15

async def get_delay(username: str) -> int:
    """
    根据登录尝试次数计算动态延迟
    """
    attempts = int(await redis_client.get(f"{username}:attempts") or 0)
    if attempts > LOGIN_ATTEMPT_LIMIT:
        logger.info("启动延迟登录")
        return DELAY_BASE ** (attempts - LOGIN_ATTEMPT_LIMIT)
    
    if attempts > MAX_ATTEMPTS:
        logger.info("15分钟暂时无法登录")
        await redis_client.set(f"{username}:locked", "1", ex=900)  # 锁定15分钟
        raise HTTPException(status_code=403, detail="Account temporarily locked")

    return 0