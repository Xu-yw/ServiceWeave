# ServiceWeave Backend

FastAPI 后端，负责多 Agent 编排、意图识别、RAG、会话记忆、监控和离线评测。

启动方式见 [仓库说明](../README.md)。仓库根目录运行 `docker compose up -d --build`，后端监听本机 8000。

主要接口：`/health`、`/chat`、`/skills`、`/knowledge/stats`、`/knowledge/add`、`/knowledge/upload`、`/search`、`/monitor`、`/metrics`、`/eval/run`。完整参数以 `/docs` 为准。

Skills 使用 `SERVICEWEAVE_SKILLS_DIR` 和 `SERVICEWEAVE_SKILLS_MAX_PROMPT_CHARS`，其他角色配置统一使用 `SERVICEWEAVE_` 前缀。真实模型凭据只放在根目录的 `.env`，不得提交。
