from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import QuestionCreate, QuestionResponse, QuestionUpdate
from crud import question as crud_question
from crud.question import get_questions_by_user
from models import Question
from database import get_db
from mylogger import logger
from utils import get_current_user
from sqlalchemy import select

# 初始化 APIRouter
router = APIRouter()

@router.post("/", response_model=QuestionResponse, summary="创建问题")
async def create_question_api(
    question: QuestionCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 添加 JWT 认证
):
    """
    创建一个新的问题。
    """
    question.user_id = current_user.id  # 将当前用户 ID 绑定到问题中
    return await crud_question.create_question(db, question)


# 分页读取历史记录并按日期分组
@router.get("/history", response_model=List[dict], summary="分页读取历史记录并按日期分组")
async def get_questions_history(
    page: int = Query(1, ge=1, description="分页页码，默认为1"),
    limit: int = Query(10, ge=1, le=100, description="分页大小，默认为10，最大值100"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 添加 JWT 认证
):
    # 查询所有属于用户的记录
    all_questions = await get_questions_by_user(db, current_user.id)
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
    # logger.info(f"grouped_list:{len(grouped_list)}")

    # 按日期分页
    # logger.info(f"page,limit:{page},{limit}")
    start = (page - 1) * limit
    end = start + limit
    paginated_data = grouped_list[start:end]
    # logger.info(f"start,end:{start},{end}")
    
    # logger.info(f"paginated_data:{len(paginated_data)}")

    return paginated_data


@router.get("/{question_id}", response_model=QuestionResponse, summary="获取问题详情")
async def get_question_api(
    question_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 添加 JWT 认证
    ):
    """
    根据问题 ID 获取问题详情。
    """
    question = await crud_question.get_question_by_id(db, question_id)
    if not question or question.user_id != current_user.id:  # 验证用户权限
        raise HTTPException(status_code=403, detail="Permission denied")
    return question

@router.get("/", response_model=List[QuestionResponse], summary="获取问题列表")
async def list_questions_api(
    skip: int = 0, 
    limit: int = 10, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 添加 JWT 认证
):
    """
    获取问题列表，支持分页。
    """
    return await crud_question.get_all_questions(db, skip, limit, user_id=current_user.id)  # 限制为当前用户的问题


@router.put("/update-by-original-content", summary="通过原始内容更新问题")
async def update_by_original_content(
    request: dict, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 添加 JWT 认证
):
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
    result = await db.execute(
        select(Question).where(
            (Question.question_content == original_content) |
            (Question.answer_content == original_content)
        )
    )
    question = result.scalars().first()

    # 检查记录是否存在
    if not question or question.user_id != current_user.id:  # 验证用户权限:
        raise HTTPException(status_code=404, detail="Question not found")

    logger.info(f"Found question: {question}")

    # 更新记录
    if question_content:
        question.question_content = question_content
    if answer_content:
        question.answer_content = answer_content

    # 提交更改
    await db.commit()

    return {"question_id": question.id, "message": "Update successful"}


@router.put("/{question_id}", response_model=QuestionResponse, summary="更新问题")
async def update_question_api(
    question_id: int, 
    question_update: QuestionUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 添加 JWT 认证
):
    """
    更新问题内容。
    """
    question = await crud_question.get_question_by_id(db, question_id)
    if not question or question.user_id != current_user.id:  # 验证用户权限
        raise HTTPException(status_code=403, detail="Permission denied")
    
    updated_question = await crud_question.update_question(db, question_id, question_update)
    return updated_question

@router.delete("/{question_id}", response_model=QuestionResponse, summary="删除问题")
async def delete_question_api(
    question_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 添加 JWT 认证
):
    """
    删除指定问题。
    """
    question = await crud_question.get_question_by_id(db, question_id)
    if not deleted_question or question.user_id != current_user.id:  # 验证用户权限
        raise HTTPException(status_code=404, detail="Question not found")
    
    deleted_question = await crud_question.delete_question(db, question_id)
    return deleted_question
