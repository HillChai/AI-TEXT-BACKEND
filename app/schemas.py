from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


# 用户相关模型
class UserBase(BaseModel):
    username: str
    user_type: Optional[str] = "user"  # 默认为普通用户
    status: Optional[str] = "active"  # 默认为活跃状态
    model_quota: Optional[int] = 0  # 调用模型的额度

class UserCreate(UserBase):
    password: str  # 创建用户时需要提供密码

class UserUpdate(BaseModel):
    username: Optional[str]
    user_type: Optional[str]
    status: Optional[str]
    model_quota: Optional[int]

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 问题和答案相关模型
class QuestionBase(BaseModel):
    question_content: str

class QuestionCreate(QuestionBase):
    prompt_id: Optional[int]  # 可以关联一个提示 ID
    user_id: int

class QuestionUpdate(BaseModel):
    question_content: Optional[str]
    answer_content: Optional[str]
    prompt_id: Optional[int]

class QuestionResponse(QuestionBase):
    id: int
    answer_content: Optional[str]
    user_id: int
    prompt_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 提示相关模型
class PromptBase(BaseModel):
    content: str

class PromptCreate(PromptBase):
    user_id: int  # 关联创建用户 ID

class PromptUpdate(BaseModel):
    content: Optional[str]

class PromptResponse(PromptBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 综合调用记录（示例参考）
class CallRecordCreate(BaseModel):
    text: str
    prompt: str
    result: str

    class Config:
        from_attributes = True


class HistoryItem(BaseModel):
    date: str
    questions: List[QuestionResponse]  # 每天的问答记录