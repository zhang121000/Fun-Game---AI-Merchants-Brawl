# 技术演进设计规格 — AI 健康生活馆

> 日期：2026-05-20
> 状态：草稿
> 方案：功能驱动（方案 A）

## 1. 背景与目标

### 1.1 当前技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + SQLAlchemy（异步）+ SQLite |
| AI 层 | 5 个 OpenAI 兼容 Provider（GLM / GPT / Kimi / MiniMax / 通义千问），手写 prompt 拼接 |
| 前端框架 | React 18 + TypeScript + Ant Design + ECharts + Zustand |
| 构建工具 | Vite 5 |
| 基础设施 | Docker Compose |
| 测试 | 后端仅 1 个测试文件，前端无测试 |

### 1.2 进化目标

以学习为导向，通过 3 个具体功能引入现代前端、AI 工程、实时通信三类新技术。每个功能独立可交付，学习有成就感。

### 1.3 约束

- 不破坏现有功能，增量演进
- 保持现有 5 个 AI Provider 体系不变
- 优先学习价值，其次才是性能优化

---

## 2. 功能 1：实时竞赛直播看板

### 2.1 目标

日期推进时，所有在线用户实时看到排名变化和订单动态，替换当前的轮询机制。

### 2.2 架构

```
后端 (FastAPI)
├── WebSocket 端点: /ws/competition
├── ConnectionManager 类
│   ├── connect(websocket) — 注册新客户端
│   ├── disconnect(websocket) — 移除断开的客户端
│   └── broadcast(message) — 向所有客户端广播
└── day_simulation_service.py
    └── 每个模拟步骤完成后调用 broadcast()

前端 (React)
├── useCompetitionWS() 自定义 Hook
│   ├── 建立 WebSocket 连接
│   ├── 断线自动重连（指数退避：1s → 2s → 4s → 8s，上限 30s）
│   └── 解析消息 → 更新 Zustand competitionStore
├── CompetitionLiveBoard 组件
│   ├── 排名变化动画（CSS transition）
│   └── ECharts 实时折线图（销量趋势）
└── 替换 AdminDashboard 中的轮询逻辑
```

### 2.3 消息协议

```typescript
// 所有消息的统一格式
interface WSMessage {
  type: 'day_start' | 'traffic_allocated' | 'merchant_decided' | 'orders_generated' | 'ranking_updated' | 'day_complete'
  day: number
  data: Record<string, unknown>
  timestamp: string  // ISO 8601
}

// 示例：排名更新消息
{
  type: 'ranking_updated',
  day: 15,
  data: {
    rankings: [
      { merchant_id: 1, name: 'GLM 旗舰店', sales: 12500, rank: 1, change: 0 },
      { merchant_id: 2, name: 'GPT 旗舰店', sales: 11800, rank: 2, change: 1 },
    ]
  },
  timestamp: '2026-05-20T14:30:00Z'
}
```

### 2.4 连接管理

- 服务端维护 `active_connections: list[WebSocket]`
- 客户端断开时自动从列表移除（在 `broadcast()` 中 try/except 包裹 `send_json`，捕获 `WebSocketDisconnect` 异常后调用 `disconnect()`）
- 客户端重连时发送最近一次的完整状态快照（避免错过中间消息）
- 心跳：服务端每 30 秒发送 ping，客户端响应 pong，超时 60 秒断开

### 2.5 前端状态管理

```typescript
// stores/competitionStore.ts
interface CompetitionState {
  currentDay: number
  isSimulating: boolean
  latestEvent: WSMessage | null
  rankings: RankingEntry[]
  dayEvents: WSMessage[]  // 当天所有事件，用于回放
}

// useCompetitionWS Hook 返回值
interface UseCompetitionWS {
  isConnected: boolean
  connect: () => void
  disconnect: () => void
}
```

### 2.6 错误处理

| 场景 | 处理方式 |
|------|----------|
| WebSocket 连接失败 | 指数退避重连，最多 5 次后降级为轮询 |
| 消息解析失败 | 忽略该消息，console.warn 记录 |
| 服务端广播失败 | 跳过断开的连接，不影响其他客户端 |
| 页面不可见时 | 使用 Page Visibility API，隐藏时降低更新频率 |

### 2.7 新技术点

- `FastAPI WebSocket`：连接生命周期管理、广播模式
- 自定义 `useWebSocket` Hook：封装连接、重连、消息解析
- `Zustand` 扩展：新增 competitionStore
- `Page Visibility API`：优化后台标签页性能

---

## 3. 功能 2：AI 决策引擎进化

### 3.1 目标

用 LangChain Agent + RAG 改进现有的 5 个商家 AI 决策系统，让决策更智能、推理过程可追溯。

### 3.2 现状分析

当前流程（`day_simulation_service.py` + `ai/providers/`）：
1. 手动拼接 prompt 字符串（包含历史销售数据、竞品信息、用户画像）
2. 调用 OpenAI 兼容 API
3. 手动解析 JSON 响应
4. 提取定价、促销、目标人群等决策

问题：
- prompt 维护困难，散落在多个文件中
- 无法利用历史决策经验
- 决策过程不可追溯
- Agent 无法自主选择需要的信息

### 3.3 进化后架构

```
backend/ai/
├── agents/
│   ├── merchant_agent.py        # LangChain Agent 主体
│   ├── tools/
│   │   ├── product_search.py    # Chroma 向量检索 — 语义搜索产品数据
│   │   ├── sales_analyzer.py    # 工具：查询历史销量趋势
│   │   ├── competitor_spy.py    # 工具：查看竞品定价/促销
│   │   └── decision_logger.py   # 工具：记录决策理由到数据库
│   └── prompts/
│       └── merchant_persona.py  # 从现有 persona_templates.py 迁移
├── rag/
│   ├── indexer.py               # 产品数据 + 历史决策 → Chroma 向量化
│   └── retriever.py             # 语义检索接口
├── providers/                   # 保留现有，作为 LLM 后端
└── decision_log.py              # 决策日志模型和存储
```

### 3.4 LangChain Agent 设计

```python
# merchant_agent.py 核心逻辑
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool

@tool
def search_product_info(query: str) -> str:
    """语义搜索产品信息，如成分、适用人群、历史评价"""
    # Chroma 向量检索
    ...

@tool
def analyze_sales_trend(merchant_id: int, days: int = 7) -> str:
    """查看指定商家最近 N 天的销量趋势"""
    # 数据库查询
    ...

@tool
def check_competitor_pricing(merchant_id: int) -> str:
    """查看竞品当前定价和促销活动"""
    # 数据库查询
    ...

@tool
def log_decision_reasoning(reasoning: str, decision: dict) -> str:
    """记录决策推理过程"""
    # 写入 decision_log 表
    ...

# Agent 创建
agent = create_openai_tools_agent(
    llm=llm,  # 复用现有 Provider
    tools=[search_product_info, analyze_sales_trend, check_competitor_pricing, log_decision_reasoning],
    prompt=merchant_persona_prompt
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

### 3.5 RAG 数据来源

| 数据源 | 内容 | 向量化方式 |
|--------|------|------------|
| `products_seed.json` | 产品名称、描述、成分、适用人群 | 按产品分块，每块一个文档 |
| 历史决策日志 | 过去 N 天的 AI 决策和理由 | 按决策分块，附加日期和商家标签 |
| 用户画像数据 | 人群分类、购买偏好、消费能力 | 按人群分块 |

### 3.6 Chroma 配置

```python
# rag/indexer.py
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./data/chroma_db",  # 本地持久化
    settings=Settings(anonymized_telemetry=False)
)

product_collection = client.get_or_create_collection(
    name="products",
    metadata={"hnsw:space": "cosine"}
)

# 索引构建：启动时或数据变更时调用
def index_products(products: list[dict]):
    product_collection.add(
        documents=[p["description"] + " " + " ".join(p["ai_selling_points"]) for p in products],
        metadatas=[{"id": p["id"], "name": p["name"], "category": p["category"], "price": p["price"]} for p in products],
        ids=[f"product_{p['id']}" for p in products]
    )
```

### 3.7 决策日志模型

```python
# models/decision_log.py
class DecisionLog(Base):
    __tablename__ = "decision_logs"
    id = Column(Integer, primary_key=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"))
    day = Column(Integer)
    tools_called = Column(JSON)       # 调用了哪些工具
    tool_results = Column(JSON)       # 工具返回的原始数据
    reasoning = Column(Text)          # AI 的推理过程
    final_decision = Column(JSON)     # 最终决策（定价、促销、目标人群）
    token_usage = Column(Integer)     # token 消耗
    latency_ms = Column(Integer)      # 响应时间
    created_at = Column(DateTime, default=func.now())
```

### 3.8 兼容性策略

- 新 Agent 系统与现有 Provider 系统并行存在
- 通过配置开关切换：`AI_DECISION_MODE=legacy|agent`（在 `backend/config.py` 的 `pydantic-settings` 中添加，默认 `legacy`）
- legacy 模式使用现有手写 prompt，agent 模式使用 LangChain Agent
- 可以逐个商家切换（通过 `AI_AGENT_MERCHANTS=1,3` 指定哪些商家使用 agent 模式），不需要一次性全部迁移

### 3.9 新技术点

- `LangChain`：Agent 架构、Tool 定义、Prompt 模板、Chain 编排
- `Chroma`：向量数据库、文档嵌入、语义检索、本地持久化
- `决策可追溯`：结构化存储 AI 推理过程

---

## 4. 功能 3：前端现代化改造（首页）

### 4.1 目标

用 Tailwind CSS 重写首页样式，拆分组件，加上 Vitest 单元测试和 Playwright E2E 测试。

### 4.2 当前状态

- `Home.tsx`：274 行单文件，大量内联 `style`，使用 Ant Design Carousel/Button/Tag
- 无测试覆盖
- 样式与逻辑耦合，难以维护

### 4.3 组件拆分

```
frontend/src/
├── components/
│   └── home/
│       ├── HeroSection.tsx        # 顶部 Hero 区域（标题 + 按钮）
│       ├── ProductCarousel.tsx    # 产品轮播容器（箭头 + Carousel）
│       ├── ProductSlide.tsx       # 单个产品幻灯片（产品图 + 信息）
│       └── HomeFooter.tsx         # 底部 Footer
├── pages/
│   └── Home.tsx                   # 精简为组合上述组件
```

### 4.4 Tailwind CSS 迁移策略

**渐进式迁移**，不一次性替换所有样式：

1. 安装 Tailwind CSS + PostCSS + autoprefixer
2. 配置 `tailwind.config.js`，扫描 `src/**/*.{tsx,ts}`
3. 从新组件开始用 Tailwind，旧组件保持不变
4. 逐步替换内联 style 为 Tailwind class

**示例对比**：

```tsx
// 当前：内联样式
<h1 style={{
  fontSize: 56, fontWeight: 600, color: '#1d1d1f',
  letterSpacing: '-0.016em', lineHeight: 1.07, marginBottom: 12,
}}>
  AI 健康生活馆
</h1>

// 改后：Tailwind
<h1 className="text-5xl font-semibold text-gray-900 tracking-tight leading-none mb-3">
  AI 健康生活馆
</h1>
```

**保留 Ant Design 组件**：Carousel、Button、Tag 继续使用，只替换自定义样式部分。长期策略：Ant Design 用于复杂交互组件（表格、表单、轮播），Tailwind 用于布局和自定义样式，两者共存。

### 4.5 Vitest 单元测试

```typescript
// __tests__/home/HeroSection.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import HeroSection from '@/components/home/HeroSection'

describe('HeroSection', () => {
  it('渲染标题和描述', () => {
    render(<HeroSection />)
    expect(screen.getByText('AI 健康生活馆')).toBeInTheDocument()
    expect(screen.getByText(/5 款明星保健品/)).toBeInTheDocument()
  })

  it('包含导航按钮', () => {
    render(<HeroSection />)
    expect(screen.getByText('电竞控制台')).toBeInTheDocument()
    expect(screen.getByText('查看数据看板')).toBeInTheDocument()
  })
})

// __tests__/utils/discount.test.ts
import { describe, it, expect } from 'vitest'
import { calculateDiscount } from '@/utils/discount'

describe('calculateDiscount', () => {
  it('计算正确折扣百分比', () => {
    expect(calculateDiscount(100, 80)).toBe(20)
  })
  it('原价低于现价时返回 0', () => {
    expect(calculateDiscount(80, 100)).toBe(0)
  })
})
```

### 4.6 Playwright E2E 测试

```typescript
// e2e/home.spec.ts
import { test, expect } from '@playwright/test'

test.describe('首页', () => {
  test('加载产品轮播', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('AI 健康生活馆')).toBeVisible()
    // 等待产品加载
    await expect(page.getByText('查看 AI 策略详情').first()).toBeVisible()
  })

  test('点击产品详情跳转', async ({ page }) => {
    await page.goto('/')
    await page.getByText('查看 AI 策略详情').first().click()
    await expect(page).toHaveURL(/\/product\/\d+/)
  })

  test('响应式布局 - 移动端', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/')
    await expect(page.getByText('AI 健康生活馆')).toBeVisible()
  })
})
```

### 4.7 新增依赖

```json
{
  "devDependencies": {
    "tailwindcss": "^4.0",
    "@tailwindcss/vite": "^4.0",
    "vitest": "^3.0",
    "@testing-library/react": "^16.0",
    "@testing-library/jest-dom": "^6.0",
    "jsdom": "^26.0",
    "@playwright/test": "^1.50"
  }
}
```

### 4.8 新技术点

- `Tailwind CSS`：Utility-first CSS、响应式设计、与 Ant Design 共存
- `Vitest`：Vite 原生测试框架、快照测试、覆盖率报告
- `@testing-library/react`：用户行为驱动的组件测试
- `Playwright`：跨浏览器 E2E 测试、截图对比

---

## 5. 新增依赖汇总

### 5.1 后端新增

```
langchain>=0.3
langchain-openai>=0.2
chromadb>=0.5
```

### 5.2 前端新增

```
tailwindcss>=4.0
@tailwindcss/vite>=4.0
vitest>=3.0
@testing-library/react>=16.0
@testing-library/jest-dom>=6.0
jsdom>=26.0
@playwright/test>=1.50
```

---

## 6. 实施顺序

| 阶段 | 功能 | 预计工作量 | 依赖 |
|------|------|------------|------|
| 1 | 实时竞赛直播看板 | 2-3 天 | 无 |
| 2 | AI 决策引擎进化 | 3-4 天 | 无 |
| 3 | 前端现代化改造 | 2-3 天 | 无 |

三个功能相互独立，可以并行开发，也可以按任意顺序实施。

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LangChain 版本更新频繁，API 变化大 | 学习成本增加 | 锁定版本，参考官方文档 |
| Chroma 本地持久化数据丢失 | 需要重建索引 | 启动时自动检查并重建 |
| Tailwind 与 Ant Design 样式冲突 | 视觉不一致 | 用 Tailwind prefix 或 scope 隔离 |
| WebSocket 连接数过多 | 服务端内存压力 | 限制最大连接数，心跳检测清理 |
| 前端测试引入后维护成本 | 开发变慢 | 先测核心逻辑，不追求 100% 覆盖率 |

---

## 8. 成功标准

- [ ] 实时看板：日期推进时，多个浏览器标签页能同时看到实时更新
- [ ] AI 决策引擎：Agent 能自主调用工具获取信息，决策日志可查询
- [ ] 前端改造：首页用 Tailwind 渲染，Vitest 测试通过，Playwright E2E 通过
- [ ] 所有现有功能不受影响
