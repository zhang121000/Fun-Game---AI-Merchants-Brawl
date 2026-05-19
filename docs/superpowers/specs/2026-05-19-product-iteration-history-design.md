# 产品迭代 & 排行榜联动 — 设计规格

日期：2026-05-19

## 1. 需求概述

AI 商家在每日决策中可申请研发新产品。研发完成后，产品名称、描述、价格自动更新，排行榜跟随变化。数据看板尾部新增「产品迭代历史」区域，可查看每次迭代的变化对比。

## 2. 后端变更

### 2.1 模型变更

#### ResearchProject 新增字段

```python
new_description: Mapped[str] = mapped_column(Text, default="")
new_price: Mapped[float] = mapped_column(Float, default=0.0)
```

#### 新增 ProductIteration 表

```python
class ProductIteration(Base):
    __tablename__ = "product_iterations"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_ai: Mapped[str] = mapped_column(String(50))
    day: Mapped[int] = mapped_column(Integer)
    old_name: Mapped[str] = mapped_column(String(200))
    new_name: Mapped[str] = mapped_column(String(200))
    old_description: Mapped[str] = mapped_column(Text, default="")
    new_description: Mapped[str] = mapped_column(Text, default="")
    old_price: Mapped[float] = mapped_column(Float)
    new_price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### 2.2 AI 决策扩展

`research_new_product` 字段从单一名称为主，扩展为：

```json
{
  "research_new_product": {
    "name": "有机综合维生素矿物质片",
    "description": "含18种有机维生素...",
    "price": 198.00,
    "days_needed": 3
  }
}
```

### 2.3 _process_research 研发完成逻辑

```python
if project.days_remaining <= 0:
    project.status = "completed"
    product = get_product_by_ai(db, project.merchant_ai)
    # 记录迭代历史
    db.add(ProductIteration(
        merchant_ai=project.merchant_ai,
        day=day,
        old_name=product.name,
        new_name=project.product_name,
        old_description=product.description,
        new_description=project.new_description,
        old_price=product.price,
        new_price=project.new_price,
    ))
    # 更新产品
    product.name = project.product_name
    product.description = project.new_description
    product.price = project.new_price
    product.original_price = project.new_price
```

### 2.4 新 API

**GET /api/v1/admin/product-iterations?merchant_ai={key}**

返回指定 AI 商家的迭代历史列表，按 day 降序排列：

```json
[
  {
    "id": 1,
    "merchant_ai": "gpt",
    "day": 8,
    "old_name": "综合维生素矿物质片",
    "new_name": "有机综合维生素矿物质片",
    "old_description": "...",
    "new_description": "...",
    "old_price": 168,
    "new_price": 198
  }
]
```

### 2.5 重置保护

`POST /admin/reset` 使用种子数据完全重建数据库，天然保证所有产品和迭代记录回到初始状态，无需额外处理。

## 3. 前端变更

### 3.1 数据看板尾部新增「产品迭代历史」区域

#### 布局

- 标题：「产品迭代历史」
- 下拉选择器：按 AI 商家筛选（GLM / GPT / MiniMax / Kimi / 通义千问）
- 时间线：垂直时间线，从上到下由近到远
  - 每个节点显示：日期圆点 → 迭代信息（第 N 天 — 旧名 → 新名）
  - 最新节点高亮（实心圆点 + 品牌色）
- 点击节点：展开变化对比表，显示新旧名称、描述、价格的并排对比

#### 变化对比表（点击展开）

| 字段 | 旧值 | 新值 |
|------|------|------|
| 产品名 | xxx | yyy |
| 描述 | xxx | yyy |
| 价格 | ¥xxx | ¥yyy |

#### 交互行为

- 默认展示当前选中 AI 商家全部迭代记录
- 选中不同时间线节点，展开对应节点的变化对比
- 无迭代记录时展示空状态：「暂无产品迭代记录」
- 时间线从上到下按时间由近到远排列

### 3.2 现有页面跟随更新

- 排行榜产品名：自动跟随 `products.name` 更新，无需改动
- 产品详情页：名称、描述、价格自动跟随，无需改动
- 决策日志中「🔬 正在研发」：保持不变

## 4. 数据流

```
AI 每日决策 (research_new_product)
  → 创建/推进 ResearchProject
  → 研发完成时:
    → 写入 ProductIteration（快照）
    → 更新 Product 的 name/description/price
    → 排行榜下次查询自动显示新名称
```

## 5. 技术范围

| 做 | 不做 |
|----|------|
| ResearchProject 扩展描述/价格字段 | 多产品线（一个 AI 多个产品） |
| ProductIteration 模型 + API | 产品研发中途取消/暂停 |
| _process_research 完成时更新 Product | |
| 数据看板尾部迭代历史区域 | |
| 迭代对比表 | |
