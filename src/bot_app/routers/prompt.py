from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.bot_app.schemas.prompt import (
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplateUpdate,
)
from src.llm.prompt import PromptManager

router = APIRouter(prefix="/prompts", tags=["prompts"])


# 创建一个 PromptManager 实例
def get_prompt_manager():
    return PromptManager()


@router.post("/create", response_model=dict, status_code=201)
async def create_prompt_template(
    prompt: PromptTemplateCreate,
    prompt_manager: PromptManager = Depends(get_prompt_manager),
):
    """创建新的提示词模板"""
    template_id = prompt_manager.create_template(
        system_prompt=prompt.system_prompt,
        name=prompt.name,
        description=prompt.description,
    )

    if template_id is None:
        raise HTTPException(status_code=500, detail="创建提示词模板失败")

    return {"id": template_id, "message": "提示词模板创建成功"}


@router.get("/list", response_model=List[PromptTemplateResponse])
async def list_prompt_templates(
    prompt_manager: PromptManager = Depends(get_prompt_manager),
):
    """获取所有提示词模板"""
    templates = prompt_manager.list_templates()
    return templates


@router.get("/by_name/{name}", response_model=PromptTemplateResponse)
async def get_prompt_template_by_name(
    name: str, prompt_manager: PromptManager = Depends(get_prompt_manager)
):
    """通过名称获取提示词模板"""
    template = prompt_manager.get_template_by_name(name)
    if template is None:
        raise HTTPException(status_code=404, detail=f"提示词模板 '{name}' 不存在")
    return template


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: int, prompt_manager: PromptManager = Depends(get_prompt_manager)
):
    """获取指定ID的提示词模板"""
    template = prompt_manager.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail=f"提示词模板 {template_id} 不存在")
    return template


@router.put("/{template_id}", response_model=dict)
async def update_prompt_template(
    template_id: int,
    prompt: PromptTemplateUpdate,
    prompt_manager: PromptManager = Depends(get_prompt_manager),
):
    """更新提示词模板"""
    # 检查模板是否存在
    existing_template = prompt_manager.get_template(template_id)
    if existing_template is None:
        raise HTTPException(status_code=404, detail=f"提示词模板 {template_id} 不存在")

    # 更新模板
    success = prompt_manager.update_template(
        template_id=template_id,
        system_prompt=prompt.system_prompt,
        name=prompt.name,
        description=prompt.description,
    )

    if not success:
        raise HTTPException(status_code=500, detail="更新提示词模板失败")

    return {"message": "提示词模板更新成功"}


@router.delete("/{template_id}", response_model=dict)
async def delete_prompt_template(
    template_id: int, prompt_manager: PromptManager = Depends(get_prompt_manager)
):
    """删除提示词模板"""
    # 检查模板是否存在
    existing_template = prompt_manager.get_template(template_id)
    if existing_template is None:
        raise HTTPException(status_code=404, detail=f"提示词模板 {template_id} 不存在")

    # 删除模板
    success = prompt_manager.delete_template(template_id)

    if not success:
        raise HTTPException(status_code=500, detail="删除提示词模板失败")

    return {"message": "提示词模板删除成功"}
