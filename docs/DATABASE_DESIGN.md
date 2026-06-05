# 数据库设计文档

## 1. 数据库说明

本系统数据库采用PostgreSQL，用于存储用户、小说作品、章节、章节摘要、故事设定档案、剧本生成任务、剧本项目、剧本片段、大模型配置、提示词模板和模型调用日志。

由于系统中存在大量结构化和半结构化数据，例如人物设定、人物关系、章节摘要、生成配置、改编范围、提示词变量和模型适用任务等内容，相关字段统一使用PostgreSQL的JSONB类型进行存储。

开发环境和生产环境均推荐使用PostgreSQL，避免SQLite与PostgreSQL之间的数据类型差异影响后续迁移。

---

## 2. PostgreSQL字段类型约定

| 业务含义 | PostgreSQL类型 |
|---|---|
| 主键ID | BIGSERIAL |
| 外键ID | BIGINT |
| 普通字符串 | VARCHAR |
| 长文本 | TEXT |
| 时间 | TIMESTAMP |
| 布尔值 | BOOLEAN |
| JSON数据 | JSONB |
| 整数 | INTEGER |
| 小数 | NUMERIC |

---

## 3. 核心表总览

```text
users：用户表
books：小说作品表
chapters：小说章节表
chapter_summaries：章节摘要表
story_profiles：故事设定档案表
generation_tasks：剧本生成任务表
generation_artifacts：生成中间成果表
script_projects：剧本项目表
script_segments：剧本片段表
llm_configs：大模型配置表
prompt_templates：提示词模板表
prompt_template_versions：提示词模板版本表
llm_call_logs：大模型调用日志表
export_records：导出记录表
```

---

## 4. users用户表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| username | VARCHAR(100) | 用户名 |
| password_hash | VARCHAR(255) | 密码哈希 |
| nickname | VARCHAR(100) | 昵称 |
| email | VARCHAR(255) | 邮箱 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| is_deleted | BOOLEAN | 是否删除 |

建议默认值：

```sql
is_deleted BOOLEAN DEFAULT FALSE
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

说明：

初版系统不区分管理员和普通用户，因此不需要role字段。

---

## 5. books小说作品表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| user_id | BIGINT | 用户ID |
| title | VARCHAR(255) | 作品名称，可修改 |
| original_filename | VARCHAR(255) | 原始文件名 |
| source_type | VARCHAR(50) | file/text |
| novel_type | VARCHAR(50) | short/middle/long |
| word_count | INTEGER | 总字数 |
| chapter_count | INTEGER | 章节数 |
| preprocess_status | VARCHAR(50) | pending/processing/completed/failed |
| story_profile_status | VARCHAR(50) | pending/generated/confirmed/failed |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | 删除时间 |
| is_deleted | BOOLEAN | 是否删除 |

说明：

novel_type用于区分短篇、中篇、长篇小说。

```text
short：短篇小说
middle：中篇小说
long：长篇小说
```

---

## 6. chapters小说章节表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| book_id | BIGINT | 作品ID |
| chapter_index | INTEGER | 章节序号 |
| title | VARCHAR(255) | 章节标题 |
| content | TEXT | 章节正文 |
| word_count | INTEGER | 章节字数 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| is_deleted | BOOLEAN | 是否删除 |

说明：

一个book可以对应多个chapter。

---

## 7. chapter_summaries章节摘要表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| book_id | BIGINT | 作品ID |
| chapter_id | BIGINT | 章节ID |
| summary | TEXT | 章节摘要 |
| characters | JSONB | 本章人物 |
| key_events | JSONB | 关键事件 |
| locations | JSONB | 地点 |
| clues | JSONB | 伏笔线索 |
| emotion_changes | JSONB | 情绪变化 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

## 8. story_profiles故事设定档案表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| book_id | BIGINT | 作品ID |
| title | VARCHAR(255) | 故事标题 |
| genre | VARCHAR(100) | 题材类型 |
| overview | TEXT | 故事简介 |
| world_setting | TEXT | 世界观 |
| main_conflict | TEXT | 主线冲突 |
| characters | JSONB | 人物设定 |
| relationships | JSONB | 人物关系 |
| key_events | JSONB | 关键事件 |
| chapter_outlines | JSONB | 章节梗概 |
| clues | JSONB | 伏笔线索 |
| tone | VARCHAR(100) | 叙事基调 |
| locked_settings | JSONB | 核心设定 |
| version | INTEGER | 版本号 |
| confirmed | BOOLEAN | 是否确认 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

说明：

故事设定档案由系统在小说预处理阶段生成，用户可以在待选书架中修改。修改后version递增。

---

## 9. generation_tasks生成任务表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| user_id | BIGINT | 用户ID |
| book_id | BIGINT | 作品ID |
| script_project_id | BIGINT | 剧本项目ID，可为空 |
| task_type | VARCHAR(100) | script_generation/preprocess等 |
| status | VARCHAR(50) | pending/running/paused/failed/completed/canceled |
| current_step | VARCHAR(100) | 当前步骤 |
| adapt_scope | JSONB | 改编范围 |
| generation_config | JSONB | 生成配置 |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| finished_at | TIMESTAMP | 完成时间 |

current_step建议值：

```text
style_strategy
scene_planning
script_yaml
save_script
```

---

## 10. generation_artifacts生成中间成果表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| task_id | BIGINT | 任务ID |
| artifact_type | VARCHAR(100) | style_strategy/scene_plan/script_yaml |
| content | JSONB | 成果内容 |
| version | INTEGER | 版本号 |
| editable | BOOLEAN | 是否可编辑 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

说明：

用于任务中断恢复和中间结果查看。用户可以查看和修改部分中间成果。

---

## 11. script_projects剧本项目表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| user_id | BIGINT | 用户ID |
| book_id | BIGINT | 来源作品ID |
| project_name | VARCHAR(255) | 剧本项目名称，可修改 |
| script_type | VARCHAR(100) | 剧本类型 |
| default_style | VARCHAR(100) | 默认风格 |
| default_compression_level | VARCHAR(50) | 默认压缩程度 |
| default_target_duration | INTEGER | 默认目标时长，单位分钟 |
| status | VARCHAR(50) | ongoing/completed |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | 删除时间 |
| is_deleted | BOOLEAN | 是否删除 |

说明：

一部小说可以生成多个剧本项目。

---

## 12. script_segments剧本片段表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| project_id | BIGINT | 剧本项目ID |
| book_id | BIGINT | 来源作品ID |
| segment_name | VARCHAR(255) | 片段名称，可修改 |
| adapt_scope | JSONB | 改编范围 |
| style_source | VARCHAR(50) | inherit_project/custom |
| style | VARCHAR(100) | 片段风格 |
| compression_level | VARCHAR(50) | 压缩程度 |
| target_duration | INTEGER | 目标时长，单位分钟 |
| actual_word_count | INTEGER | 实际生成字数 |
| scene_count | INTEGER | 场景数量 |
| yaml_content | TEXT | 剧本YAML |
| plain_text_content | TEXT | 普通文本内容 |
| status | VARCHAR(50) | completed/draft |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | 删除时间 |
| is_deleted | BOOLEAN | 是否删除 |

说明：

一个剧本项目可以包含多个剧本片段。剧本片段可以对应单章、章节区间、分卷、人物线或剧情片段。

---

## 13. llm_configs大模型配置表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| provider | VARCHAR(100) | 模型供应商 |
| base_url | VARCHAR(500) | 接口地址 |
| api_key_encrypted | TEXT | 加密后的APIKey |
| api_key_masked | VARCHAR(100) | 脱敏展示 |
| model_name | VARCHAR(100) | 模型名称 |
| temperature | NUMERIC(4,2) | 温度参数 |
| top_p | NUMERIC(4,2) | top_p |
| max_tokens | INTEGER | 最大输出Token |
| timeout_seconds | INTEGER | 超时时间 |
| retry_count | INTEGER | 重试次数 |
| task_scope | JSONB | 适用任务 |
| is_default | BOOLEAN | 是否默认 |
| enabled | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| is_deleted | BOOLEAN | 是否删除 |

说明：

APIKey必须加密保存。前端只能展示api_key_masked字段。

---

## 14. prompt_templates提示词模板表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| template_name | VARCHAR(255) | 模板名称 |
| task_type | VARCHAR(100) | 任务类型 |
| system_prompt | TEXT | 系统提示词 |
| user_prompt_template | TEXT | 用户提示词模板 |
| output_format | VARCHAR(50) | json/yaml/text |
| variables | JSONB | 可用变量 |
| version | INTEGER | 版本号 |
| enabled | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| is_deleted | BOOLEAN | 是否删除 |

task_type建议值：

```text
chapter_summary_generation
story_profile_generation
style_strategy_generation
scene_plan_generation
script_yaml_generation
yaml_repair
```

---

## 15. prompt_template_versions提示词模板版本表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| template_id | BIGINT | 模板ID |
| version | INTEGER | 版本号 |
| system_prompt | TEXT | 系统提示词 |
| user_prompt_template | TEXT | 用户提示词模板 |
| output_format | VARCHAR(50) | 输出格式 |
| variables | JSONB | 变量列表 |
| created_at | TIMESTAMP | 创建时间 |

说明：

每次修改提示词模板时，都应写入一条版本记录，方便回滚。

---

## 16. llm_call_logs大模型调用日志表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| task_id | BIGINT | 生成任务ID |
| llm_config_id | BIGINT | 模型配置ID |
| prompt_template_id | BIGINT | 提示词模板ID |
| task_type | VARCHAR(100) | 调用任务类型 |
| request_summary | TEXT | 请求摘要 |
| response_summary | TEXT | 响应摘要 |
| input_tokens | INTEGER | 输入Token |
| output_tokens | INTEGER | 输出Token |
| total_tokens | INTEGER | 总Token |
| status | VARCHAR(50) | success/failed |
| error_message | TEXT | 错误信息 |
| latency_ms | INTEGER | 响应耗时 |
| created_at | TIMESTAMP | 创建时间 |

注意：

日志中不要保存完整小说原文，避免敏感内容泄露。

---

## 17. export_records导出记录表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGSERIAL | 主键 |
| user_id | BIGINT | 用户ID |
| project_id | BIGINT | 剧本项目ID |
| segment_id | BIGINT | 剧本片段ID，可为空 |
| export_type | VARCHAR(50) | project/segment |
| file_format | VARCHAR(50) | yaml/txt/docx/pdf |
| file_path | VARCHAR(500) | 文件路径 |
| created_at | TIMESTAMP | 创建时间 |

---

## 18. 核心关系

```text
users 1 - N books

books 1 - N chapters
books 1 - N chapter_summaries
books 1 - 1 story_profiles

books 1 - N script_projects
script_projects 1 - N script_segments

generation_tasks 1 - N generation_artifacts

llm_configs 1 - N llm_call_logs
prompt_templates 1 - N prompt_template_versions
prompt_templates 1 - N llm_call_logs
```

---

## 19. 索引建议

建议为以下字段建立索引：

```sql
CREATE INDEX idx_books_user_id ON books(user_id);
CREATE INDEX idx_books_novel_type ON books(novel_type);
CREATE INDEX idx_chapters_book_id ON chapters(book_id);
CREATE INDEX idx_chapters_book_index ON chapters(book_id, chapter_index);
CREATE INDEX idx_story_profiles_book_id ON story_profiles(book_id);
CREATE INDEX idx_generation_tasks_user_id ON generation_tasks(user_id);
CREATE INDEX idx_generation_tasks_book_id ON generation_tasks(book_id);
CREATE INDEX idx_script_projects_user_id ON script_projects(user_id);
CREATE INDEX idx_script_projects_book_id ON script_projects(book_id);
CREATE INDEX idx_script_segments_project_id ON script_segments(project_id);
CREATE INDEX idx_llm_call_logs_task_id ON llm_call_logs(task_id);
CREATE INDEX idx_prompt_templates_task_type ON prompt_templates(task_type);
```

JSONB字段后续如果需要检索，可以补充GIN索引。
