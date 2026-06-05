# 接口设计文档

## 1. 接口设计说明

初版系统不区分管理员和普通用户，所有接口统一面向当前系统用户开放。

接口按业务模块划分，包括小说作品接口、小说预处理接口、章节接口、故事设定档案接口、剧本生成任务接口、剧本书架接口、剧本下载接口、大模型API配置接口、提示词模板接口和大模型调用日志接口。

大模型API配置、提示词模板和模型调用日志虽然属于系统配置类功能，但初版不做角色权限限制，统一通过普通页面入口进行管理。

---

## 2. 统一响应格式

所有接口统一返回：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

失败示例：

```json
{
  "code": 400,
  "message": "小说内容不能为空",
  "data": null
}
```

---

## 3. 小说作品接口

### 3.1 上传小说文件

```http
POST /api/books/upload
Content-Type: multipart/form-data
```

参数：

```text
file：小说文件
title：作品名称，可选
```

返回：

```json
{
  "book_id": 1,
  "title": "长夜来信",
  "preprocess_status": "pending"
}
```

---

### 3.2 粘贴文本创建小说

```http
POST /api/books/text
Content-Type: application/json
```

请求：

```json
{
  "title": "长夜来信",
  "content": "第1章 旧信\n......"
}
```

返回：

```json
{
  "book_id": 1,
  "title": "长夜来信",
  "preprocess_status": "pending"
}
```

---

### 3.3 获取待选书架作品列表

```http
GET /api/books
```

查询参数：

```text
keyword：搜索关键词
novel_type：short/middle/long
page：页码
size：每页数量
```

返回：

```json
{
  "records": [
    {
      "book_id": 1,
      "title": "长夜来信",
      "novel_type": "long",
      "chapter_count": 128,
      "word_count": 350000,
      "preprocess_status": "completed"
    }
  ],
  "total": 1
}
```

---

### 3.4 获取作品详情

```http
GET /api/books/{book_id}
```

返回：

```json
{
  "book_id": 1,
  "title": "长夜来信",
  "novel_type": "long",
  "chapter_count": 128,
  "word_count": 350000,
  "preprocess_status": "completed",
  "story_profile_status": "confirmed"
}
```

---

### 3.5 修改作品名称

```http
PUT /api/books/{book_id}/title
```

请求：

```json
{
  "title": "长夜来信修订版"
}
```

---

### 3.6 删除作品

```http
DELETE /api/books/{book_id}
```

说明：

采用软删除。如果存在关联剧本，后端可以返回提醒信息，由前端展示确认。

---

## 4. 小说预处理接口

### 4.1 启动预处理

```http
POST /api/books/{book_id}/preprocess
```

返回：

```json
{
  "book_id": 1,
  "status": "processing"
}
```

---

### 4.2 查询预处理状态

```http
GET /api/books/{book_id}/preprocess/status
```

返回：

```json
{
  "book_id": 1,
  "status": "processing",
  "current_step": "chapter_summary",
  "processed_chapters": 20,
  "total_chapters": 128
}
```

---

## 5. 章节接口

### 5.1 获取章节列表

```http
GET /api/books/{book_id}/chapters
```

返回：

```json
[
  {
    "chapter_id": 1,
    "chapter_index": 1,
    "title": "旧信",
    "word_count": 4200
  }
]
```

---

### 5.2 获取章节详情

```http
GET /api/chapters/{chapter_id}
```

返回：

```json
{
  "chapter_id": 1,
  "title": "旧信",
  "content": "章节正文......"
}
```

---

### 5.3 获取章节摘要

```http
GET /api/chapters/{chapter_id}/summary
```

返回：

```json
{
  "chapter_id": 1,
  "summary": "林川收到一封旧信，并开始怀疑多年前的事件另有隐情。",
  "characters": ["林川", "许念"],
  "key_events": ["旧信出现", "林川决定调查"],
  "locations": ["教室", "旧教学楼"],
  "clues": ["信封上的旧校徽"]
}
```

---

## 6. 故事设定档案接口

### 6.1 获取故事设定档案

```http
GET /api/books/{book_id}/story-profile
```

返回：

```json
{
  "profile_id": 1,
  "book_id": 1,
  "title": "长夜来信",
  "genre": "校园悬疑",
  "overview": "故事围绕一封旧信展开。",
  "world_setting": "现代校园",
  "main_conflict": "主角需要查清旧信背后的真相。",
  "characters": [],
  "relationships": [],
  "key_events": [],
  "clues": [],
  "version": 1,
  "confirmed": true
}
```

---

### 6.2 修改故事设定档案

```http
PUT /api/books/{book_id}/story-profile
```

请求：

```json
{
  "genre": "校园悬疑",
  "overview": "修改后的故事简介",
  "world_setting": "现代校园",
  "main_conflict": "主角需要查清旧信背后的真相",
  "characters": [],
  "relationships": [],
  "key_events": [],
  "clues": []
}
```

返回：

```json
{
  "version": 2
}
```

---

## 7. 剧本生成任务接口

### 7.1 创建剧本生成任务

```http
POST /api/script-tasks
```

请求：

```json
{
  "book_id": 1,
  "project_id": null,
  "adapt_scope": {
    "type": "chapter_range",
    "start_chapter": 1,
    "end_chapter": 5
  },
  "generation_config": {
    "script_type": "short_drama",
    "style": "校园悬疑",
    "compression_level": "high",
    "target_duration": 5,
    "scene_density": "low",
    "dialogue_ratio": "medium",
    "narration_ratio": "low",
    "keep_main_plot": true,
    "allow_remove_side_plots": true,
    "allow_merge_minor_characters": true
  }
}
```

返回：

```json
{
  "task_id": 1001,
  "status": "pending"
}
```

---

### 7.2 启动生成任务

```http
POST /api/script-tasks/{task_id}/start
```

返回：

```json
{
  "task_id": 1001,
  "status": "running"
}
```

---

### 7.3 查询生成任务状态

```http
GET /api/script-tasks/{task_id}
```

返回：

```json
{
  "task_id": 1001,
  "status": "running",
  "current_step": "scene_planning",
  "progress": 60,
  "error_message": null
}
```

---

### 7.4 重试当前步骤

```http
POST /api/script-tasks/{task_id}/retry
```

---

### 7.5 取消生成任务

```http
POST /api/script-tasks/{task_id}/cancel
```

---

## 8. 生成中间成果接口

### 8.1 获取任务中间成果列表

```http
GET /api/script-tasks/{task_id}/artifacts
```

返回：

```json
[
  {
    "artifact_id": 1,
    "artifact_type": "style_strategy",
    "version": 1,
    "editable": true
  },
  {
    "artifact_id": 2,
    "artifact_type": "scene_plan",
    "version": 1,
    "editable": true
  }
]
```

---

### 8.2 获取中间成果详情

```http
GET /api/artifacts/{artifact_id}
```

---

### 8.3 修改中间成果

```http
PUT /api/artifacts/{artifact_id}
```

请求：

```json
{
  "content": {}
}
```

---

## 9. 剧本书架接口

### 9.1 获取剧本项目列表

```http
GET /api/script-projects
```

查询参数：

```text
keyword
script_type
page
size
```

返回：

```json
{
  "records": [
    {
      "project_id": 1,
      "project_name": "长夜来信短剧版",
      "book_title": "长夜来信",
      "script_type": "短剧剧本",
      "default_style": "校园悬疑",
      "segment_count": 3
    }
  ],
  "total": 1
}
```

---

### 9.2 获取剧本项目详情

```http
GET /api/script-projects/{project_id}
```

---

### 9.3 修改剧本项目名称

```http
PUT /api/script-projects/{project_id}/name
```

请求：

```json
{
  "project_name": "长夜来信短剧版第一稿"
}
```

---

### 9.4 删除剧本项目

```http
DELETE /api/script-projects/{project_id}
```

---

### 9.5 获取剧本片段列表

```http
GET /api/script-projects/{project_id}/segments
```

返回：

```json
[
  {
    "segment_id": 1,
    "segment_name": "第1章至第3章：旧信出现",
    "style": "校园悬疑",
    "compression_level": "high",
    "target_duration": 5,
    "scene_count": 4,
    "status": "completed"
  }
]
```

---

### 9.6 获取剧本片段详情

```http
GET /api/script-segments/{segment_id}
```

---

### 9.7 修改剧本片段名称

```http
PUT /api/script-segments/{segment_id}/name
```

请求：

```json
{
  "segment_name": "第1章至第3章：旧信出现"
}
```

---

### 9.8 编辑剧本片段内容

```http
PUT /api/script-segments/{segment_id}/content
```

请求：

```json
{
  "yaml_content": "script:\n  title: 长夜来信\n",
  "plain_text_content": "普通文本剧本内容"
}
```

---

### 9.9 删除剧本片段

```http
DELETE /api/script-segments/{segment_id}
```

---

## 10. 剧本下载接口

### 10.1 下载单个剧本片段

```http
GET /api/script-segments/{segment_id}/download?format=yaml
```

format可选：

```text
yaml
txt
docx
pdf
```

初版实现yaml和txt。

---

### 10.2 下载整个剧本项目

```http
GET /api/script-projects/{project_id}/download?format=txt
```

---

### 10.3 下载前检查

```http
GET /api/script-projects/{project_id}/export-check
```

返回：

```json
{
  "chapter_continuous": true,
  "style_consistent": false,
  "duration_consistent": true,
  "warnings": [
    "当前剧本项目包含多个风格片段"
  ]
}
```

---

## 11. 大模型API管理接口

### 11.1 新增模型配置

```http
POST /api/llm-configs
```

请求：

```json
{
  "provider": "DeepSeek",
  "base_url": "https://api.deepseek.com",
  "api_key": "sk-xxxx",
  "model_name": "deepseek-chat",
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 4096,
  "timeout_seconds": 60,
  "retry_count": 2,
  "task_scope": [
    "story_profile_generation",
    "style_strategy_generation",
    "scene_plan_generation",
    "script_yaml_generation"
  ],
  "enabled": true
}
```

说明：

后端保存时需要加密api_key，并生成脱敏展示字段api_key_masked。

---

### 11.2 获取模型配置列表

```http
GET /api/llm-configs
```

---

### 11.3 修改模型配置

```http
PUT /api/llm-configs/{config_id}
```

---

### 11.4 删除模型配置

```http
DELETE /api/llm-configs/{config_id}
```

---

### 11.5 测试模型连接

```http
POST /api/llm-configs/{config_id}/test
```

返回：

```json
{
  "provider": "DeepSeek",
  "model_name": "deepseek-chat",
  "latency_ms": 1260
}
```

---

### 11.6 设置默认模型

```http
POST /api/llm-configs/{config_id}/default
```

---

## 12. 提示词模板接口

### 12.1 新增提示词模板

```http
POST /api/prompt-templates
```

请求：

```json
{
  "template_name": "剧本YAML生成模板",
  "task_type": "script_yaml_generation",
  "system_prompt": "你是一个专业剧本创作助手...",
  "user_prompt_template": "请根据以下信息生成剧本YAML：{{scene_plan}}",
  "output_format": "yaml",
  "variables": [
    "story_profile",
    "script_type",
    "style_strategy",
    "generation_config",
    "scene_plan",
    "yaml_schema"
  ],
  "enabled": true
}
```

---

### 12.2 获取提示词模板列表

```http
GET /api/prompt-templates
```

查询参数：

```text
task_type
enabled
keyword
```

---

### 12.3 修改提示词模板

```http
PUT /api/prompt-templates/{template_id}
```

说明：

修改时需要生成新版本记录，不能直接覆盖历史版本。

---

### 12.4 查看提示词版本

```http
GET /api/prompt-templates/{template_id}/versions
```

---

### 12.5 回滚提示词版本

```http
POST /api/prompt-templates/{template_id}/rollback/{version_id}
```

---

### 12.6 测试提示词模板

```http
POST /api/prompt-templates/{template_id}/test
```

请求：

```json
{
  "llm_config_id": 1,
  "test_variables": {
    "story_profile": {},
    "scene_plan": {},
    "generation_config": {}
  }
}
```

---

## 13. 大模型调用日志接口

### 13.1 获取调用日志

```http
GET /api/llm-call-logs
```

查询参数：

```text
task_type
status
start_time
end_time
page
size
```

---

### 13.2 查看日志详情

```http
GET /api/llm-call-logs/{log_id}
```
