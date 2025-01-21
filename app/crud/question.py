from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from models import Question, User
from schemas import QuestionCreate, QuestionUpdate
from mylogger import logger
from fastapi import HTTPException
from datetime import datetime

# 创建问题
async def create_question(db: AsyncSession, question: QuestionCreate):
    db_question = Question(
        question_content=question.question_content,
        user_id=question.user_id,
        prompt_id=question.prompt_id,
    )
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)
    return db_question

# 根据 ID 获取问题
async def get_question_by_id(db: AsyncSession, question_id: int):
    result = await db.execute(select(Question).where(Question.id == question_id))
    return result.scalars().first()

# 获取用户的所有问题
async def get_questions_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Question)
        .where(Question.user_id == user_id)
        .order_by(Question.created_at.desc())
    )
    return result.scalars().all()

# 获取所有问题
async def get_all_questions(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(Question).offset(skip).limit(limit))
    return result.scalars().all()

# 更新问题
async def update_question(db: AsyncSession, question_id: int, question_update: QuestionUpdate):
    db_question = await get_question_by_id(db, question_id)
    if not db_question:
        return None
    for key, value in question_update.dict(exclude_unset=True).items():
        setattr(db_question, key, value)
    await db.commit()
    await db.refresh(db_question)
    return db_question

# 删除问题
async def delete_question(db: AsyncSession, question_id: int):
    db_question = await get_question_by_id(db, question_id)
    if not db_question:
        return None
    await db.delete(db_question)
    await db.commit()
    return db_question

# GPT API调用相关
async def create_call_record(db: AsyncSession, user_id: int, question_content: str, prompt_id: int, answer_content: str = None):
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 检查用户的 model_quota 是否足够
    if user.model_quota <= 0:
        raise HTTPException(status_code=403, detail="Insufficient model quota")
    
    # 创建问题记录并存储在 questions_and_answers 表中
    record = Question(
        question_content=question_content,
        answer_content=answer_content,
        user_id=user_id,
        prompt_id=prompt_id,
    )
    db.add(record)

    # 减少用户的 model_quota
    user.model_quota -= 1
    user.updated_at = datetime.now()

    await db.commit()
    await db.refresh(record)
    return record

# 查询是否已存在匹配的提问内容和提示词的记录
async def get_existing_answer(db: AsyncSession, question_content: str, prompt_id: int, user_id: int):
    try:
        result = await db.execute(
            select(Question)
            .where(
                Question.user_id == user_id,
                Question.question_content == question_content,
                Question.prompt_id == prompt_id,
            )
        )
        question_and_answer = result.scalars().first()

        if question_and_answer:
            logger.info(f"找到记录: {question_and_answer}")
            return question_and_answer
        else:
            logger.info("没有记录")
            return None
    except NoResultFound:
        logger.info("没有记录")
        return None
