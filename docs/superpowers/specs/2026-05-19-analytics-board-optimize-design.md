# 数据看板优化 — 销售趋势去重 & 人群分布品类切换

**日期**: 2026-05-19  
**范围**: `AnalyticsBoard.tsx` + `analytics.py`（微调）

## 背景

当前数据看板（AnalyticsBoard）存在两个问题：

1. **销售趋势 "按 AI" 和 "按品类" 重复** — 5 个 AI 商家各自绑定唯一品类（GLM=蛋白粉、GPT=维生素、MiniMax=钙片、Kimi=益生菌、通义千问=鱼油），两个维度数据完全一致，仅是图例标签不同。
2. **购买人群分布无法按品类筛选** — 当前仅展示全局饼图，无法看到单个品类的购买人群分布。

## 设计

### 1. 销售趋势 — 合并 "按 AI" 与 "按品类"

**改动**：3 个 Tab → 2 个 Tab

| 原来 | 改为 |
|------|------|
| 按 AI 商家 | **按商家**（图例显示 "GLM · 蛋白粉" 格式） |
| 按品类 | ~~删除~~ |
| 按人群 | 按人群（不变） |

**前端策略**：dimension 保留用 `ai` 请求数据，图例标签在 `AI_LABELS` 基础上追加品类名（从 `products` 数组获取 `ai_model → category` 映射）。

**后端**：无需改动。

### 2. 购买人群分布 — 下拉选择器按品类切换

**改动**：卡片标题区右侧新增一个 `Select` 下拉框

- 默认选中 "全部品类"
- 选项列表：全部品类 + 5 个品类（蛋白粉、维生素、钙片、益生菌、鱼油）
- 选中 "全部品类" → 请求 `/analytics/demographic-dist`（现有接口）
- 选中具体品类 → 请求 `/analytics/product/{product_id}/demographic-breakdown`（现有接口，已实现）

**交互细节**：
- 切换时图表做平滑过渡（ECharts 的 `notMerge: false` + 动画）
- 下拉框样式与页面 Apple 风格一致（minimal border, rounded）
- 饼图颜色保持现有 DEMO_COLORS（老年=橙、青年=蓝、中年=紫、儿童=绿）

### 数据流

```
品类下拉 onChange
  ├─ "全部" → GET /analytics/demographic-dist → 全局饼图
  └─ 具体品类 → 查找 product_id → GET /analytics/product/{id}/demographic-breakdown → 品类饼图
```

品类到 product_id 的映射从已加载的 `products` (product-compare) 数组中获取。

### 涉及文件

| 文件 | 改动 |
|------|------|
| `frontend/src/pages/AnalyticsBoard.tsx` | 趋势 Tab 精简；人群分布加品类下拉 + 联动请求 |
| `backend/api/analytics.py` | 无需改动（接口已就绪） |

### 不做什么

- 不新增后端接口
- 不改动产品明细表、KPI 卡片、产品对比柱状图
- 不在其他页面做联动修改
