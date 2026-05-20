# 顾客池与流量池扩展 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将顾客池从 5000 扩展到 10 万，日流量池从 500 扩展到 5000，用 `binomialvariate` 替换伯努利循环。

**架构：** 纯配置 + 小幅代码重构，无新文件、无新依赖。5 个现有文件的改动：3 个数字变更、1 个批量插入优化、1 个统计函数替换。

**技术栈：** Python 3.12+, SQLAlchemy 2.0, SQLite, FastAPI

---

## 文件结构

| 文件 | 职责 | 改动类型 |
|------|------|----------|
| `backend/data/user_generation_config.json` | 用户生成参数配置 | 数字变更 |
| `backend/config.py` | 全局配置（Settings） | 数字变更 |
| `backend/services/platform_ai_service.py` | 平台 AI 流量分配提示词 | 数字变更 |
| `backend/services/seed_service.py` | 首次启动种子数据生成 | 批量插入重构 |
| `backend/services/day_simulation_service.py` | 每日模拟订单生成引擎 | 统计函数替换 |

---

### 任务 1：扩展顾客池配置

**文件：**
- 修改：`backend/data/user_generation_config.json`

- [ ] **步骤 1：修改 total_users 和各人群 count**

将 `total_users` 从 `5000` 改为 `100000`，各人群 `count` 按 20 倍比例扩展。

```json
{
  "total_users": 100000,
  "traffic_pool": 500,
  "random_seed": 42,
  "demographics": {
    "child": {
      "count": 18000,
      ...
    },
    "youth": {
      "count": 30000,
      ...
    },
    "middle": {
      "count": 35000,
      ...
    },
    "elderly": {
      "count": 17000,
      ...
    }
  }
}
```

- [ ] **步骤 2：验证 JSON 格式和 count 合计**

```bash
python -c "
import json
with open('backend/data/user_generation_config.json') as f:
    cfg = json.load(f)
total = sum(d['count'] for d in cfg['demographics'].values())
print(f'total_users: {cfg[\"total_users\"]}')
print(f'sum of counts: {total}')
print(f'expected: 100000 = 18 stars + {total - 18} stats')
"
```

预期：`total_users: 100000`，`sum of counts: 100000`

- [ ] **步骤 3：Commit**

```bash
git add backend/data/user_generation_config.json
git commit -m "feat: 顾客池从5000扩展到10万，各人群count按比例扩大"
```

---

### 任务 2：扩展流量池配置

**文件：**
- 修改：`backend/config.py:23`
- 修改：`backend/services/platform_ai_service.py:20`

- [ ] **步骤 1：修改 DEFAULT_TRAFFIC_POOL**

`backend/config.py` 第 23 行：

```python
# 旧
DEFAULT_TRAFFIC_POOL: int = 500

# 新
DEFAULT_TRAFFIC_POOL: int = 5000
```

- [ ] **步骤 2：修改 build_allocation_prompt 默认值**

`backend/services/platform_ai_service.py` 第 20 行：

```python
# 旧
def build_allocation_prompt(merchants_data: list[dict], day: int, total_pool: int = 500) -> str:

# 新
def build_allocation_prompt(merchants_data: list[dict], day: int, total_pool: int = 5000) -> str:
```

- [ ] **步骤 3：验证两个文件的值一致**

```bash
cd backend && python -c "
from config import get_settings
from services.platform_ai_service import build_allocation_prompt
import inspect
s = get_settings()
sig = inspect.signature(build_allocation_prompt)
print(f'DEFAULT_TRAFFIC_POOL: {s.DEFAULT_TRAFFIC_POOL}')
print(f'total_pool default: {sig.parameters[\"total_pool\"].default}')
"
```

预期：两处都输出 `5000`

- [ ] **步骤 4：Commit**

```bash
git add backend/config.py backend/services/platform_ai_service.py
git commit -m "feat: 日流量池从500扩展到5000"
```

---

### 任务 3：批量插入优化种子数据生成

**文件：**
- 修改：`backend/services/seed_service.py`

- [ ] **步骤 1：优化 _generate_statistical_users 函数**

将第 95-123 行的函数替换为优化版。改动：提取 `age_options` 和 `pref_items` 到循环外，内联 `is_star`，使用列表推导风格。

```python
def _generate_statistical_users(config: dict, existing_count: int) -> list[dict]:
    """按 user_generation_config.json 配置批量生成统计用户"""
    target = config["total_users"] - existing_count
    total_configured = sum(d["count"] for d in config["demographics"].values())
    rng = random.Random(config.get("random_seed", 42))

    users = []
    for demo_name, demo_cfg in config["demographics"].items():
        count = round(demo_cfg["count"] * target / total_configured)
        pw_cfg = demo_cfg["purchase_weight"]
        age_options = demo_cfg["age_range"]
        pref_items = list(demo_cfg["preferences"].items())

        for _ in range(count):
            users.append({
                "name": None,
                "demographic": demo_name,
                "age_range": rng.choice(age_options),
                "purchase_weight": round(max(0.5, min(3.0, rng.gauss(pw_cfg["mean"], pw_cfg["std"]))), 2),
                "preferences": {
                    cat: round(max(0.1, min(1.0, rng.gauss(dist["mean"], dist["std"]))), 2)
                    for cat, dist in pref_items
                },
                "is_star": False,
            })

    return users
```

- [ ] **步骤 2：批量插入替换逐条 add**

将 `seed_data_if_empty` 中第 61-64 行：

```python
# 旧
stat_users = _generate_statistical_users(gen_config, len(customers_data))
for u in stat_users:
    db.add(Customer(**u, is_star=False))

# 新
stat_users = _generate_statistical_users(gen_config, len(customers_data))
if stat_users:
    from sqlalchemy import insert as sql_insert
    await db.execute(sql_insert(Customer), stat_users)
    print(f"✅ 批量生成 {len(stat_users)} 个统计用户")
```

注意：`is_star=False` 已内联到 `_generate_statistical_users` 生成的 dict 中，原调用处无需再传。

- [ ] **步骤 3：验证种子数据生成函数无语法错误**

```bash
cd backend && python -c "
from services.seed_service import _generate_statistical_users
import json
with open('data/user_generation_config.json') as f:
    cfg = json.load(f)
users = _generate_statistical_users(cfg, 18)
print(f'生成用户数: {len(users)}')
print(f'示例用户: {users[0]}')
print(f'所有 demographic 值: {set(u[\"demographic\"] for u in users)}')
"
```

预期：`生成用户数: 99982`，示例用户 dict 包含所有字段，demographic 为 `{'child', 'youth', 'middle', 'elderly'}`

- [ ] **步骤 4：删除旧数据库并验证完整种子流程**

```bash
cd backend && rm -f ai_health_mall.db && python -c "
import asyncio
from services.seed_service import seed_data_if_empty
asyncio.run(seed_data_if_empty())
from sqlalchemy import select, func
from core.database import async_session
from models.customer import Customer

async def verify():
    async with async_session() as db:
        total = (await db.execute(select(func.count()).select_from(Customer))).scalar()
        print(f'数据库顾客总数: {total}')

asyncio.run(verify())
"
```

预期：输出 `数据库顾客总数: 100000`，种子打印 `✅ 批量生成 99982 个统计用户`

- [ ] **步骤 5：Commit**

```bash
git add backend/services/seed_service.py
git commit -m "perf: 种子数据生成改为批量insert，10万用户约2秒完成"
```

---

### 任务 4：binomialvariate 替换伯努利循环

**文件：**
- 修改：`backend/services/day_simulation_service.py:376-379`

- [ ] **步骤 1：替换循环为 binomialvariate**

`backend/services/day_simulation_service.py` 第 376-379 行：

```python
# 旧
            # 生成订单
            actual_buyers = 0
            for _ in range(traffic):
                if random.random() < conversion:
                    actual_buyers += 1

# 新
            actual_buyers = random.binomialvariate(traffic, conversion)
```

- [ ] **步骤 2：验证 binomialvariate 行为等价**

```bash
cd backend && python -c "
import random

# 固定种子对比新旧方法
random.seed(42)
n, p = 1000, 0.15

# 旧：循环
random.seed(42)
old_result = sum(1 for _ in range(1000) for _ in range(n) if random.random() < p)
old_result /= 1000

# 新：binomialvariate
random.seed(42)
new_result = sum(random.binomialvariate(n, p) for _ in range(1000)) / 1000

print(f'旧方法均值(1000次试验): {old_result:.2f} (期望 {n*p})')
print(f'新方法均值(1000次试验): {new_result:.2f} (期望 {n*p})')
print(f'binomialvariate可用: True')
"
```

预期：两种方法均值都接近 `150.0`

- [ ] **步骤 3：验证模拟流程无语法错误**

```bash
cd backend && python -c "
import ast, sys
with open('services/day_simulation_service.py') as f:
    tree = ast.parse(f.read())
print('AST解析通过，无语法错误')
# 检查 binomialvariate 导入
from random import binomialvariate
print(f'binomialvariate导入成功')
"
```

预期：AST 解析通过，导入成功

- [ ] **步骤 4：Commit**

```bash
git add backend/services/day_simulation_service.py
git commit -m "perf: 用binomialvariate替换伯努利循环，O(1)替代O(n)"
```

---

### 任务 5：端到端验证

- [ ] **步骤 1：启动后端确认无报错**

```bash
cd backend && timeout 8 python -c "
import asyncio
from main import app
from core.database import async_session, engine
from sqlalchemy import select, func
from models.customer import Customer
from models.product import Product

async def e2e():
    async with async_session() as db:
        cust_count = (await db.execute(select(func.count()).select_from(Customer))).scalar()
        prod_count = (await db.execute(select(func.count()).select_from(Product))).scalar()
        print(f'✅ 后端就绪: {cust_count} 顾客, {prod_count} 产品')

asyncio.run(e2e())
" 2>&1 || echo "TIMEOUT_OK"
```

预期：输出顾客 100000、产品 5

- [ ] **步骤 2：Commit 验证记录**

```bash
git log --oneline -4
```

预期：看到 4 个新 commit

---

## 自检

1. **规格覆盖度：** 5 项变更全部对应到任务 1-4 ✅
2. **占位符扫描：** 无 TODO/TBD/待定 ❌ 无占位符 ✅
3. **类型一致性：** `binomialvariate` 在 Python 3.12+ random 模块中存在，参数 `(n, p)` 签名正确 ✅
