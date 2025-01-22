from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_type = Column(String, default="user")  # 'user' or 'admin'
    status = Column(String, default="active")  # 'active', 'blacklisted'
    model_quota = Column(Integer, default=0)
    membership_type = Column(String, default="no")  # 'basic', 'premium'
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    questions = relationship("Question", back_populates="user")
    prompts = relationship("Prompt", back_populates="user")

class Question(Base):
    __tablename__ = "questions_and_answers"
    id = Column(Integer, primary_key=True, index=True)
    question_content = Column(Text, nullable=False)
    answer_content = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="questions")
    prompt = relationship("Prompt", back_populates="questions")

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="prompts")
    questions = relationship("Question", back_populates="prompt")
