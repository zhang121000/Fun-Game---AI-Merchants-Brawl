# AI 健康生活馆 · Fun Game — AI Merchants Brawl

AI 保健品电商竞争模拟平台。5 个 AI（DeepSeek / GPT / 豆包 / MiMo / 通义千问）各自管理一款保健品，平台 AI 动态分配顾客流量，每日推进模拟竞争。

>  💡 思路来源：抖音 **梯度下沉君**

## 核心玩法

```
平台 AI（DeepSeek）→ 分配顾客流量
        ↓
5 个商家 AI → 各自决策：定价 / 促销 / 目标人群 / 研发新品
        ↓
概率引擎 → 按品类匹配度和转化率生成订单
        ↓
排名更新 → 垫底 AI 收到平台警告，可降价或研发翻盘
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python · FastAPI · SQLAlchemy (异步) · SQLite |
| 前端 | React 18 · TypeScript · Vite · Ant Design 5 · ECharts |
| AI | DeepSeek · GPT-4o · 豆包 · MiMo · 通义千问（OpenAI 兼容协议） |
| 状态管理 | Zustand |

## 快速开始

```bash
# 1. 后端
cd backend
pip install -r requirements.txt
cp .env.example .env   # 填入各 AI 的 API Key
uvicorn main:app --reload

# 2. 前端（新终端）
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

## 项目结构

```
├── backend/          FastAPI 后端 (8000)
│   ├── api/          8 个路由模块
│   ├── ai/           5 个 AI Provider + 注册中心
│   ├── services/     模拟引擎 + 营销策略 + 种子数据
│   ├── models/       7 个 ORM 模型
│   └── data/         种子数据 JSON
├── frontend/         React 前端 (5173)
│   └── src/pages/    7 个页面
└── docs/             设计文档
```
