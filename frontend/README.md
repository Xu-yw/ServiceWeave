# ServiceWeave Frontend

Vue 3 与 Vite 实现的用户聊天界面和开发者工作台，连接仓库中的 Python 后端。

```bash
npm ci
npm run dev
npm run build
```

开发服务默认监听本机 5173，将 `/api/python` 代理到 `http://127.0.0.1:8000`。容器内由 Nginx 将相同路径代理到 `backend:8000`，见 [启动说明](../README.md)。

界面共享当前会话、消息和输入框状态；浏览器存储仅保存连接设置，刷新后不会恢复聊天气泡。`public/runtime-config.js` 使用 `window.__SERVICEWEAVE_CONFIG__`，只包含公开连接配置。
