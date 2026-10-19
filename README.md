# 基于 uni-app 的智能记账与生活便签一体化管理系统

课程设计交付包（可运行完整版）。前端 uni-app（Vue 3），后端 FastAPI + SQLAlchemy，
数据库 MySQL（开发模式可用 SQLite 直接运行），AI 能力通过 OpenAI 兼容 API 接入。

## 目录结构

```
smart_life_coursework/
├── frontend/               # uni-app 前端（HBuilderX 项目，10 个页面 + tabBar）
├── backend/                # FastAPI 后端（认证/账单/便签/预算/统计/AI 七组接口）
├── database/schema.sql     # MySQL 8 初始化脚本（含种子分类）
├── tests/
│   ├── ai_test_cases.xlsx      # AI 测试集模板（20 条）
│   ├── run_ai_tests.py         # AI 测试集自动执行脚本
│   └── smoke_test.py           # 后端接口冒烟测试（41 项断言）
├── tools/gen_tabbar_icons.py   # 生成 tabBar 图标
├── diagrams/ docs/             # 设计图（架构/模块/用例/E-R/流程/原型）
└── 课程设计报告_初稿.docx
```

## 快速开始

1. **启动后端**（Python 3.10+）：
   ```bash
   cd backend
   pip install -r requirements.txt
   # 开发模式无需安装数据库，默认使用 SQLite
   uvicorn app.main:app --reload --port 8000
   ```
   浏览器打开 http://127.0.0.1:8000/docs 可查看自动生成的接口文档。

2. **启动前端**：用 HBuilderX 导入 `frontend/` 目录，运行到浏览器（H5）或微信开发者工具。
   后端地址在 `frontend/common/config.js` 中配置；App 真机调试时可在
   **登录页 → 服务器设置** 或 **我的 → 服务器地址** 中填写电脑局域网地址，
   详见 [docs/APK打包说明.md](docs/APK打包说明.md)。

3. **启用 AI 功能**（可选，不配置时系统降级为纯手动记账/便签）：
   ```bash
   cd backend
   copy .env.example .env     # 编辑 .env，填入 AI_BASE_URL / AI_API_KEY / AI_MODEL
   ```
   支持任何 OpenAI 兼容接口（智谱 GLM、通义千问、DeepSeek 等）。

## 正式部署（MySQL）

```bash
mysql -u root -p < database/schema.sql
# 修改 backend/.env：
# DATABASE_URL=mysql+pymysql://user:password@127.0.0.1:3306/smart_life
```

## 测试与验收材料

- 接口冒烟测试：`python tests/smoke_test.py`（覆盖认证、账单、便签、预算、统计、
  AI 降级/限流/脱敏/草稿校验、用户隔离，共 41 项断言，无需配置 AI）
- AI 专项测试：启动后端并配置 AI 后运行 `python tests/run_ai_tests.py`，
  自动执行 20 条用例并生成 `tests/AI测试用例_实测结果.xlsx`
  （已完成一轮实测：模型 glm-4-flash，20/20 通过，结果表内含每条用例的实际输出）
- AI 配置自检：`python tests/verify_ai.py`（登录测试账号并调用一次真实解析）

## 安全约定

- 模型密钥只存于后端 `.env`，不进前端、不进仓库、不进截图与报告
- 密码使用 PBKDF2-SHA256（24 万轮 + 随机盐）哈希存储，接口使用 JWT 鉴权
- 所有账单/便签接口按 user_id 隔离，跨用户访问返回 404
- AI 只生成草稿，必须用户确认后才写入数据库；备注中的疑似敏感数字自动脱敏
