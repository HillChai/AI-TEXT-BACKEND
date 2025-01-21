from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from schemas import QuestionCreate, QuestionResponse, QuestionUpdate
from crud import question as crud_question
from crud.question import get_questions_by_user
from datetime import date
from models import Question
from database import get_db
from sqlalchemy import func
from mylogger import logger

# 初始化 APIRouter
router = APIRouter()

@router.post("/", response_model=QuestionResponse, summary="创建问题")
def create_question_api(question: QuestionCreate, db: Session = Depends(get_db)):
    """
    创建一个新的问题。
    """
    return crud_question.create_question(db, question)


# 分页读取历史记录并按日期分组
@router.get("/history", response_model=List[dict])
async def get_questions_history(
    user_id: int = Query(..., description="用户ID，必须为整数"),
    page: int = Query(1, ge=1, description="分页页码，默认为1"),
    limit: int = Query(10, ge=1, le=100, description="分页大小，默认为10，最大值100"),
    db: Session = Depends(get_db)
):
    # 查询所有属于用户的记录
    all_questions = get_questions_by_user(db, user_id)
    if not all_questions:
        raise HTTPException(status_code=404, detail="No history found.")

    # 按日期分组问题
    grouped_data = {}
    for question in all_questions:
        created_date = question.created_at.date()
        if created_date not in grouped_data:
            grouped_data[created_date] = []
        grouped_data[created_date].append({
            "id": question.id,
            "question_content": question.question_content,
            "answer_content": question.answer_content,
            "user_id": question.user_id,
            "prompt_id": question.prompt_id,
            "created_at": question.created_at.strftime("%Y-%m-%d"),  # 只返回日期部分
            "updated_at": question.updated_at.strftime("%Y-%m-%d"),
        })

    # 转换为列表并按日期排序
    grouped_list = [{"date": str(date), "questions": questions} for date, questions in grouped_data.items()]
    grouped_list.sort(key=lambda x: x["date"], reverse=True)  # 日期降序排序

    # 按日期分页
    start = (page - 1) * limit
    end = start + limit
    paginated_data = grouped_list[start:end]

    # print("返回数据:", paginated_data)

    return paginated_data


@router.get("/{question_id}", response_model=QuestionResponse, summary="获取问题详情")
def get_question_api(question_id: int, db: Session = Depends(get_db)):
    """
    根据问题 ID 获取问题详情。
    """
    question = crud_question.get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.get("/", response_model=list[QuestionResponse], summary="获取问题列表")
def list_questions_api(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    获取问题列表，支持分页。
    """
    return crud_question.get_all_questions(db, skip, limit)


@router.put("/update-by-original-content")
def update_by_original_content(request: dict, db: Session = Depends(get_db)):
    # 获取请求参数
    original_content = request.get("original_content")
    question_content = request.get("question_content")
    answer_content = request.get("answer_content")

    # 参数校验
    if not original_content:
        raise HTTPException(status_code=400, detail="Original content is required")
    if not question_content and not answer_content:
        raise HTTPException(status_code=400, detail="At least one of question_content or answer_content is required")

    # 查找记录
    logger.info(f"Received original_content: {original_content}")
    question = db.query(Question).filter(
        (Question.question_content == original_content) |
        (Question.answer_content == original_content)
    ).first()
    if question:
        logger.info(f"Found question: {question}")
    else:
        logger.info("No matching question found")

    # 检查记录是否存在
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # 更新记录
    if question_content:
        question.question_content = question_content
    if answer_content:
        question.answer_content = answer_content

    # 提交更改
    db.commit()

    return {"question_id": question.id, "message": "Update successful"}


@router.put("/{question_id}", response_model=QuestionResponse, summary="更新问题")
def update_question_api(question_id: int, question_update: QuestionUpdate, db: Session = Depends(get_db)):
    """
    更新问题内容。
    """
    updated_question = crud_question.update_question(db, question_id, question_update)
    if not updated_question:
        raise HTTPException(status_code=404, detail="Question not found")
    return updated_question

@router.delete("/{question_id}", response_model=QuestionResponse, summary="删除问题")
def delete_question_api(question_id: int, db: Session = Depends(get_db)):
    """
    删除指定问题。
    """
    deleted_question = crud_question.delete_question(db, question_id)
    if not deleted_question:
        raise HTTPException(status_code=404, detail="Question not found")
    return deleted_question


