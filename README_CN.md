# AI 健康生活馆 | Fun Game | AI Merchants Brawl

[English](README.md) | 简体中文

AI 健康生活馆是一个保健品电商竞争模拟平台。5 个 AI 商家分别经营不同品类的保健品，平台 AI 会根据每日经营表现动态分配顾客流量，商家 AI 再独立决定定价、促销、人群定位和补货策略，最终通过概率引擎生成订单并更新排名。

## 项目亮点

- 5 个独立 AI 商家，分别接入不同的 OpenAI 兼容模型
- 平台 AI 每日分配 500 个模拟顾客线索
- 商家 AI 独立决策定价、促销、目标人群、卖点和补货
- 概率引擎结合折扣、促销和品类匹配度生成订单
- 支持推进模拟、查看排行、经营分析和后台管理

## 5 个 AI 商家

| AI | 产品 | 品类 | 起售价 | 原价 | 目标人群 |
|---|---|---|---|---|---|
| DeepSeek | 乳清蛋白粉 | 蛋白粉 | ¥168 | ¥228 | 青年 |
| GPT-4o | 复合维生素矿物质片 | 维生素 | ¥168 | ¥218 | 全年龄 |
| 豆包 | 液体钙软胶囊 | 钙片 | ¥128 | ¥168 | 老年 |
| MiMo | 益生菌冻干粉 | 益生菌 | ¥138 | ¥178 | 儿童 |
| 通义千问 | 深海鱼油 Omega-3 胶囊 | 鱼油 | ¥128 | ¥198 | 老年 |

每个 AI 都通过独立 API 调用运行，彼此之间不共享策略和数据。

## 顾客池

系统内置一个 5000+ 的模拟顾客池，包含 18 位明星用户和大量按统计分布生成的普通用户。

每位顾客都有独立属性：

- 品类偏好向量
- 价格敏感度
- 品牌忠诚度
- 时间行为模式

## 每日模拟流程

点击“推进明天”或调用 `POST /api/v1/admin/advance-day`，即可触发完整的一日竞争循环。

1. 平台 AI 根据商家表现和人群比例分配流量。
2. 5 个商家 AI 并行完成定价、促销、目标人群、卖点和补货决策。
3. 概率引擎根据这些决策生成订单。
4. 每日结束后更新排名与平台建议。

## 管理后台

管理员可以：

- 逐日推进模拟
- 查看销量、营收、价格、促销和目标人群
- 检查 AI 决策日志
- 审阅平台建议
- 跟踪研发项目
- 管理库存
- 一键重置模拟

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Python / FastAPI / Async SQLAlchemy / SQLite |
| 前端 | Vue 3 / TypeScript / Vite / Ant Design Vue / ECharts |
| AI | DeepSeek / GPT-4o / 豆包 / MiMo / 通义千问（OpenAI 兼容协议） |
| 状态管理 | Pinia / Axios 拦截器统一错误处理 |

## 项目结构

```text
backend/
  main.py              FastAPI 入口
  config.py            配置
  constants.py         共享常量
  core/database.py     数据库初始化
  models/              ORM 模型
  api/                 接口路由
  services/            业务服务
  ai/                  AI Provider 与图执行逻辑
  data/                种子数据

frontend/
  src/App.vue          应用入口
  src/pages/           页面
  src/api/             API 封装
  src/stores/          Pinia 状态
  src/components/      组件
  src/router/          Vue Router
  vite.config.ts       本地代理配置
```

## 快速开始

```bash
# 1. 后端（端口 8000）
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. 前端（端口 5174，/api 代理到 8000）
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5174`，进入管理后台后点击“推进明天”即可开始模拟。

## API 说明

常用管理接口：

- `POST /api/v1/admin/advance-day`：推进一天
- `GET /api/v1/admin/advance-day-status`：查询推进进度
- `POST /api/v1/admin/generate-strategies`：生成营销策略
- `POST /api/v1/admin/reset`：重置模拟

## 许可证

本项目基于 [MIT License](LICENSE) 开源。
