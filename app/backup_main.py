from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from crud import create_call_record, get_existing_answer
# import openai
from openai import OpenAI
from logger import logger
from fastapi.middleware.cors import CORSMiddleware



# Load OpenAI API Key from environment variables
import os
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
if not api_key or not base_url:
    logger.error("API_KEY or BASE_URL not found in environment variables!")
    raise RuntimeError("OpenAI API configuration missing!")

client = OpenAI(api_key=api_key, base_url=base_url)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或者指定实际的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GPTRequest(BaseModel):
    text: str
    prompt: str

@app.post("/gpt")
async def handle_gpt_request(request: GPTRequest, db: Session = Depends(get_db)):
    """
    Handle GPT requests from the frontend.
    """

    # 查询是否有相同题目和提示词的记录
    try:
        existing_record = get_existing_answer(db, text=request.text, prompt=request.prompt)
    except Exception as db_error:
        logger.error(f"Database query failed: {db_error}")
        raise HTTPException(status_code=500, detail="Database query error")

    if existing_record:
        return {
            "result": existing_record.result,
            "source": "database",  # 表明结果来源于数据库
            "status": "success"
        }

    # 如果不存在，则调用 
    # 组合 prompt 和 text
    # input_prompt = f"{request.prompt}\n\n{request.text}"
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": request.prompt},
                {"role": "user", "content": request.text}
            ],
            stream=False,
            max_tokens=500
        )
        logger.debug(f"Response type: {type(response)}")
        logger.debug(f"Response content: {response}")
        # 转换为字典后访问内容
        response_dict = response.to_dict()
        result = response.choices[0].message.content.strip()
        logger.info(f"result:{result}")
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {str(e)}")
  
    # 保存新记录到数据库
    try:
        create_call_record(db, text=request.text, prompt=request.prompt, result=result)
    except Exception as e:
        logger.error(f"Failed to save record to database: {db_error}")
        raise HTTPException(status_code=500, detail="Error saving result to database")

    return {
            "result": result,
            "source": "deepseek",  # 表明结果来源于 GPT
            "status": "success"
        }