from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database import get_db
from mylogger import logger
from crud.question import create_call_record, get_existing_answer
from crud.prompt import get_prompt_by_id
from config import settings
from openai import OpenAI

# 初始化 OpenAI 客户端
if not settings.API_KEY or not settings.API_URL:
    logger.error("API_KEY or API_URL not configured in settings!")
    raise RuntimeError("OpenAI API configuration missing!")

client = OpenAI(api_key=settings.API_KEY, base_url=settings.API_URL)

# 初始化 APIRouter
router = APIRouter()

# 请求数据模型
class GPTRequest(BaseModel):
    question_content: str
    prompt_id: int
    user_id: int

@router.post("/", summary="处理 GPT 请求")
async def handle_gpt_request(
    request: GPTRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    处理 GPT 请求
    """
    question_content = request.question_content
    prompt_id = request.prompt_id
    user_id = request.user_id

    logger.info(f"current user: {user_id}")

    # 检查是否有缓存记录
    try:
        logger.info("检查是否有缓存")
        existing_record = await get_existing_answer(db, question_content, prompt_id, user_id)
    except Exception as db_error:
        logger.error(f"Database query failed: {db_error}")
        raise HTTPException(status_code=500, detail="Database query error")

    if existing_record:
        return {
            "status": "success",
            "source": "database",
            "result": existing_record.answer_content
        }

    # 调用大模型 API
    try:
        prompt = await get_prompt_by_id(db, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        logger.info(f"prompt_content: {prompt.content}")
        logger.info(f"question_content: {question_content}")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt.content},
                {"role": "user", "content": question_content},
            ],
            stream=False,
            max_tokens=500,
        )
        generated_answer = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise HTTPException(status_code=500, detail="Error calling OpenAI API")

    # 保存结果到数据库
    try:
        new_record = await create_call_record(
            db,
            user_id=user_id,
            question_content=question_content,
            prompt_id=prompt_id,
            answer_content=generated_answer
        )
    except Exception as db_error:
        logger.error(f"Failed to save record to database: {db_error}")
        raise HTTPException(status_code=500, detail="Error saving result to database")

    return {
        "status": "success",
        "source": "generated",
        "result": new_record.answer_content
    }
