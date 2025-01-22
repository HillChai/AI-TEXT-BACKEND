from database import get_db
from models import User
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def reset_model_quota():
    async for db in get_db():  # 从 get_db 获取数据库会话
        try:
            # 更新 basic 用户
            result_basic = await db.execute(
                update(User)
                .where(User.membership_type == "basic")
                .values(model_quota=10, updated_at=datetime.now())
            )

            # 更新 premium 用户
            result_premium = await db.execute(
                update(User)
                .where(User.membership_type == "premium")
                .values(model_quota=100, updated_at=datetime.now())
            )

            await db.commit()  # 提交所有更新
        except Exception as e:
            logger.error(f"Error updating model quota: {e}")
