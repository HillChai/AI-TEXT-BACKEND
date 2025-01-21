from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
# import redis

# redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True, password="cuipi123")

# 引入异步 Redis 客户端
import aioredis

# 替换 redis_client 为异步客户端
redis_client = aioredis.from_url(settings.redis_url, decode_responses=True, password="cuipi123")

# engine = create_engine(settings.DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 异步数据库引擎
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# 异步会话工厂
async_session_maker = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


Base = declarative_base()

# Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# Dependency：获取异步数据库会话
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()