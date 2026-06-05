# AI小说剧本改编辅助系统项目开发说明

## 1. 项目定位

本项目名称为 **ai-novel-screenplay**。

本项目是一个基于Web的AI小说剧本改编辅助系统。系统面向小说作者、内容创作者和剧本创作者，支持用户上传小说文本，系统自动完成小说预处理、故事设定档案生成、剧本生成配置、场景规划、结构化剧本YAML生成，并提供待选书架、剧本书架、剧本编辑、删除、下载、大模型API管理和提示词模板管理等功能。

本系统不是简单的“小说转剧本”文本改写工具，而是一个带有作品管理、剧本管理、AI生成任务管理、大模型API管理和提示词模板管理能力的创作平台。

初版系统不区分管理员和普通用户。所有功能入口统一面向当前系统用户开放，包括大模型API管理、提示词模板管理和大模型调用日志查看。

---

## 2. 推荐技术栈

```text
前端：Vue3 + Vite + Element Plus + Axios
后端：FastAPI + SQLAlchemy + Pydantic
数据库：PostgreSQL
AI编排：LangChain
大模型接口：兼容OpenAI格式的大模型API，例如DeepSeek、通义千问、OpenAI等
文件处理：python-docx、PyYAML
文件导出：YAML、TXT，后续扩展DOCX、PDF
```

说明：

LangChain主要用于后端AI生成流程编排，包括章节摘要生成、故事设定档案生成、风格策略生成、场景规划生成、剧本YAML生成和YAML格式修复。

PostgreSQL用于存储系统业务数据，其中人物设定、人物关系、生成配置、改编范围、提示词变量等半结构化数据使用JSONB字段保存。

---

## 3. 系统核心业务流程

```text
用户上传小说
 ↓
小说预处理
 ├─ 章节解析
 ├─ 小说篇幅识别
 ├─ 章节摘要生成
 ├─ 人物、事件、地点、伏笔抽取
 └─ 故事设定档案生成
 ↓
加入待选书架
 ↓
用户查看作品
 ├─ 修改作品名称
 ├─ 查看章节
 ├─ 查看章节摘要
 └─ 修改故事设定档案
 ↓
用户选择作品进行改编
 ↓
配置剧本生成参数
 ├─ 改编范围
 ├─ 剧本类型
 ├─ 风格配置
 ├─ 内容压缩程度
 ├─ 剧本大致时长
 ├─ 场景密度
 ├─ 对白比例
 └─ 旁白比例
 ↓
创建剧本生成任务
 ↓
AI生成风格策略
 ↓
AI生成场景规划
 ↓
AI生成剧本YAML
 ↓
保存到剧本书架
 ↓
用户查看 / 编辑 / 删除 / 下载剧本
```

---

## 4. 核心业务概念

### 4.1 待选书架

待选书架存放用户上传并完成预处理的小说作品。

待选书架中的作品包括：

```text
小说基本信息
小说章节
章节摘要
故事设定档案
预处理状态
小说类型
```

待选书架支持：

```text
查看作品列表
查看作品详情
修改作品名称
查看章节内容
查看章节摘要
查看和修改故事设定档案
选择作品进行剧本改编
删除作品
```

删除作品时，如果该作品已经生成过剧本，需要提示用户：删除作品后，关联剧本可以保留，但无法继续基于原小说重新生成。

---

### 4.2 故事设定档案

“故事设定档案”用于替代“故事圣经”这一较专业的说法。它是系统从小说中提取出的核心故事资料。

故事设定档案包括：

```text
故事简介
小说类型
题材类型
世界观
主要人物
人物关系
主线冲突
关键事件
章节梗概
伏笔线索
叙事基调
不可随意改动的核心设定
```

故事设定档案在小说预处理阶段生成，并跟随小说一起进入待选书架。用户可以在待选书架中查看和修改它。后续生成剧本时，系统使用用户确认后的故事设定档案作为基础输入。

---

### 4.3 小说篇幅识别

系统需要根据章节数和字数区分短篇、中篇、长篇小说。

```text
短篇小说：约3万字以内，或10章以内
中篇小说：约3万到15万字，或11到50章
长篇小说：约15万字以上，或50章以上
```

处理策略：

```text
短篇小说：可以支持整本生成剧本
中篇小说：建议按章节区间生成剧本
长篇小说：必须分章预处理，建议按分卷、章节区间或剧情片段生成剧本
```

长篇小说不建议默认生成完整剧本。系统应引导用户选择改编范围。

---

### 4.4 剧本书架

剧本书架存放生成后的剧本成果。剧本书架不只保存完整剧本，也可以保存部分章节、分卷或剧情片段生成的剧本。

剧本书架采用：

```text
剧本项目 ScriptProject
 └─ 剧本片段 ScriptSegment
```

示例：

```text
《长夜来信短剧版》
 ├─ 第1章至第3章剧本片段
 ├─ 第4章至第6章剧本片段
 └─ 第7章至第9章剧本片段
```

剧本书架支持：

```text
查看剧本项目
修改剧本项目名称
查看剧本片段
修改剧本片段名称
编辑剧本内容
删除剧本项目
删除剧本片段
下载剧本
```

---

## 5. 剧本生成配置

用户生成剧本前，需要配置以下参数：

```text
改编范围
剧本类型
风格配置
内容压缩程度
剧本大致时长
场景密度
对白比例
旁白比例
是否保留主线
是否允许删减支线
是否允许合并次要人物
```

### 5.1 改编范围

支持：

```text
单章改编
章节区间改编
分卷改编
剧情片段改编
人物线改编
全书大纲改编
整本完整改编
```

### 5.2 剧本类型

支持：

```text
影视剧本
短剧剧本
话剧剧本
广播剧剧本
分镜剧本
```

### 5.3 内容压缩程度

```text
低压缩：尽量保留原文主要情节和人物关系
中等压缩：保留主线，适当删减支线和重复情节
高压缩：只保留核心冲突和关键剧情
极高压缩：将大量内容浓缩成简短剧情框架
```

### 5.4 剧本大致时长

支持：

```text
3分钟以内
5分钟左右
10分钟左右
15分钟左右
30分钟左右
45分钟左右
60分钟左右
自定义时长
```

内容压缩程度和剧本大致时长会影响场景数量、对白长度、旁白数量、剧情推进速度和冲突密度。

---

## 6. 大模型API管理

系统需要提供大模型API管理页面，不能把模型API写死在代码中。

大模型API管理功能包括：

```text
新增模型配置
编辑模型配置
删除模型配置
启用/停用模型配置
设置默认模型
测试模型连接
配置模型适用任务
查看模型调用日志
```

模型配置字段包括：

```text
模型供应商
接口地址base_url
APIKey
模型名称model_name
temperature
top_p
max_tokens
timeout_seconds
retry_count
enabled
is_default
task_scope
```

APIKey必须加密保存，前端只显示脱敏内容，例如：

```text
sk-******abcd
```

大模型API管理页面作为系统配置页面提供给当前用户使用。初版系统不做管理员和普通用户的权限拆分。

---

## 7. 提示词模板管理

系统需要提供提示词模板管理页面，不能把提示词写死在代码中。

提示词模板按任务类型区分：

```text
chapter_summary_generation：章节摘要生成
story_profile_generation：故事设定档案生成
style_strategy_generation：风格策略生成
scene_plan_generation：场景规划生成
script_yaml_generation：剧本YAML生成
yaml_repair：YAML格式修复
```

提示词模板包括：

```text
模板名称
任务类型
系统提示词
用户提示词模板
输出格式
变量列表
版本号
启用状态
```

提示词模板需要支持版本管理。每次修改模板时生成新版本，方便后续回滚。

提示词模板管理页面统一面向当前系统用户开放，初版不做角色权限限制。

---

## 8. 大模型调用流程

后端调用大模型时，按照以下流程：

```text
根据当前任务步骤确定task_type
 ↓
读取该task_type启用的提示词模板
 ↓
读取该task_type可用的大模型配置
 ↓
将业务数据填充到提示词变量中
 ↓
通过LangChain组织调用链
 ↓
调用大模型API
 ↓
解析模型返回结果
 ↓
校验JSON或YAML格式
 ↓
保存中间成果
 ↓
记录模型调用日志
 ↓
失败时按重试配置进行重试
```

---

## 9. 任务中断与恢复

剧本生成必须采用任务式机制。

任务状态包括：

```text
pending：等待生成
running：正在生成
paused：暂停
failed：失败
completed：完成
canceled：取消
```

剧本生成任务步骤包括：

```text
风格策略生成
场景规划生成
剧本YAML生成
保存到剧本书架
```

每一步完成后都要保存中间成果。如果用户刷新页面、关闭浏览器或网络中断，后端任务数据不能丢失。用户重新进入任务页面后，可以查看当前进度，并支持继续生成、重试当前步骤或取消任务。

---

## 10. 项目工作树

建议Codex按以下目录创建项目：

```text
ai-novel-screenplay/
├─ README.md
├─ docs/
│  ├─ PROJECT_SPEC.md
│  ├─ DATABASE_DESIGN.md
│  ├─ API_DESIGN.md
│  └─ YAML_SCHEMA.md
│
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ core/
│  │  │  ├─ config.py
│  │  │  ├─ database.py
│  │  │  ├─ security.py
│  │  │  └─ response.py
│  │  │
│  │  ├─ models/
│  │  │  ├─ user.py
│  │  │  ├─ book.py
│  │  │  ├─ chapter.py
│  │  │  ├─ chapter_summary.py
│  │  │  ├─ story_profile.py
│  │  │  ├─ generation_task.py
│  │  │  ├─ script_project.py
│  │  │  ├─ script_segment.py
│  │  │  ├─ llm_config.py
│  │  │  ├─ prompt_template.py
│  │  │  └─ llm_call_log.py
│  │  │
│  │  ├─ schemas/
│  │  │  ├─ book_schema.py
│  │  │  ├─ story_profile_schema.py
│  │  │  ├─ script_task_schema.py
│  │  │  ├─ script_project_schema.py
│  │  │  ├─ llm_config_schema.py
│  │  │  └─ prompt_template_schema.py
│  │  │
│  │  ├─ routers/
│  │  │  ├─ book_router.py
│  │  │  ├─ chapter_router.py
│  │  │  ├─ story_profile_router.py
│  │  │  ├─ script_task_router.py
│  │  │  ├─ script_project_router.py
│  │  │  ├─ export_router.py
│  │  │  ├─ llm_config_router.py
│  │  │  ├─ prompt_template_router.py
│  │  │  └─ llm_log_router.py
│  │  │
│  │  ├─ services/
│  │  │  ├─ book_service.py
│  │  │  ├─ preprocess_service.py
│  │  │  ├─ story_profile_service.py
│  │  │  ├─ script_generation_service.py
│  │  │  ├─ script_project_service.py
│  │  │  ├─ export_service.py
│  │  │  ├─ llm_service.py
│  │  │  ├─ langchain_service.py
│  │  │  ├─ prompt_service.py
│  │  │  └─ yaml_service.py
│  │  │
│  │  ├─ utils/
│  │  │  ├─ chapter_parser.py
│  │  │  ├─ file_reader.py
│  │  │  ├─ yaml_validator.py
│  │  │  └─ crypto.py
│  │  │
│  │  └─ prompts/
│  │     └─ default_prompts.py
│  │
│  ├─ requirements.txt
│  └─ run.py
│
├─ frontend/
│  ├─ package.json
│  ├─ index.html
│  ├─ src/
│  │  ├─ main.ts
│  │  ├─ App.vue
│  │  ├─ router/
│  │  │  └─ index.ts
│  │  ├─ api/
│  │  │  ├─ book.ts
│  │  │  ├─ scriptTask.ts
│  │  │  ├─ scriptProject.ts
│  │  │  ├─ llmConfig.ts
│  │  │  └─ promptTemplate.ts
│  │  ├─ views/
│  │  │  ├─ HomeView.vue
│  │  │  ├─ BookUploadView.vue
│  │  │  ├─ BookShelfView.vue
│  │  │  ├─ BookDetailView.vue
│  │  │  ├─ StoryProfileEditView.vue
│  │  │  ├─ ScriptGenerateConfigView.vue
│  │  │  ├─ ScriptTaskProgressView.vue
│  │  │  ├─ ScriptShelfView.vue
│  │  │  ├─ ScriptProjectDetailView.vue
│  │  │  ├─ ScriptEditorView.vue
│  │  │  ├─ LlmConfigManageView.vue
│  │  │  ├─ PromptTemplateManageView.vue
│  │  │  └─ LlmCallLogView.vue
│  │  ├─ components/
│  │  └─ stores/
│  │
│  └─ vite.config.ts
│
└─ sql/
   └─ init.sql
```

---

## 11. 前端页面列表

前端至少实现以下页面：

```text
首页
小说上传页
预处理进度页
待选书架页
作品详情页
故事设定档案编辑页
剧本生成配置页
生成任务进度页
剧本书架页
剧本项目详情页
剧本编辑页
剧本下载页
大模型API管理页
提示词模板管理页
模型调用日志页
```

---

## 12. 开发优先级

### 第一阶段：基础业务闭环

```text
小说上传
章节解析
小说篇幅识别
待选书架
故事设定档案生成与编辑
剧本生成配置
剧本YAML生成
剧本书架
剧本下载YAML/TXT
```

### 第二阶段：AI管理能力

```text
大模型API管理
提示词模板管理
模型调用日志
LangChain流程编排
YAML格式修复
任务失败重试
```

### 第三阶段：体验优化

```text
剧本片段合并
风格一致性检查
DOCX/PDF导出
回收站
提示词模板版本回滚
```

---

## 13. YAML Schema简要说明

剧本YAML需要包含：

```text
metadata：剧本元信息
adapt_scope：改编范围
generation_config：生成配置
characters：人物信息
scenes：场景列表
```

不同剧本类型可扩展：

```text
短剧剧本：short_drama字段
影视剧本：film字段
广播剧剧本：audio字段
话剧剧本：stage字段
分镜剧本：shots字段
```

基础示例：

```yaml
script:
  metadata:
    script_id: "script_001"
    project_id: "project_001"
    segment_id: "segment_001"
    source_book_id: "book_001"
    title: "长夜来信短剧版"
    segment_title: "第1章至第3章：旧信出现"
    script_type: "短剧剧本"
    style: "校园悬疑"
    compression_level: "high"
    target_duration: 5
    duration_unit: "minute"

  adapt_scope:
    type: "chapter_range"
    start_chapter: 1
    end_chapter: 3
    description: "改编第1章至第3章"

  generation_config:
    scene_density: "low"
    dialogue_ratio: "medium"
    narration_ratio: "low"
    keep_main_plot: true
    allow_remove_side_plots: true
    allow_merge_minor_characters: true

  characters:
    - name: "林川"
      role: "男主角"
      description: "敏感、冷静、执着。"

  scenes:
    - scene_id: 1
      scene_title: "旧信出现"
      source_chapters:
        - 1
      location: "教室"
      time: "傍晚"
      characters:
        - "林川"
      scene_goal: "用旧信引出主线悬念"
      conflict: "林川想忽略旧信，但信中的内容指向过去"
      short_drama:
        hook: "林川在课桌里发现一封写着自己名字的旧信。"
        reversal_point: "信中的字迹像是多年前留下的。"
        ending_hook: "信的最后一行写着：别去旧教学楼。"
      action:
        - "教室里只剩下林川一个人。"
      dialogue:
        - speaker: "林川"
          line: "这是谁放的？"
          emotion: "疑惑"
      transition: "画面切至旧教学楼外。"
```
