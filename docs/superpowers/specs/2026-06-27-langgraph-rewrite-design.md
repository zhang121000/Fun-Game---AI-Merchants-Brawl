# LangGraph 重构设计 - AI 健康生活馆

> 日期：2026-06-27
> 状态：草稿
> 方案：LangGraph 驱动的渐进式重构

## 1. 背景与目标

当前项目的核心价值在于“AI 商家竞争模拟”，但现有实现更接近“单轮 prompt + JSON 结果”的脚本式编排，容易出现以下问题：

- 决策过程短、硬，缺少经营模拟应有的连续感
- 平台流量分配、商家策略、风险判断和执行回写耦合在一起
- 异常、降级、审批、回退等行为散落在 service 内部，难以追踪
- 日志侧只能看到结果，较难解释“为什么做出这个决策”

本次重构的目标不是替换整个系统，而是把最有价值的 AI 决策链改造成一个可组合、可回放、可分支的状态图，以增强模拟的自然度和可维护性。

### 1.1 重构目标

- 让每日模拟更像经营模拟器，而不是一次性调用模型
- 将“分析、判断、执行、回写”拆成明确节点
- 保留现有 FastAPI、数据库模型和前端大结构，降低迁移风险
- 为后续加入人工审批、重试、回退、解释日志打基础

### 1.2 非目标

- 不重写前端路由和基础页面
- 不替换商品、购物车、订单等 CRUD API
- 不强制把所有 AI 场景都改成图式编排
- 不引入额外的向量库或知识库，除非后续营销/R&D 真的需要

## 2. 方案选择

### 2.1 选型结论

采用 **LangGraph** 作为核心编排层，保留现有 provider 体系和 FastAPI 接口层。

### 2.2 为什么不是 DeepAgen 全量接管

DeepAgen 这类框架更强调多 agent 协作体验，适合展示“角色之间在讨论”。但本项目的主需求不是聊天协作，而是：

- 有状态的日模拟
- 可控的业务规则
- 可解释的分支决策
- 可回退的异常处理

如果直接把主流程交给“多 agent 对话式协作”，容易得到更强的表演感，但不一定更适合经营模拟的稳定性和调试性。

### 2.3 为什么 LangGraph 更合适

LangGraph 的优势是：

- 原生适合状态机和有向图流程
- 节点之间的输入输出清晰
- 便于插入分支、循环、人工审批、降级
- 更适合“模拟引擎”这种需要逐步推进状态的系统

对本项目来说，LangGraph 的价值不在“多 agent”本身，而在“把多 agent 的能力装进一个有约束的流程里”。

## 3. 总体架构

### 3.1 架构原则

- 保留现有 API 边界，不改变前端调用方式
- 把 AI 决策收敛到单独的编排层
- 节点职责单一，输入输出结构化
- 任何 LLM 失败都必须有规则化降级路径

### 3.2 目标分层

```text
frontend/
  维持现有页面与 API 调用方式

backend/api/
  维持现有 REST 路由
  advance-day 仍然是对外入口

backend/services/
  从“单体决策服务”演进为“编排入口 + 图节点实现”

backend/ai/
  继续保留 provider_registry 和各 provider
  新增 LangGraph 相关的决策图与状态定义
```

### 3.3 建议新增模块

```text
backend/
  ai/
    graphs/
      day_simulation_graph.py
      marketing_graph.py
      rd_graph.py
    graph_state.py
    graph_nodes/
      collect_context.py
      allocate_traffic.py
      merchant_decision.py
      validate_decision.py
      execute_market_action.py
      finalize_day.py
      fallback_rules.py
  services/
    day_simulation_service.py
    marketing_service.py
```

说明：

- `services` 负责 API 入口、事务边界和持久化
- `graphs` 负责图结构和状态推进
- `graph_nodes` 负责单个节点的业务逻辑

## 4. 核心图设计

### 4.1 每日模拟图

每日推进仍然是整个系统的核心，建议成为第一个重构对象。

```text
Start
  -> CollectContext
  -> AllocateTraffic
  -> ParallelMerchantDecisions
  -> ValidateDecisions
  -> Branch
      -> ApproveAndExecute
      -> FallbackAndExecute
  -> GenerateOrders
  -> UpdateInventoryAndRanking
  -> EmitLogsAndAdvisories
  -> End
```

### 4.2 节点职责

#### 4.2.1 CollectContext

收集昨日经营数据与今日运行所需上下文：

- 各商家销量、收入、库存
- 昨日排名与变化趋势
- 历史 7 日均值
- 促销状态、产品状态、R&D 状态
- 需要给平台 AI 和商家 AI 的可见信息

#### 4.2.2 AllocateTraffic

生成当天 500 个线索的分配结果：

- 基于历史表现做正反馈
- 保留最低保底流量
- 结合类目与人群匹配度
- 失败时进入规则化分配

#### 4.2.3 ParallelMerchantDecisions

对 5 个商家并行生成经营决策：

- 定价
- 促销
- 目标人群
- 卖点文案
- 补货策略
- 是否触发 R&D

这里的重点不是让 agent “自由聊天”，而是让每个商家在统一状态输入上输出结构化策略。

#### 4.2.4 ValidateDecisions

校验所有商家决策是否可执行：

- 价格变动是否超过上限
- 库存是否足以支撑促销
- 促销是否违反规则
- R&D 是否满足触发条件

校验结果决定后续是否进入审批分支或降级分支。

#### 4.2.5 ApproveAndExecute / FallbackAndExecute

两条执行路径：

- 自动审批通过则执行高阶策略
- 失败、超时、格式错误时走规则化降级

降级不是简单报错，而是生成一个保守但可运行的决策。

#### 4.2.6 GenerateOrders

根据价格、促销、类目偏好、流量、人群匹配度和随机扰动生成订单。

#### 4.2.7 UpdateInventoryAndRanking

回写库存、销量、收入、排名、告警状态、R&D 进度。

#### 4.2.8 EmitLogsAndAdvisories

输出可回放的决策链路：

- 每个节点的输入摘要
- 工具调用记录
- 校验失败原因
- 最终执行的动作
- 平台建议与异常提示

### 4.3 状态对象

建议定义统一的 graph state，用于整个流程传递。

```python
class DaySimulationState(TypedDict):
    day: int
    merchants: list[dict]
    customers: list[dict]
    traffic_allocation: dict
    merchant_decisions: dict
    validation_results: dict
    execution_path: str
    generated_orders: list[dict]
    rankings: list[dict]
    advisories: list[dict]
    logs: list[dict]
    errors: list[dict]
```

说明：

- 状态必须可序列化，便于日志和调试
- 节点输出尽量使用结构化字典，避免纯自然语言作为系统事实来源
- 任何推理文本都应作为日志附加信息，而不是唯一业务依据

## 5. 商家决策设计

### 5.1 决策策略

每个商家保持独立 persona，但输入统一由图层提供。商家 AI 的任务不再是“生成一段看起来像经营建议的话”，而是产出固定结构的决策对象。

建议决策字段：

- `price`
- `promotion_type`
- `promotion_intensity`
- `target_segment`
- `selling_points`
- `restock_amount`
- `launch_rd`
- `confidence`
- `reasoning_summary`

### 5.2 角色感与约束并存

为了让系统更自然，应保留每个商家的风格差异：

- 不同品牌在语言风格上有差异
- 不同产品在策略偏好上有差异
- 不同历史表现会影响保守/激进倾向

但这些差异要服从统一输出格式和规则约束，避免 agent “跑偏”。

## 6. 失败处理与降级

### 6.1 失败类型

- LLM 超时
- 返回 JSON 格式错误
- 决策违反硬约束
- 节点运行异常
- 数据缺失或状态不一致

### 6.2 降级原则

任何失败都不得中断整日模拟，至少要保证：

- 流量有默认分配
- 商家有保守策略
- 订单生成流程可继续
- 排名和日志可回写

### 6.3 降级路径

建议分三层：

1. **轻微错误**：重试当前节点一次
2. **可修复错误**：用规则修正后继续
3. **不可恢复错误**：切换到保守策略并记录告警

## 7. 可观测性

重构后必须比现在更容易排查问题。

### 7.1 日志要求

每次推进日模拟时，记录：

- day 编号
- 图版本
- 每个节点的开始/结束时间
- 节点输出摘要
- 失败原因和降级策略
- 最终执行的决策对象

### 7.2 管理后台展示

后台至少应能看到：

- 今日图执行状态
- 每个商家的决策摘要
- 哪些节点走了 fallback
- 哪些决策进入了审批
- 当天产生的异常与建议

## 8. 迁移计划

### 8.1 第一阶段：只重构每日模拟

范围：

- `day_simulation_service`
- 平台流量分配
- 商家策略生成
- 订单生成
- 结果回写

目标：

- 先让 `POST /api/v1/admin/advance-day` 走 LangGraph
- 保持对外接口不变
- 保留旧实现作为回退路径

### 8.2 第二阶段：接入营销审批

把营销建议从单步逻辑改成：

- 数据分析
- 策略生成
- 风险评估
- 审批
- 执行

### 8.3 第三阶段：接入 R&D

把 R&D 改造成“提案 -> 评估 -> 等待 -> 产出 -> 上线”的多步流程。

## 9. 测试策略

### 9.1 单元测试

- 图状态转换测试
- 节点输入输出契约测试
- 校验逻辑测试
- 降级分支测试

### 9.2 集成测试

- `advance-day` 全链路测试
- LLM 正常/失败两种路径测试
- 审批分支测试
- 回退路径测试

### 9.3 回归测试

- 与当前版本对比每日销量、排名、库存变化是否稳定
- 验证空库初始化和重置逻辑不受影响
- 验证前端页面无需改动即可继续使用现有 API

## 10. 风险与控制

### 10.1 主要风险

- 图过于碎片化，反而难维护
- 状态字段膨胀，导致调试困难
- agent 输出自由度太大，破坏业务约束
- 重构过程中出现模拟结果大幅漂移

### 10.2 控制措施

- 先做最小图，再逐步增加节点
- 所有业务状态使用统一 schema
- 所有 LLM 输出必须经过校验
- 旧逻辑保留为 fallback，便于对比和回滚

## 11. 交付标准

如果本次重构完成，应满足：

- `advance-day` 仍可稳定运行
- 决策过程更连贯，日志更可解释
- 平台流量和商家策略可以分步调试
- 失败时系统能够自动降级
- 前端不需要配合大改即可继续使用

## 12. 下一步

建议进入实现规划阶段，按以下顺序推进：

1. 定义 LangGraph 的状态对象
2. 抽离每日模拟图的节点
3. 接入 `advance-day` 入口
4. 增加测试与回退路径
5. 再迁移营销和 R&D

