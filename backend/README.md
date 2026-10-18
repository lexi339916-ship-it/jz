# FastAPI 后端（完整实现）

## 运行

1. Python 3.10+，建议使用虚拟环境：
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```
2. 开发模式直接启动（默认 SQLite，自动建表并写入系统预置分类）：
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
3. 打开 `http://127.0.0.1:8000/docs` 查看接口文档。

## 配置

复制 `.env.example` 为 `.env`：

- `DATABASE_URL`：默认 SQLite 快速体验；正式部署改为
  `mysql+pymysql://user:password@127.0.0.1:3306/smart_life`（先导入 `database/schema.sql`）
- `JWT_SECRET`：生产环境必须替换为长随机串
- `AI_BASE_URL / AI_API_KEY / AI_MODEL`：任意 OpenAI 兼容接口；
  未配置时 AI 接口返回 503，其余功能不受影响（降级策略）
- `AI_DAILY_LIMIT`：每用户每日调用上限（成本控制）

## 模块结构

```
app/
├── main.py          # 入口：路由注册、统一错误格式、启动建表与种子分类
├── config.py        # 环境变量集中读取
├── database.py      # SQLAlchemy 引擎与会话
├── models.py        # ORM 模型（users/bills/notes/budgets/ai_call_logs 等 6 表）
├── schemas.py       # Pydantic 请求/响应契约
├── security.py      # PBKDF2 密码哈希 + JWT 签发校验
├── deps.py          # get_db / get_current_user 依赖
├── routers/         # auth / categories / bills / notes / budgets / statistics / ai
└── services/ai_service.py  # 模型调用、提示词、JSON 提取校验、限流、日志、脱敏
```

## 设计要点

- **认证与隔离**：JWT Bearer 鉴权；所有业务接口按 user_id 过滤，跨用户访问返回 404
- **AI 人机协同**：`/api/ai/parse-bill`、`/api/ai/parse-note` 只返回草稿，
  用户确认后走 `/api/bills`、`/api/notes` 保存（`source=ai` 字段可追溯）
- **AI 工程化**：调用超时 + 一次重试、每用户每日限流、调用日志落库
  （ai_call_logs 记录功能/提示词版本/模型/耗时/状态）、模糊信息不猜测、
  备注敏感数字自动脱敏、提示词注入防护
- **统一错误**：所有错误响应为 `{"code": HTTP状态码, "message": 提示}`，
  参数校验失败返回 422 并注明字段
