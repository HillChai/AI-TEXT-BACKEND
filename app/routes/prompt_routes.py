from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from crud import prompt as crud_prompt
from schemas import PromptCreate, PromptUpdate, PromptResponse

# 初始化 APIRouter
router = APIRouter()

@router.post("/", response_model=PromptResponse, summary="创建提示")
async def create_prompt_api(prompt: PromptCreate, db: AsyncSession = Depends(get_db)):
    """
    创建一个新的提示（Prompt）。
    """
    return await crud_prompt.create_prompt(db, prompt)

@router.get("/{prompt_id}", response_model=PromptResponse, summary="获取提示详情")
async def get_prompt_api(prompt_id: int, db: AsyncSession = Depends(get_db)):
    """
    根据 ID 获取提示详情。
    """
    prompt = await crud_prompt.get_prompt_by_id(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt

@router.get("/", response_model=list[PromptResponse], summary="获取提示列表")
async def list_prompts_api(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """
    获取提示列表，支持分页。
    """
    return await crud_prompt.get_all_prompts(db, skip, limit)

@router.put("/{prompt_id}", response_model=PromptResponse, summary="更新提示")
async def update_prompt_api(prompt_id: int, prompt_update: PromptUpdate, db: AsyncSession = Depends(get_db)):
    """
    更新指定的提示信息。
    """
    updated_prompt = await crud_prompt.update_prompt(db, prompt_id, prompt_update)
    if not updated_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return updated_prompt

@router.delete("/{prompt_id}", response_model=PromptResponse, summary="删除提示")
async def delete_prompt_api(prompt_id: int, db: AsyncSession = Depends(get_db)):
    """
    删除指定的提示。
    """
    deleted_prompt = await crud_prompt.delete_prompt(db, prompt_id)
    if not deleted_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return deleted_prompt
