# 顾客池与流量池扩展设计

**日期：** 2026-05-19
**状态：** 已批准

## 目标

将模拟系统的用户基数从 5000 扩展到 10 万，每日流量池从 500 扩展到 5000，并优化订单生成中的伯努利循环。

## 背景

当前系统配置 `total_users=5000`、`DEFAULT_TRAFFIC_POOL=500`。平台 AI 把 500 次访问分给 5 个商家 × 4 个人群 = 20 个分配槽位，平均每槽位仅 25 次访问，转化率波动较大。扩展后可模拟更贴近真实电商的竞争场景。

## 配置变更

### 1. 用户生成配置 (`backend/data/user_generation_config.json`)

| 字段 | 旧值 | 新值 |
|------|------|------|
| `total_users` | 5000 | 100000 |

各人群 `count` 按 DEMOGRAPHIC_RATIO 比例扩展：

| 人群 | 旧 count | 新 count | 占比 |
|------|---------|----------|------|
| child | 900 | 18,000 | 18% |
| youth | 1,500 | 30,000 | 30% |
| middle | 1,750 | 35,000 | 35% |
| elderly | 850 | 17,000 | 17% |

合计 100,000 = 18 明星用户 + 99,982 统计生成用户。其余配置（`purchase_weight`、`preferences`、`age_range`）不变。

### 2. 流量池 (`backend/config.py`)

```python
DEFAULT_TRAFFIC_POOL: int = 500 → 5000
```

### 3. 平台 AI 提示词 (`backend/services/platform_ai_service.py`)

`build_allocation_prompt` 函数 `total_pool` 默认值 `500 → 5000`。

## 代码变更

### 4. 种子数据生成 (`backend/services/seed_service.py`)

**插入方式**：逐条 `db.add()` 改为 `db.execute(sql_insert(Customer), list_of_dicts)` 批量插入。

**_generate_statistical_users 函数**：提取 `age_options` 和 `pref_items` 到循环外，减少重复查找。内联 `is_star=False` 到 dict 构造中。

预期生成耗时：~1.5 秒（10 万条高斯抽样），批量 INSERT ~0.5 秒，合计约 2 秒。

### 5. 订单生成 (`backend/services/day_simulation_service.py`)

将伯努利循环：

```python
actual_buyers = 0
for _ in range(traffic):
    if random.random() < conversion:
        actual_buyers += 1
```

替换为二项分布抽样：

```python
actual_buyers = random.binomialvariate(traffic, conversion)
```

`binomialvariate(n, p)` — Python 3.12+ 标准库函数，返回 n 重伯努利试验的成功次数，与循环统计学等价，O(1) 时间复杂度。

## 变更文件清单

| 文件 | 改动 |
|------|------|
| `backend/data/user_generation_config.json` | 用户基数 5000→100000 |
| `backend/services/seed_service.py` | 批量插入 + 生成优化 |
| `backend/config.py` | DEFAULT_TRAFFIC_POOL 500→5000 |
| `backend/services/platform_ai_service.py` | total_pool 默认值 500→5000 |
| `backend/services/day_simulation_service.py` | binomialvariate 替换循环 |

## 影响评估

| 指标 | 扩展前 | 扩展后 | 风险 |
|------|--------|--------|------|
| 数据库文件大小 | ~2MB | ~15MB | 低 |
| 每日订单数 | ~75 | ~750 | 低 |
| 模拟耗时 | ~10s | ~10s | 无变化 |
| _generate_orders 耗时 | <10ms | <10ms | 无变化 |
| 内存占用 | ~1MB | ~20MB | 低 |
| 全量顾客查询 | ~50ms | ~200ms | 低 |

## 不在范围内

- 前端无任何改动需求
- 不引入 NumPy 或其他新依赖
- 不修改转化率计算逻辑
