# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目概述

AI 健康生活馆 — 保健品电商竞争模拟平台。5 个 AI（DeepSeek / GPT / 豆包 / MiMo / 通义千问）各自管理一款保健品，平台 AI 动态分配顾客流量，每日推进模拟竞争。

## 常用命令

```bash
# 后端（端口 8000）
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端（端口 5174，代理 /api → 8000）
cd frontend && npm run dev

# 安装依赖
cd backend && pip install -r requirements.txt
cd frontend && npm install

# 数据库（SQLite，文件 backend/ai_health_mall.db，首次启动自动创建）
# 重置模拟：POST /api/v1/admin/reset
```

## 架构

```text
backend/                          frontend/
├── main.py        FastAPI 入口    ├── src/App.vue      应用入口
├── config.py      pydantic 配置   ├── src/pages/       8 个页面
├── constants.py   共享常量        ├── src/api/         8 个 API 模块
├── core/database.py SQLAlchemy   ├── src/stores/      Pinia 状态
├── models/        7 个 ORM 模型   ├── src/components/  2 个组件
├── api/           8 个路由        ├── src/router/      Vue Router
├── services/      业务服务        ├── src/composables/ 主题组合式函数
├── ai/            AI Provider 体系 └── vite.config.ts   Vite 代理
│   ├── provider_registry.py  注册中心
│   ├── base_provider.py      抽象基类
│   └── providers/            5 个 OpenAI 兼容 Provider
└── data/          种子数据 JSON
```

## 关键设计

**Vite 代理**：开发时前端请求 `/api/*` 自动转发到 `localhost:8000`，代码写相对路径即可。

**AI Provider 注册中心**（`backend/ai/provider_registry.py`）：各 Provider 通过 `@register_provider("key")` 装饰器自动注册，调用方用 `get_provider(key, api_key)` 获取实例，无需硬编码类名。

**日期推进模拟**（`backend/services/day_simulation_service.py`）：核心竞争引擎。流程：平台 AI 分配流量 → 5 个商家 AI 并行决策（定价/促销/目标人群）→ 概率引擎生成订单 → 排名更新。通过 `POST /api/v1/admin/advance-day` 触发，轮询 `GET /api/v1/admin/advance-day-status` 获取进度。

**营销策略生成**（`backend/services/marketing_service.py`）：独立于日期推进的老策略系统，`POST /api/v1/admin/generate-strategies` 触发，根据产品历史销售数据生成定价/促销/文案建议，小幅调整自动执行，大幅变更需审批。

**种子数据**（`backend/services/seed_service.py`）：首次启动时从 `backend/data/` 下的 JSON 文件读取并初始化 5 个产品、18 个明星用户、统计用户和模拟配置。已有数据时跳过。

**共享常量**（`backend/constants.py`）：`CATEGORY_DEMO_AFFINITY`（品类-人群匹配度）、`DEMOGRAPHIC_RATIO`（人口比例基准），避免在多服务间重复定义。

**前端全局错误处理**（`frontend/src/api/client.ts`）：axios 响应拦截器统一捕获超时、网络错误、500/404/400 等，通过 ant-design-vue `message.error()` 提示，页面不再卡 loading。

**状态管理**：Pinia 中的 `customer` store 管理当前模拟顾客身份切换，`cart` store 管理购物车增删改查。
