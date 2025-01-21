from sqlalchemy.orm import Session
from models import Question
from schemas import QuestionCreate, QuestionUpdate, CallRecordCreate
from mylogger import logger
from fastapi import HTTPException
from models import User
from datetime import datetime

# 创建问题
def create_question(db: Session, question: QuestionCreate):
    db_question = Question(
        question_content=question.question_content,
        user_id=question.user_id,
        prompt_id=question.prompt_id,
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


# 根据 ID 获取问题
def get_question_by_id(db: Session, question_id: int):
    return db.query(Question).filter(Question.id == question_id).first()


# 获取用户的所有问题
def get_questions_by_user(db: Session, user_id: int):
    return db.query(Question).filter(Question.user_id == user_id).order_by(Question.created_at.desc()).all()


# 获取所有问题
def get_all_questions(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Question).offset(skip).limit(limit).all()


# 更新问题
def update_question(db: Session, question_id: int, question_update: QuestionUpdate):
    db_question = get_question_by_id(db, question_id)
    if not db_question:
        return None
    for key, value in question_update.dict(exclude_unset=True).items():
        setattr(db_question, key, value)
    db.commit()
    db.refresh(db_question)
    return db_question


# 删除问题
def delete_question(db: Session, question_id: int):
    db_question = get_question_by_id(db, question_id)
    if not db_question:
        return None
    db.delete(db_question)
    db.commit()
    return db_question


# GPT API调用相关
def create_call_record(db: Session, user_id: int, question_content: str, prompt_id: int, answer_content: str = None):
    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # 检查用户的 model_quota 是否足够
    if user.model_quota <= 0:
        raise HTTPException(status_code=403, detail="Insufficient model quota")
    
    """
    创建问题记录并存储在 questions_and_answers 表中。
    """
    record = Question(
        question_content=question_content,
        answer_content=answer_content,
        user_id=user_id,
        prompt_id=prompt_id
    )
    db.add(record)

    # 减少用户的 model_quota
    user.model_quota -= 1
    user.updated_at = datetime.now()

    db.commit()

    db.refresh(record)
    return record

def get_existing_answer(db: Session, question_content: str, prompt_id: int, user_id: int):
    """
    查询是否已存在匹配的提问内容和提示词的记录。
    """
    question_and_answer = db.query(Question).filter(
        Question.user_id == user_id,
        Question.question_content == question_content,
        Question.prompt_id == prompt_id
    ).first()
    
    if question_and_answer:
        # 再次验证 user_id 是否正确
        if question_and_answer.user_id == user_id:
            logger.info(f"找到记录: {question_and_answer}")
            return question_and_answer
        else:
            logger.warning("记录存在，但 user_id 不匹配")
            return False
    else:
        logger.info("没有记录")
        return False 
    

    