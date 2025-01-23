from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Prompt
from schemas import PromptCreate, PromptUpdate


# 创建提示
async def create_prompt(db: AsyncSession, prompt: PromptCreate):
    db_prompt = Prompt(
        content=prompt.content,
        user_id=prompt.user_id,
    )
    db.add(db_prompt)
    await db.commit()
    await db.refresh(db_prompt)
    return db_prompt


# 根据 ID 获取提示
async def get_prompt_by_id(db: AsyncSession, prompt_id: int):
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    return result.scalars().first()


# 获取用户的所有提示
async def get_prompts_by_user(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    result = await db.execute(
        select(Prompt)
        .where(Prompt.user_id == user_id)
        .order_by(Prompt.created_at.desc())  # 按创建时间降序排序
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


# 获取所有提示
async def get_all_prompts(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(Prompt).offset(skip).limit(limit))
    return result.scalars().all()


# 更新提示
async def update_prompt(db: AsyncSession, prompt_id: int, prompt_update: PromptUpdate):
    db_prompt = await get_prompt_by_id(db, prompt_id)
    if not db_prompt:
        return None
    for key, value in prompt_update.dict(exclude_unset=True).items():
        setattr(db_prompt, key, value)
    await db.commit()
    await db.refresh(db_prompt)
    return db_prompt


# 删除提示
async def delete_prompt(db: AsyncSession, prompt_id: int):
    db_prompt = await get_prompt_by_id(db, prompt_id)
    if not db_prompt:
        return None
    await db.delete(db_prompt)
    await db.commit()
    return db_prompt
