from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from schemas import UserCreate, UserUpdate
from passlib.context import CryptContext

# 配置密码哈希算法
pwd_context = CryptContext(
    schemes=["bcrypt"],  # 指定使用 bcrypt 算法
    deprecated="auto",   # 自动标记过时算法
    bcrypt__rounds=10    # 设置 bcrypt 的哈希复杂度
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 验证用户输入的密码是否正确
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 创建用户
async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(
        username=user.username,
        password_hash=hash_password(user.password),  # 使用哈希密码
        user_type=user.user_type,
        status=user.status,
        model_quota=10,
        membership_type='basic',
    )
    db.add(db_user)
    await db.commit()  # 异步提交
    await db.refresh(db_user)  # 异步刷新
    return db_user

# 根据 ID 获取用户
async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))  # 异步执行查询
    return result.scalars().first()  # 获取查询结果

# 根据用户名获取用户
async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))  # 异步执行查询
    return result.scalars().first()  # 获取查询结果

# 获取所有用户
async def get_users(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(User).offset(skip).limit(limit))  # 异步分页查询
    return result.scalars().all()  # 返回所有结果

# 更新用户
async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate):
    db_user = await get_user_by_id(db, user_id)  # 异步获取用户
    if not db_user:
        return None
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, key, value)  # 更新字段
    await db.commit()  # 异步提交
    await db.refresh(db_user)  # 异步刷新
    return db_user

# 删除用户
async def delete_user(db: AsyncSession, user_id: int):
    db_user = await get_user_by_id(db, user_id)  # 异步获取用户
    if not db_user:
        return None
    await db.delete(db_user)  # 异步删除
    await db.commit()  # 异步提交
    return db_user
