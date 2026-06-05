from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate, PromptTemplateVersion
from app.prompts.default_prompts import DEFAULT_PROMPT_TEMPLATES
from app.schemas.prompt_template_schema import (
    PromptTemplateCreate,
    PromptTemplateDetail,
    PromptTemplateUpdate,
    PromptTemplateVersionDetail,
)


def serialize_template(template: PromptTemplate) -> PromptTemplateDetail:
    return PromptTemplateDetail(
        template_id=template.id,
        template_name=template.template_name,
        task_type=template.task_type,
        system_prompt=template.system_prompt,
        user_prompt_template=template.user_prompt_template,
        output_format=template.output_format,
        variables=template.variables,
        version=template.version,
        enabled=template.enabled,
    )


def serialize_version(version: PromptTemplateVersion) -> PromptTemplateVersionDetail:
    return PromptTemplateVersionDetail(
        version_id=version.id,
        template_id=version.template_id,
        version=version.version,
        system_prompt=version.system_prompt,
        user_prompt_template=version.user_prompt_template,
        output_format=version.output_format,
        variables=version.variables,
    )


def add_version(db: Session, template: PromptTemplate) -> PromptTemplateVersion:
    version = PromptTemplateVersion(
        template_id=template.id,
        version=template.version,
        system_prompt=template.system_prompt,
        user_prompt_template=template.user_prompt_template,
        output_format=template.output_format,
        variables=template.variables,
    )
    db.add(version)
    return version


def create_prompt_template(
    db: Session, payload: PromptTemplateCreate
) -> PromptTemplateDetail:
    template = PromptTemplate(**payload.model_dump(), version=1, is_deleted=False)
    db.add(template)
    db.flush()
    add_version(db, template)
    db.commit()
    db.refresh(template)
    return serialize_template(template)


def seed_default_prompt_templates(db: Session) -> list[PromptTemplateDetail]:
    created_templates: list[PromptTemplateDetail] = []
    for prompt_data in DEFAULT_PROMPT_TEMPLATES:
        existing = db.scalar(
            select(PromptTemplate).where(
                PromptTemplate.task_type == prompt_data["task_type"],
                PromptTemplate.is_deleted.is_(False),
            )
        )
        if existing is not None:
            continue
        template = PromptTemplate(**prompt_data, version=1, is_deleted=False)
        db.add(template)
        db.flush()
        add_version(db, template)
        created_templates.append(serialize_template(template))
    db.commit()
    return created_templates


def list_prompt_templates(
    db: Session,
    *,
    task_type: str | None = None,
    enabled: bool | None = None,
    keyword: str | None = None,
) -> list[PromptTemplateDetail]:
    stmt = select(PromptTemplate).where(PromptTemplate.is_deleted.is_(False))
    if task_type:
        stmt = stmt.where(PromptTemplate.task_type == task_type)
    if enabled is not None:
        stmt = stmt.where(PromptTemplate.enabled.is_(enabled))
    if keyword:
        stmt = stmt.where(PromptTemplate.template_name.ilike(f"%{keyword.strip()}%"))
    templates = db.scalars(stmt.order_by(PromptTemplate.updated_at.desc())).all()
    return [serialize_template(template) for template in templates]


def get_prompt_template_model(db: Session, template_id: int) -> PromptTemplate | None:
    return db.scalar(
        select(PromptTemplate).where(
            PromptTemplate.id == template_id,
            PromptTemplate.is_deleted.is_(False),
        )
    )


def update_prompt_template(
    db: Session, template_id: int, payload: PromptTemplateUpdate
) -> PromptTemplateDetail | None:
    template = get_prompt_template_model(db, template_id)
    if template is None:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(template, field_name, value)
    template.version += 1
    add_version(db, template)
    db.commit()
    db.refresh(template)
    return serialize_template(template)


def delete_prompt_template(db: Session, template_id: int) -> bool | None:
    template = get_prompt_template_model(db, template_id)
    if template is None:
        return None
    template.is_deleted = True
    template.enabled = False
    db.commit()
    return True


def list_prompt_template_versions(
    db: Session, template_id: int
) -> list[PromptTemplateVersionDetail] | None:
    template = get_prompt_template_model(db, template_id)
    if template is None:
        return None
    versions = db.scalars(
        select(PromptTemplateVersion)
        .where(PromptTemplateVersion.template_id == template_id)
        .order_by(PromptTemplateVersion.version.desc(), PromptTemplateVersion.id.desc())
    ).all()
    return [serialize_version(version) for version in versions]


def rollback_prompt_template(
    db: Session, template_id: int, version_id: int
) -> PromptTemplateDetail | None:
    template = get_prompt_template_model(db, template_id)
    if template is None:
        return None
    version = db.scalar(
        select(PromptTemplateVersion).where(
            PromptTemplateVersion.id == version_id,
            PromptTemplateVersion.template_id == template_id,
        )
    )
    if version is None:
        raise ValueError("提示词版本不存在")
    template.system_prompt = version.system_prompt
    template.user_prompt_template = version.user_prompt_template
    template.output_format = version.output_format
    template.variables = version.variables
    template.version += 1
    add_version(db, template)
    db.commit()
    db.refresh(template)
    return serialize_template(template)
