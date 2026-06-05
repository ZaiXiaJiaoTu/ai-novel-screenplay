from pydantic import BaseModel, Field


class PromptTemplateBase(BaseModel):
    template_name: str = Field(min_length=1, max_length=255)
    task_type: str = Field(min_length=1, max_length=100)
    system_prompt: str = Field(min_length=1)
    user_prompt_template: str = Field(min_length=1)
    output_format: str = Field(min_length=1, max_length=50)
    variables: list[str] | None = None
    enabled: bool = True


class PromptTemplateCreate(PromptTemplateBase):
    pass


class PromptTemplateUpdate(BaseModel):
    template_name: str | None = Field(default=None, min_length=1, max_length=255)
    task_type: str | None = Field(default=None, min_length=1, max_length=100)
    system_prompt: str | None = Field(default=None, min_length=1)
    user_prompt_template: str | None = Field(default=None, min_length=1)
    output_format: str | None = Field(default=None, min_length=1, max_length=50)
    variables: list[str] | None = None
    enabled: bool | None = None


class PromptTemplateDetail(PromptTemplateBase):
    template_id: int
    version: int


class PromptTemplateVersionDetail(BaseModel):
    version_id: int
    template_id: int
    version: int
    system_prompt: str
    user_prompt_template: str
    output_format: str
    variables: list[str] | None
