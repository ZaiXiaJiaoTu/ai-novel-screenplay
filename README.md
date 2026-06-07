# ai-novel-screenplay

AI 小说剧本改编辅助系统。项目面向中文小说到分集剧本的改编工作流，提供小说上传、章节维护、剧情事件拆分、人物档案、分集剧本生成、剧本编辑导出、大模型配置、提示词模板和调用日志排查。

## 功能

- 工作台：展示结项版业务流程，并提供小说书架、剧本生成、模型配置快捷入口。
- 小说书架：支持文本粘贴和 `.txt` 文件上传，自动切分章节，支持新增、编辑、删除章节和删除小说。
- 剧本改编项目：支持电视剧、短剧、动画、广播剧四种改编类型，配置单集时长、剧情节奏、场景切换频率、对话密度和每集事件数。
- 剧情事件拆分：每 3 章为一个批次，支持单次拆分、全部拆分和安全停止；事件可编辑、删除，已用于剧集后锁定。
- 人物档案：随剧情拆分增量提取人物关键特征，支持手动编辑和 AI 一键整合档案。
- 分集剧本生成：按未锁定剧情事件生成单集或全部剧集，支持安全停止；后端固定规范化 YAML metadata。
- 剧本编辑：支持中文表单编辑和 YAML 源码编辑。
- 剧本导出：支持单集/全集导出，格式为 YAML 或渲染后的 TXT。
- 大模型配置：支持 OpenAI 兼容 API 配置、加密保存 API Key、测试连接和默认配置。
- 提示词模板：支持默认模板初始化、筛选、编辑、启停、版本查看和回滚。
- 调用日志：支持查看模型调用状态、耗时、Token 用量、请求/响应摘要、错误信息和一键清空。

已移除旧模块：章节摘要生成、故事设定档案生成、旧剧本任务流水线、旧剧本片段接口和演示 seed 入口。

## 技术栈

后端：

- FastAPI：HTTP API。
- SQLAlchemy 2：ORM。
- Pydantic 2 / pydantic-settings：数据校验和环境配置。
- PostgreSQL / psycopg：关系数据库。
- PyYAML：剧本 YAML 解析和序列化。
- cryptography：API Key 加密。
- LangChain / langchain-openai：OpenAI 兼容聊天模型调用。
- pytest：后端测试。

前端：

- Vue 3：前端框架。
- Vue Router：路由。
- Vite：开发服务器与构建。
- Element Plus / @element-plus/icons-vue：UI 组件与图标。
- Axios：HTTP 客户端。
- TypeScript / vue-tsc：类型检查。

第三方模型：

- 支持 OpenAI Chat Completions 兼容接口。
- 已按 DeepSeek 等供应商的配置方式设计，具体供应商通过前端“模型配置”录入。

## 环境要求

- Windows PowerShell 或等效 shell。
- Python 3.12。
- Node.js 20+ 与 npm。
- PostgreSQL 14+。
- 可用的 OpenAI 兼容大模型 API Key。

## 安装步骤

### 1. 克隆项目

```powershell
git clone https://github.com/ZaiXiaJiaoTu/ai-novel-screenplay.git
cd ai-novel-screenplay
```

### 2. 初始化数据库

确保 PostgreSQL 服务已启动，然后执行：

```powershell
psql -U postgres -f sql\init.sql
```

如果数据库已存在，按需先手动创建库或调整 `sql/init.sql` 中的数据库名。

老库升级可按历史情况执行：

```powershell
psql -U postgres -d ai_novel_screenplay -f sql\cleanup_legacy_bookshelf.sql
psql -U postgres -d ai_novel_screenplay -f sql\cleanup_legacy_script_flow.sql
psql -U postgres -d ai_novel_screenplay -f sql\upgrade_script_adaptation_workflow.sql
psql -U postgres -d ai_novel_screenplay -f sql\upgrade_script_character_facts.sql
psql -U postgres -d ai_novel_screenplay -f sql\update_default_prompt_templates_zh.sql
```

### 3. 配置后端环境变量

```powershell
Copy-Item backend\.env.example backend\.env
```

编辑 `backend\.env`：

```env
APP_NAME=ai-novel-screenplay
APP_VERSION=0.1.0
ENV=development
HOST=127.0.0.1
PORT=8000
RELOAD=true
DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/ai_novel_screenplay
SECRET_KEY=请替换为本机随机长密钥
CORS_ORIGINS=["http://127.0.0.1:5173","http://localhost:5173"]
```

生产环境必须：

- 设置 `ENV=production`。
- 设置 `RELOAD=false`。
- 使用高强度随机 `SECRET_KEY`。
- 使用独立数据库账号和最小权限；如数据库需要密码，请只写入本地 `.env`。
- 不提交真实 `.env`、API Key、数据库密码和运行日志。

### 4. 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

后端地址：

- API：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/api/health`
- 数据库检查：`http://127.0.0.1:8000/api/health/db`
- OpenAPI：`http://127.0.0.1:8000/api/docs`

### 5. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端地址：`http://127.0.0.1:5173`

### 6. 配置大模型

进入前端“模型配置”，新增 OpenAI 兼容配置。DeepSeek 示例：

- 供应商：`deepseek`
- Base URL：`https://api.deepseek.com/v1`
- 模型名称：`deepseek-chat`
- API Key：填入你的密钥
- 任务范围：可留空表示所有任务，或选择指定任务
- 启用：是
- 默认：是

然后进入“提示词模板”，点击“初始化默认模板”。

## 使用流程

1. 打开“小说书架”，上传 `.txt` 或粘贴小说正文。
2. 检查章节切分结果，必要时新增、编辑或删除章节。
3. 打开“剧本生成”，基于小说创建改编项目。
4. 在“剧情事件拆分”中执行单次或全部拆分。
5. 在“人物”中检查人物档案，可执行 AI 一键整合。
6. 在“剧本生成”中设置每集事件数，生成单集或全部剧集。
7. 使用中文表单或 YAML 源码编辑单集剧本。
8. 在“剧本导出”中导出 YAML 或 TXT。
9. 出现生成失败或质量问题时，查看“调用日志”和“提示词模板”。

## 测试与构建

后端测试：

```powershell
backend\.venv\Scripts\python.exe -m pytest -p no:cacheprovider
```

前端构建：

```powershell
cd frontend
npm run build
```

## 目录说明

```text
backend/                 FastAPI 后端
frontend/                Vue 3 前端
sql/                     数据库初始化、升级和清理脚本
docs/                    需求、API、数据库和 YAML 设计文档
```

## 文档

- [需求文档](docs/PROJECT_SPEC.md)
- [API 设计](docs/API_DESIGN.md)
- [数据库设计](docs/DATABASE_DESIGN.md)
- [YAML 设计](docs/YAML_SCHEMA.md)

## 安全说明

- `.env` 已加入 `.gitignore`，不要提交真实配置。
- 大模型 API Key 通过 `cryptography.Fernet` 加密后保存到数据库。
- 调用日志只保存请求/响应摘要，不保存完整提示词和完整模型输出。
- 生产环境默认拒绝使用开发 `SECRET_KEY` 或开启热重载。

## 开发规范

项目按小粒度 PR 推进，每个 PR 只实现或修改单一功能。主分支在每次合并后保持可运行，便于任意时间复现演示效果。
