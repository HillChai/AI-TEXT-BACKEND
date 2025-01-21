from sqlalchemy.orm import Session
from models import Prompt
from schemas import PromptCreate, PromptUpdate


# 创建提示
def create_prompt(db: Session, prompt: PromptCreate):
    db_prompt = Prompt(
        content=prompt.content,
        user_id=prompt.user_id,
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt


# 根据 ID 获取提示
def get_prompt_by_id(db: Session, prompt_id: int):
    return db.query(Prompt).filter(Prompt.id == prompt_id).first()


# 获取用户的所有提示
def get_prompts_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(Prompt).filter(Prompt.user_id == user_id).offset(skip).limit(limit).all()


# 获取所有提示
def get_all_prompts(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Prompt).offset(skip).limit(limit).all()


# 更新提示
def update_prompt(db: Session, prompt_id: int, prompt_update: PromptUpdate):
    db_prompt = get_prompt_by_id(db, prompt_id)
    if not db_prompt:
        return None
    for key, value in prompt_update.dict(exclude_unset=True).items():
        setattr(db_prompt, key, value)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt


# 删除提示
def delete_prompt(db: Session, prompt_id: int):
    db_prompt = get_prompt_by_id(db, prompt_id)
    if not db_prompt:
        return None
    db.delete(db_prompt)
    db.commit()
    return db_prompt
