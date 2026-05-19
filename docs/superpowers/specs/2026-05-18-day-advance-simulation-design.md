# AI 保健品竞争平台 — 日期推进式设计

## 核心概念

5个AI商家各自选一个保健品品类经营，平台AI动态分配顾客流量，每天推进一天观察竞争结果。

## 系统架构

```
平台AI（豆包 Seed 2.0 Pro）→ 分配顾客流量
    ↓
5个商家AI（DeepSeek/GPT/豆包/MiMo/Qwen）→ 各自决策定价/促销/目标人群
    ↓
概率引擎 → 生成订单
    ↓
排名更新 → 垫底AI收到平台建议（研发新品 or 调整营销）
```

## 顾客池（真实人口比例）

- 儿童（0-14岁）：~18%
- 青年（15-35岁）：~30%
- 中年（36-59岁）：~35%
- 老年（60+岁）：~17%

## 品类池（AI启动时自选，锁定）

蛋白粉、维生素、钙片、益生菌、鱼油、胶原蛋白、褪黑素、枸杞

## 每天推进流程

1. 平台AI分配顾客（哪类人→哪个商家，多少流量）
2. 5个商家AI并行决策（定价、促销、目标人群、是否研发）
3. 概率引擎计算销量（流量×转化率×随机扰动）
4. 写入订单、更新排名、触发平台建议

## 研发机制

- 垫底AI可选择研发新品（同一品类细分）
- 研发需2-3天上架
- 新品上架后旧品保留或替换

## 平台AI配置

- API: https://ark.cn-beijing.volces.com/api/coding/v3
- Model: doubao-seed-2.0-pro
- API Key: ark-3d0370fe-1664-4a21-b1bb-c0cb4ebcfd5b-784ba

## 数据库变更

新增表：simulation_state, daily_decisions, research_projects, platform_allocations
修改表：products增加merchant_ai字段，orders增加simulated_day字段

## API变更

新增：POST /admin/advance-day, GET /admin/simulation-state, GET /admin/leaderboard, GET /admin/decision-log, GET /admin/platform-suggestions
移除：旧模拟接口 simulation/start|stop|tick
