# API 设计文档

## 1. 通用约定

后端基路径为 `/api`。除下载接口外，响应统一为：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

错误响应：

```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

## 2. 健康检查

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 服务健康检查 |
| GET | `/api/health/db` | 数据库连接检查 |

## 3. 小说作品

### 3.1 文本上传

`POST /api/books/text`

请求：

```json
{
  "title": "斗罗大陆",
  "content": "第一章 ...\n第二章 ..."
}
```

响应：

```json
{
  "book_id": 1,
  "title": "斗罗大陆",
  "preprocess_status": "completed"
}
```

### 3.2 文件上传

`POST /api/books/upload`

`multipart/form-data`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file | file | 是 | `.txt` 文件 |
| title | string | 否 | 作品名 |

### 3.3 作品列表

`GET /api/books?keyword=&novel_type=&page=1&size=20`

响应：

```json
{
  "records": [
    {
      "book_id": 1,
      "title": "斗罗大陆",
      "novel_type": "long",
      "chapter_count": 678,
      "word_count": 1200000,
      "preprocess_status": "completed"
    }
  ],
  "total": 1
}
```

### 3.4 作品详情

`GET /api/books/{book_id}`

### 3.5 删除作品

`DELETE /api/books/{book_id}`

删除作品会软删除章节和关联剧本改编数据。

## 4. 章节

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/books/{book_id}/chapters` | 获取作品章节列表 |
| GET | `/api/chapters/{chapter_id}` | 获取章节正文 |
| POST | `/api/books/{book_id}/chapters` | 新增章节 |
| PUT | `/api/chapters/{chapter_id}` | 修改章节 |
| DELETE | `/api/chapters/{chapter_id}` | 删除章节 |

新增章节请求：

```json
{
  "title": "第一章 武魂觉醒",
  "content": "章节正文",
  "chapter_index": 1
}
```

修改章节请求：

```json
{
  "title": "第一章 武魂觉醒",
  "content": "新的正文"
}
```

## 5. 剧本改编项目

### 5.1 项目列表

`GET /api/script-adaptations?page=1&size=20`

### 5.2 创建项目

`POST /api/script-adaptations`

```json
{
  "book_id": 1,
  "project_name": "斗罗大陆动画改编",
  "adaptation_type": "animation",
  "episode_duration": 24,
  "pacing": "medium",
  "scene_frequency": "medium",
  "dialogue_density": "medium",
  "events_per_episode": 10
}
```

`adaptation_type` 可选：`tv`、`short_drama`、`animation`、`audio_drama`。

### 5.3 更新配置

`PUT /api/script-adaptations/{project_id}/config`

可修改字段：`project_name`、`episode_duration`、`pacing`、`scene_frequency`、`dialogue_density`、`events_per_episode`。

### 5.4 删除项目

`DELETE /api/script-adaptations/{project_id}`

### 5.5 进度

`GET /api/script-adaptations/{project_id}/progress`

## 6. 剧情事件拆分

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/script-adaptations/{project_id}/split/once` | 单批拆分 |
| POST | `/api/script-adaptations/{project_id}/split/all` | 后台全部拆分 |
| POST | `/api/script-adaptations/{project_id}/split/stop` | 请求停止拆分 |
| GET | `/api/script-adaptations/{project_id}/batches` | 批次列表 |
| GET | `/api/script-adaptations/{project_id}/events` | 剧情事件列表 |
| PUT | `/api/script-adaptations/events/{event_id}` | 编辑事件 |
| DELETE | `/api/script-adaptations/events/{event_id}` | 删除事件 |

事件更新：

```json
{
  "content": "唐三完成武魂觉醒，发现蓝银草伴随先天满魂力。"
}
```

## 7. 人物档案

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/script-adaptations/{project_id}/characters` | 人物列表 |
| PUT | `/api/script-adaptations/characters/{character_id}` | 编辑人物 |
| POST | `/api/script-adaptations/{project_id}/characters/consolidate` | AI 整合人物档案 |

人物更新：

```json
{
  "name": "唐三",
  "profile": "唐三，冷静坚韧，重视亲情，拥有蓝银草与昊天锤。",
  "metadata_json": {}
}
```

## 8. 剧集生成与编辑

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/script-adaptations/{project_id}/episodes/once` | 生成单集 |
| POST | `/api/script-adaptations/{project_id}/episodes/all` | 后台全部生成 |
| POST | `/api/script-adaptations/{project_id}/episodes/stop` | 请求停止生成 |
| GET | `/api/script-adaptations/{project_id}/episodes` | 剧集列表 |
| PUT | `/api/script-adaptations/episodes/{episode_id}` | 编辑剧集 |

生成请求：

```json
{
  "events_per_episode": 10
}
```

编辑请求：

```json
{
  "title": "启程·诺丁城",
  "yaml_payload": {
    "script": {
      "metadata": {
        "title": "启程·诺丁城"
      },
      "scenes": []
    }
  }
}
```

后端会强制规范化 `metadata.episode_number`、`source_book_title`、`adaptation_type` 等固定字段。

## 9. 导出

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/script-adaptations/episodes/{episode_id}/download?format=yaml` | 单集导出 |
| GET | `/api/script-adaptations/{project_id}/download?format=txt` | 全部导出 |

`format` 支持 `yaml`、`txt`。

下载接口直接返回文件响应，不使用通用 JSON envelope。

## 10. 大模型配置

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/llm-configs` | 配置列表 |
| POST | `/api/llm-configs` | 新增配置 |
| PUT | `/api/llm-configs/{config_id}` | 修改配置 |
| DELETE | `/api/llm-configs/{config_id}` | 删除配置 |
| POST | `/api/llm-configs/{config_id}/default` | 设为默认 |
| POST | `/api/llm-configs/{config_id}/test` | 测试连接 |

新增配置：

```json
{
  "provider": "deepseek",
  "base_url": "https://api.deepseek.com/v1",
  "api_key": "sk-...",
  "model_name": "deepseek-chat",
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 4096,
  "timeout_seconds": 60,
  "retry_count": 2,
  "task_scope": ["plot_event_split_generation", "script_episode_generation"],
  "enabled": true,
  "is_default": true
}
```

## 11. 提示词模板

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/prompt-templates` | 模板列表 |
| POST | `/api/prompt-templates` | 新增模板 |
| POST | `/api/prompt-templates/seed-defaults` | 初始化默认模板 |
| PUT | `/api/prompt-templates/{template_id}` | 修改模板 |
| DELETE | `/api/prompt-templates/{template_id}` | 删除模板 |
| GET | `/api/prompt-templates/{template_id}/versions` | 版本列表 |
| POST | `/api/prompt-templates/{template_id}/rollback/{version_id}` | 回滚版本 |

当前默认任务类型：

- `plot_event_split_generation`
- `script_episode_generation`
- `character_profile_consolidation`

## 12. 调用日志

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/llm-call-logs` | 日志列表 |
| GET | `/api/llm-call-logs/{log_id}` | 日志详情 |
| DELETE | `/api/llm-call-logs` | 清空日志 |

列表筛选参数：

- `task_type`
- `status`
- `start_time`
- `end_time`
- `page`
- `size`
