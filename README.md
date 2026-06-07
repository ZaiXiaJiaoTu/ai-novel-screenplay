# AI Novel Screenplay

AI Novel Screenplay 是一个面向中文小说的 AI 剧本改编系统。用户可以上传小说文本，自动切分章节，再通过大模型完成剧情事件拆分、人物档案整理、分集剧本生成、剧本修复、编辑预览和导出。

本发布版本不包含任何演示数据、用户数据、小说内容或大模型 API Key。首次运行后，用户需要自行配置大模型 API、上传小说并生成剧本。
demo演示视频https://www.bilibili.com/video/BV1GQE86RE5d/?spm_id_from=333.1387.homepage.video_card.click&vd_source=5bd8b2a24076ed2acc8b98477028d714

## 技术栈

- 后端：Python 3.12、FastAPI、SQLAlchemy 2、Pydantic 2、PostgreSQL、PyYAML、LangChain、cryptography、pytest
- 前端：Vue 3、TypeScript、Vite、Vue Router、Element Plus、Axios
- 模型接口：OpenAI Chat Completions 兼容 API，支持 DeepSeek 等兼容服务
- 部署：PowerShell 本地启动脚本、Docker、Docker Compose、Nginx

## 环境依赖

本地运行需要：

- Git
- Python 3.12
- Node.js 20+ 与 npm
- PostgreSQL 14+
- 可用的大模型 API Key

Docker 部署需要：

- Docker
- Docker Compose
- 可用的大模型 API Key

## 安装方式

### 方式一：Git 拉取后一键安装依赖并运行

```powershell
git clone https://github.com/ZaiXiaJiaoTu/ai-novel-screenplay.git
cd ai-novel-screenplay
.\scripts\start.ps1
```

首次本地运行前，请确保 PostgreSQL 已启动。脚本会自动安装依赖、创建 `backend/.env`、初始化空数据库并启动前后端。

默认访问地址：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/api/docs

如需指定数据库连接：

```powershell
.\scripts\start.ps1 -DatabaseUrl "postgresql+psycopg://postgres:你的密码@localhost:5432/ai_novel_screenplay"
```

如果你希望手动初始化数据库，可执行：

```powershell
psql -U postgres -f sql\init.sql
.\scripts\start.ps1 -SkipDatabaseInit
```

### 方式二：Docker 一键部署运行

```powershell
git clone https://github.com/ZaiXiaJiaoTu/ai-novel-screenplay.git
cd ai-novel-screenplay
docker compose up -d --build
```

默认访问地址：

- 前端：http://127.0.0.1:8080
- 后端：http://127.0.0.1:8000

可选：启动前设置生产密钥和数据库密码。

```powershell
$env:SECRET_KEY="请替换为随机长密钥"
$env:POSTGRES_PASSWORD="请替换为数据库密码"
docker compose up -d --build
```

停止服务：

```powershell
docker compose down
```

清空 Docker 数据卷：

```powershell
docker compose down -v
```

## 使用流程

1. 打开前端页面。
2. 进入“模型配置”，新增 OpenAI 兼容模型配置，填写 Base URL、模型名称和 API Key，并设为默认。
3. 进入“提示词模板”，点击“初始化默认模板”。
4. 进入“小说书架”，上传 `.txt` 小说或粘贴小说正文。
5. 检查章节切分结果，可手动新增、编辑或删除章节。
6. 进入“剧本生成”，创建剧本改编项目。
7. 在“剧情事件拆分”中执行单次拆分或全部拆分。
8. 在“人物”中查看、编辑或 AI 整合人物档案。
9. 在“剧本生成”中按剧情事件生成单集或全部剧集。
10. 使用中文表单、YAML 源码和文本预览检查剧本内容。
11. 必要时点击“修复剧集”进行单集修复。
12. 在“剧本导出”中导出 YAML 或 TXT。

## 文档链接

- [需求文档](docs/PROJECT_SPEC.md)
- [API 设计](docs/API_DESIGN.md)
- [数据库设计](docs/DATABASE_DESIGN.md)
- [YAML 设计](docs/YAML_SCHEMA.md)

## 发布说明

- 仓库不提交 `backend/.env`、API Key、数据库密码、上传小说、生成剧本、调用日志和本地数据库数据。
- Docker 首次启动只创建空数据库表结构。
- 用户需要自行配置模型 API 并上传小说后才能开始生成。
