# 产品迭代 & 排行榜联动 — 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 研发完成后自动更新产品名/描述/价格，排行榜跟随变化，数据看板新增迭代历史时间线

**架构：** 后端在 ResearchProject 中存储新品描述/价格，研发完成时写入 ProductIteration 快照表并回写 Product 表。前端在数据看板尾部通过 GET API 拉取迭代历史，用垂直时间线展示，点击节点展开新旧对比表。

**技术栈：** FastAPI + SQLAlchemy + React + Ant Design

---

### 任务 1：ResearchProject 模型新增字段

**文件：**
- 修改：`backend/models/marketing.py`（ResearchProject 类）

- [ ] **步骤 1：添加 new_description 和 new_price 字段**

在 `ResearchProject` 类中，`product_name` 字段后新增两个字段：

```python
class ResearchProject(Base):
    __tablename__ = "research_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_ai: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(100))
    product_name: Mapped[str] = mapped_column(String(200))
    new_description: Mapped[str] = mapped_column(Text, default="")        # 新增
    new_price: Mapped[float] = mapped_column(Float, default=0.0)          # 新增
    days_total: Mapped[int] = mapped_column(Integer, default=3)
    days_remaining: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String(20), default="active")
    started_day: Mapped[int] = mapped_column(Integer)
    completed_day: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **步骤 2：验证模型定义无语法错误**

```bash
cd backend && python -c "from models.marketing import ResearchProject; print('OK')"
```

- [ ] **步骤 3：Commit**

```bash
git add backend/models/marketing.py
git commit -m "feat: ResearchProject 新增 new_description、new_price 字段"
```

---

### 任务 2：新增 ProductIteration 模型

**文件：**
- 修改：`backend/models/marketing.py`（尾部新增类）

- [ ] **步骤 1：在 marketing.py 尾部添加 ProductIteration 类**

```python
class ProductIteration(Base):
    """产品迭代快照 — 记录每次研发完成时的产品变化"""
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

- [ ] **步骤 2：在 models/__init__.py 中导出 ProductIteration**

```python
from models.marketing import (
    MarketingStrategy, SimulationState, DailyDecision,
    PlatformAllocation, ResearchProject, ProductIteration,
)

__all__ = [
    ...
    "MarketingStrategy", "PurchaseSimulationConfig", "ResearchProject",
    "DailyDecision", "PlatformAllocation", "SimulationState",
    "ProductIteration",
]
```

- [ ] **步骤 3：验证模型加载**

```bash
cd backend && python -c "from models import ProductIteration; print('OK')"
```

- [ ] **步骤 4：Commit**

```bash
git add backend/models/marketing.py backend/models/__init__.py
git commit -m "feat: 新增 ProductIteration 模型 — 产品迭代快照表"
```

---

### 任务 3：AI 决策 prompt 扩展 research_new_product

**文件：**
- 修改：`backend/services/day_simulation_service.py:307`（`_build_merchant_prompt` 中的 JSON 模板）

- [ ] **步骤 1：更新 prompt JSON 模板中的 research_new_product 说明**

将 line 307 的 `"research_new_product": null,` 替换为带注释的新格式：

```python
  "research_new_product": {{"name": "新品名称（必填，如'有机综合维生素矿物质片'）", "description": "新品描述（必填）", "price": 新品售价（必填，数字）, "days_needed": 研发所需天数（必填，1~7）}} | 不研发填 null,
```

同时更新 prompt 中第 6 点的说明文字（line 298），从：
```
6. 如果排名垫底，是否启动研发新品
```
改为：
```
6. 如果排名垫底，可以启动研发新品（需指定名称、描述、售价、所需天数）
```

- [ ] **步骤 2：验证 prompt 格式化正确**

```bash
cd backend && python -c "
from services.day_simulation_service import _build_merchant_prompt
info = {'category': '维生素', 'product_name': '测试品', 'current_price': 100, 'original_price': 120, 'stock': 50, 'yesterday_units': 10, 'yesterday_revenue': 1000, 'avg_units_7d': 15.0, 'trend': '上升', 'rank': 3}
prompt = _build_merchant_prompt(info, 100, [], 1)
assert 'new_description' in prompt or 'description' in prompt
print('OK')
"
```

- [ ] **步骤 3：Commit**

```bash
git add backend/services/day_simulation_service.py
git commit -m "feat: AI 决策 prompt 扩展 — research_new_product 新增描述和价格"
```

---

### 任务 4：研发完成时更新 Product 并写入 ProductIteration

**文件：**
- 修改：`backend/services/day_simulation_service.py:419-457`（`_process_research` 函数）
- 修改：`backend/services/day_simulation_service.py:1-15`（import 新增 ProductIteration）

- [ ] **步骤 1：更新 import**

将 line 12-14 的 import 改为：

```python
from models.marketing import (
    SimulationState, DailyDecision, PlatformAllocation,
    ResearchProject, ProductIteration,
)
```

- [ ] **步骤 2：_process_research 创建 ResearchProject 时写入新品描述和价格**

在 `db.add(ResearchProject(...))` 调用中新增两个字段（line 436-444）：

```python
if not existing:
    db.add(ResearchProject(
        merchant_ai=ai_model,
        category=decision.get("category", ""),
        product_name=name,
        new_description=research.get("description", ""),   # 新增
        new_price=research.get("price", 0.0),               # 新增
        days_total=days,
        days_remaining=days,
        status="active",
        started_day=day,
    ))
```

- [ ] **步骤 3：_process_research 推进研发完成时更新 Product 并写迭代记录**

替换 line 453-456 的 TODO：

```python
if project.days_remaining <= 0:
    project.status = "completed"
    project.completed_day = day

    # 查找该 AI 商家对应的产品
    product_result = (await db.execute(
        select(Product)
        .where(Product.ai_model == project.merchant_ai)
    )).scalars().first()

    if product_result:
        # 记录迭代快照
        db.add(ProductIteration(
            merchant_ai=project.merchant_ai,
            day=day,
            old_name=product_result.name,
            new_name=project.product_name,
            old_description=product_result.description,
            new_description=project.new_description,
            old_price=float(product_result.price),
            new_price=project.new_price,
        ))
        # 更新产品
        product_result.name = project.product_name
        product_result.description = project.new_description
        product_result.price = project.new_price
        product_result.original_price = project.new_price
```

- [ ] **步骤 4：验证语法**

```bash
cd backend && python -c "from services.day_simulation_service import _process_research; print('OK')"
```

- [ ] **步骤 5：Commit**

```bash
git add backend/services/day_simulation_service.py
git commit -m "feat: 研发完成时更新 Product 名称/描述/价格并写入 ProductIteration"
```

---

### 任务 5：重置时清理 ProductIteration

**文件：**
- 修改：`backend/api/admin.py:142-168`（`admin_reset` 函数）

- [ ] **步骤 1：在 reset 中增加 ProductIteration 清理**

在 import 行（line 10-13）添加 `ProductIteration`：

```python
from models.marketing import (
    MarketingStrategy, SimulationState, DailyDecision,
    PlatformAllocation, ResearchProject, ProductIteration,
)
```

在 reset 函数中（line 153 后）添加一行：

```python
await db.execute(delete(ProductIteration))
```

完整顺序：
```python
await db.execute(delete(OrderItem))
await db.execute(delete(Order))
await db.execute(delete(DailyDecision))
await db.execute(delete(PlatformAllocation))
await db.execute(delete(ResearchProject))
await db.execute(delete(ProductIteration))  # 新增
await db.execute(delete(SimulationState))
```

- [ ] **步骤 2：验证语法**

```bash
cd backend && python -c "from api.admin import admin_reset; print('OK')"
```

- [ ] **步骤 3：Commit**

```bash
git add backend/api/admin.py
git commit -m "fix: 重置时清理 ProductIteration 表"
```

---

### 任务 6：新增 GET /admin/product-iterations API

**文件：**
- 修改：`backend/api/admin.py`（尾部新增路由）

- [ ] **步骤 1：在 admin.py 尾部添加路由**

```python
@router.get("/admin/product-iterations")
async def product_iterations(
    merchant_ai: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """获取指定 AI 商家的产品迭代历史，按时间从近到远排列"""
    iterations = (await db.execute(
        select(ProductIteration)
        .where(ProductIteration.merchant_ai == merchant_ai)
        .order_by(ProductIteration.day.desc())
    )).scalars().all()

    return [
        {
            "id": it.id,
            "merchant_ai": it.merchant_ai,
            "day": it.day,
            "old_name": it.old_name,
            "new_name": it.new_name,
            "old_description": it.old_description,
            "new_description": it.new_description,
            "old_price": it.old_price,
            "new_price": it.new_price,
        }
        for it in iterations
    ]
```

- [ ] **步骤 2：验证路由自动注册**

```bash
cd backend && python -c "from main import app; routes = [r.path for r in app.routes]; print('OK' if '/api/v1/admin/product-iterations' in routes else 'MISSING')"
```

- [ ] **步骤 3：Commit**

```bash
git add backend/api/admin.py
git commit -m "feat: 新增 GET /admin/product-iterations API"
```

---

### 任务 7：启动前后端验证后端 API

**文件：** 无新文件

- [ ] **步骤 1：重启后端服务**

```bash
# 使用 preview_start 重启 backend
```

确认后端无报错启动。

- [ ] **步骤 2：手动测试 API**

```bash
# 暂无数据时查询
curl "http://localhost:8000/api/v1/admin/product-iterations?merchant_ai=gpt"
# 预期：[]
```

---

### 任务 8：前端数据看板尾部新增「产品迭代历史」

**文件：**
- 修改：`frontend/src/pages/AnalyticsBoard.tsx`

- [ ] **步骤 1：添加接口类型和状态**

在文件开头现有类型定义和组件之间，添加：

```typescript
interface Iteration {
  id: number
  merchant_ai: string
  day: number
  old_name: string
  new_name: string
  old_description: string
  new_description: string
  old_price: number
  new_price: number
}
```

在组件 `AnalyticsBoard` 内的状态区（现有 useState 之后）添加：

```typescript
const [iterations, setIterations] = useState<Iteration[]>([])
const [iterMerchant, setIterMerchant] = useState<string>('gpt')
const [expandedIter, setExpandedIter] = useState<number | null>(null)
const [iterLoading, setIterLoading] = useState(false)
```

- [ ] **步骤 2：添加加载迭代数据的 useEffect**

```typescript
useEffect(() => {
  loadIterations()
}, [iterMerchant])

async function loadIterations() {
  setIterLoading(true)
  try {
    const res = await client.get(`/admin/product-iterations?merchant_ai=${iterMerchant}`)
    setIterations(res.data)
  } catch { setIterations([]) }
  setIterLoading(false)
}
```

- [ ] **步骤 3：在页面尾部（产品明细表下方）添加迭代历史区域 JSX**

```tsx
{/* 产品迭代历史 */}
<div style={{
  background: '#ffffff', border: '1px solid #e0e0e0',
  borderRadius: 18, padding: 32, marginTop: 32,
}}>
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
    <h2 style={{ fontSize: 21, fontWeight: 600, margin: 0 }}>产品迭代历史</h2>
    <Select
      value={iterMerchant}
      onChange={setIterMerchant}
      style={{ width: 160 }}
      popupMatchSelectWidth={false}
    >
      {Object.entries(AI_LABELS).map(([key, label]) => (
        <Option key={key} value={key}>{label}</Option>
      ))}
    </Select>
  </div>

  {iterations.length === 0 ? (
    <div style={{ textAlign: 'center', padding: 40, color: '#7a7a7a', fontSize: 14 }}>
      暂无产品迭代记录
    </div>
  ) : (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {iterations.map((it, idx) => {
        const isLatest = idx === 0
        const color = AI_COLORS[it.merchant_ai] || '#0066cc'
        const isExpanded = expandedIter === it.id

        return (
          <div key={it.id} style={{ display: 'flex', gap: 0 }}>
            {/* 时间线竖轴 */}
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              width: 32, flexShrink: 0,
            }}>
              <div style={{
                width: isLatest ? 14 : 10, height: isLatest ? 14 : 10,
                borderRadius: '50%',
                background: isLatest ? color : '#d0d0d0',
                border: isLatest ? `3px solid ${color}33` : '2px solid #e0e0e0',
                flexShrink: 0, marginTop: 8,
              }} />
              <div style={{ width: 2, flex: 1, background: idx < iterations.length - 1 ? '#e8e8e8' : 'transparent', minHeight: 20 }} />
            </div>

            {/* 内容区 */}
            <div
              style={{
                flex: 1, padding: '10px 0 10px 12px',
                cursor: 'pointer',
              }}
              onClick={() => setExpandedIter(isExpanded ? null : it.id)}
            >
              <div style={{ fontSize: 13, color: '#7a7a7a', marginBottom: 2 }}>
                第 {it.day} 天
              </div>
              <div style={{ fontSize: 15, color: '#1d1d1f', lineHeight: 1.4 }}>
                <span style={{ textDecoration: 'line-through', color: '#7a7a7a' }}>{it.old_name}</span>
                {' → '}
                <span style={{ fontWeight: 600, color }}>{it.new_name}</span>
              </div>

              {/* 展开的对比表 */}
              {isExpanded && (
                <div style={{
                  marginTop: 12, background: '#f9f9fb',
                  borderRadius: 10, padding: 16,
                  border: '1px solid #eee',
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #e0e0e0' }}>
                        <th style={{ textAlign: 'left', padding: '6px 8px', color: '#7a7a7a', fontWeight: 400, fontSize: 12 }}>字段</th>
                        <th style={{ textAlign: 'left', padding: '6px 8px', color: '#7a7a7a', fontWeight: 400, fontSize: 12 }}>旧值</th>
                        <th style={{ textAlign: 'left', padding: '6px 8px', color: color, fontWeight: 400, fontSize: 12 }}>新值</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={{ padding: '8px', color: '#7a7a7a', fontSize: 12 }}>产品名</td>
                        <td style={{ padding: '8px', color: '#7a7a7a' }}>{it.old_name}</td>
                        <td style={{ padding: '8px', color, fontWeight: 500 }}>{it.new_name}</td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={{ padding: '8px', color: '#7a7a7a', fontSize: 12 }}>描述</td>
                        <td style={{ padding: '8px', color: '#7a7a7a' }}>{it.old_description}</td>
                        <td style={{ padding: '8px', color, fontWeight: 500 }}>{it.new_description}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: '8px', color: '#7a7a7a', fontSize: 12 }}>价格</td>
                        <td style={{ padding: '8px', color: '#7a7a7a' }}>¥{it.old_price}</td>
                        <td style={{ padding: '8px', color, fontWeight: 500 }}>¥{it.new_price}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )}
</div>
```

- [ ] **步骤 4：验证编译无错误**

```bash
# 检查前端编译
```

- [ ] **步骤 5：Commit**

```bash
git add frontend/src/pages/AnalyticsBoard.tsx
git commit -m "feat: 数据看板尾部新增产品迭代历史时间线"
```

---

## 任务顺序

```
任务1 (模型+字段) → 任务2 (模型) → 任务3 (prompt) → 任务4 (核心逻辑) → 任务5 (重置) → 任务6 (API) → 任务7 (验证后端) → 任务8 (前端)
```

所有后端任务（1-6）需按序执行。任务 7-8 在前后端都启动后验证。
