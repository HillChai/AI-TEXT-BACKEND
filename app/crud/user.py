from sqlalchemy.orm import Session
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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 创建用户
def create_user(db: Session, user: UserCreate):
    db_user = User(
        username=user.username,
        password_hash=hash_password(user.password),  # 使用哈希密码
        user_type=user.user_type,
        status=user.status,
        model_quota=user.model_quota,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# 根据 ID 获取用户
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


# 根据用户名获取用户
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


# 获取所有用户
def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()


# 更新用户
def update_user(db: Session, user_id: int, user_update: UserUpdate):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


# 删除用户
def delete_user(db: Session, user_id: int):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    db.delete(db_user)
    db.commit()
    return db_user
