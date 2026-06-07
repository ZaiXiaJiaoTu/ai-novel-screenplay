"""Pydantic models for validating LLM structured outputs.

These models serve as the canonical output schema for each task type,
enabling structured-output support where the provider allows it and
falling back to local parsing otherwise.
"""

from typing import Literal

from pydantic import BaseModel, Field


FACT_TYPE_LITERAL = Literal[
    "身份",
    "外貌",
    "性格",
    "能力",
    "物品",
    "关系",
    "立场",
    "目标",
    "当前状态",
]

VALID_FACT_TYPES: frozenset[str] = frozenset(
    {
        "身份",
        "外貌",
        "性格",
        "能力",
        "物品",
        "关系",
        "立场",
        "目标",
        "当前状态",
    }
)


class CharacterFactOutput(BaseModel):
    fact_type: FACT_TYPE_LITERAL = Field(..., description="事实类别")
    content: str = Field(..., description="事实内容", min_length=1)


class CharacterIncrementOutput(BaseModel):
    name: str = Field(..., description="人物标准名称", min_length=1)
    facts: list[CharacterFactOutput] = Field(default_factory=list)


class PlotEventOutput(BaseModel):
    content: str = Field(..., description="剧情事件内容", min_length=1)
    source_chapter_start: int = Field(..., ge=1, description="起始章节编号")
    source_chapter_end: int = Field(..., ge=1, description="结束章节编号")


class PlotEventSplitOutput(BaseModel):
    events: list[PlotEventOutput] = Field(..., description="剧情事件列表", min_length=1)
    characters: list[CharacterIncrementOutput] = Field(default_factory=list)


class ConsolidatedCharacterOutput(BaseModel):
    name: str = Field(..., description="人物标准名称", min_length=1)
    profile: str = Field(..., description="整合后人物档案", min_length=1)


class CharacterConsolidationOutput(BaseModel):
    characters: list[ConsolidatedCharacterOutput] = Field(
        ..., description="整合后人物列表"
    )
