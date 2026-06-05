# ai-novel-screenplay

AI 小说剧本改编辅助系统，面向小说作者、内容创作者和剧本创作者。项目采用 FastAPI 后端、Vue 3 前端和 PostgreSQL 数据库，支持从小说导入到剧本生成、编辑、导出的演示闭环。

## 功能概览

- 小说导入：支持文本粘贴和 txt 文件上传，自动解析章节和篇幅类型。
- 章节预处理：支持章节摘要生成，缺少模型配置时会降级生成可演示摘要。
- 故事设定：支持故事设定档案生成、查看和更新。
- 剧本生成：支持创建剧本生成任务，生成风格策略、场景规划、剧本 YAML，并保存到剧本书架。
- 剧本书架：支持查看项目/片段、编辑剧本片段、删除片段、下载 YAML/TXT。
- 大模型配置：支持 OpenAI 兼容 API 配置、加密保存 API Key、测试连接和设默认配置。
- 提示词模板：支持默认模板初始化、筛选、编辑、启停、版本查看和回滚。
- 调用日志：支持查看大模型调用状态、耗时、Token 用量、请求/响应摘要和错误信息。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic、PostgreSQL、LangChain
- 前端：Vue 3、Vite、Element Plus、Axios
- 模型 API：兼容 OpenAI Chat Completions 格式，可配置 DeepSeek 等供应商
- 导出：YAML/TXT

## 本地启动

### 1. 准备数据库

确保本机 PostgreSQL 可用，然后执行初始化 SQL：

```powershell
psql -U postgres -f sql\init.sql
```

如果你的数据库账号、密码或端口不是默认值，请在 `backend\.env` 中修改 `DATABASE_URL`。

### 2. 配置后端环境变量

```powershell
Copy-Item backend\.env.example backend\.env
```

按需修改 `backend\.env`。DeepSeek 示例：

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_novel_screenplay
SECRET_KEY=replace-with-a-local-random-secret
```

大模型 API Key 不需要写进 `.env`。启动后进入前端“模型配置”页面新增配置：

- 供应商：`deepseek`
- Base URL：`https://api.deepseek.com/v1`
- 模型名称：`deepseek-chat`
- API Key：填写你的 DeepSeek API Key

### 3. 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

后端默认地址：`http://127.0.0.1:8000`
健康检查：`http://127.0.0.1:8000/api/health`
OpenAPI 文档：`http://127.0.0.1:8000/api/docs`

### 4. 可选：初始化演示数据

如果希望快速看到完整演示内容，可以在数据库初始化后执行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.seed_demo_data
```

该命令会幂等创建一套演示小说、章节摘要、故事设定档案和已生成的剧本项目。

### 5. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端默认地址：`http://127.0.0.1:5173`

## 演示流程

完整演示步骤见 [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)。

最短路径：

1. 打开“模型配置”，新增并测试 DeepSeek 配置。
2. 打开“提示词模板”，点击“初始化默认模板”。
3. 打开“待选书架”，导入一段带章节标题的小说文本。
4. 选择作品，点击“生成章节摘要”。
5. 打开“剧本书架”，点击“生成剧本”，选择作品并启动任务。
6. 在剧本书架查看片段，编辑内容，并下载 YAML/TXT。
7. 打开“调用日志”，查看模型调用记录。

## 测试

后端：

```powershell
backend\.venv\Scripts\python.exe -m pytest -p no:cacheprovider
```

前端：

```powershell
cd frontend
npm run build
```

## 开发原则

项目按小粒度 PR 推进，每个 PR 只实现一类功能。主分支在每次合并后保持可运行，便于任意时间复现演示效果。
