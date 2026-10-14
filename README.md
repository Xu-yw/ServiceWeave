# ServiceWeave

面向电商咨询与售后场景的全栈多 Agent 智能客服系统，提供用户聊天界面与开发者工作台，结合意图识别、知识检索和分层记忆支持多轮服务。

## 功能

- **多 Agent 协作**：融合 LLM、向量相似度和关键词识别意图，路由到通用、技术、账单及升级 Agent；支持主辅 Agent 并行处理和失败降级。
- **RAG 工具链**：查询改写、多查询召回、去重及 LLM 重排；工具层支持 TTL 缓存、超时和熔断。
- **分层记忆**：Redis 保存近期会话，ChromaDB 存储长期记忆和用户画像，组合历史摘要与近期原文提供上下文。
- **动态 Skills**：按角色和场景加载业务规范，支持热更新。
- **全栈交互**：Vue 3 聊天界面与开发者工作台共享会话状态，提供知识库导入、工具调用详情、运行监控与评测入口。
- **两类离线评测**：意图分类统计 Accuracy、Macro-F1 和逐类指标；对话采用 LLM-as-Judge 四维评分及关键项校验。

技术栈：Python 3.12、FastAPI、AsyncIO、Redis、ChromaDB、Vue 3、Vite、Docker Compose。

## 目录

| 目录 | 内容 |
| --- | --- |
| backend/api | HTTP API 与 CLI |
| backend/agents | Agent 角色、工具与编排 |
| backend/core | 意图识别和 Skills 加载 |
| backend/mcp | RAG 与工具执行管理 |
| backend/memory | 会话记忆与用户画像 |
| backend/monitor | 运行指标和监控 |
| backend/evaluation | 评测器、测试用例与脚本 |
| backend/skills | 业务规范 |
| backend/tests | 后端单元测试 |
| frontend/src | Vue 界面与 API 封装 |
| frontend/docker | Nginx 同源代理 |

## 启动

安装 Docker Desktop（Linux 容器模式）或 Docker Engine 与 Compose 插件。在仓库根目录复制配置：

```powershell
Copy-Item .env.example .env
```

Linux/macOS 使用 `cp .env.example .env`。填写 `.env` 中的 `ANTHROPIC_API_KEY`、`ANTHROPIC_MODEL` 和 `REDIS_PASSWORD`；使用兼容服务时填写 `ANTHROPIC_BASE_URL`，接口需要支持 Anthropic Messages API。

```bash
docker compose up -d --build
docker compose ps
```

- 前端：http://127.0.0.1:5173
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

首次构建会下载依赖与向量模型。前端通过 `/api/python` 同源访问后端；Redis 和 ChromaDB 在内部网络运行。端口可在 `.env` 修改。当前配置用于本机运行，服务接口尚未实现用户鉴权。

```bash
# 查看日志
docker compose logs -f backend
# 启动容器内 CLI
docker compose exec backend python api/main.py --cli
# 停止服务并保留数据
docker compose down
```

## 开发与测试

后端启动后可单独开发前端（Node.js 22.12+）：

```bash
cd frontend
npm ci
npm run dev
npm run build
```

同时运行容器前端时，先 `docker compose stop frontend` 释放 5173 端口。Vite 默认代理到本机 8000，其他后端地址可用 `VITE_PYTHON_API_URL` 指定。

后端测试使用 Python 3.12：

```bash
cd backend
python -m venv .venv
# 激活虚拟环境后执行
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

## 评测

测试集包含 200 条意图样本和 30 组 60 轮对话，均为合成样本。见 [评测说明](backend/evaluation/README.md) 与 [测试用例](backend/evaluation/测试用例/README.md)。实际评测会调用模型，结果保存在本机并由 Git 忽略。

## 当前边界

系统提供咨询、检索、字段核验和处理建议，尚未接入真实订单、支付、退款与人工坐席执行接口。CLI 与 HTTP 初始化链路存在差异；浏览器刷新后不会恢复聊天气泡。对话评测直接调用编排器，不覆盖持久化记忆读写；实体传递差异可能影响交接用例，详见评测说明。
