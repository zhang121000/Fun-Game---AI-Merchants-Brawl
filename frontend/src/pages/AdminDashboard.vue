<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import {
  ReloadOutlined, RocketOutlined,
  TrophyOutlined, BulbOutlined, WarningOutlined,
  CheckOutlined, CloseOutlined, ExperimentOutlined,
  ArrowUpOutlined, ArrowDownOutlined, MinusOutlined,
  ShoppingCartOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import client from '../api/client'

// ============ 类型定义 ============
interface Overview {
  total_orders: number; total_revenue: number; total_customers: number;
  total_merchants: number; total_products: number;
  current_day: number; pending_strategies: number
}

interface RankingItem {
  merchant_ai: string; category: string; product_name: string;
  rank: number; units_sold: number; revenue: number; price: number;
  promotion: string; target_focus: string; reasoning: string;
  traffic_received: number;
  history: { rank: number; units: number }[]
}

interface Suggestion {
  merchant_ai: string; category: string; type: string;
  message: string; advice: string
}

interface Strategy {
  id: number; merchant_id: number; strategy_type: string; title: string;
  description: string; proposed_changes: Record<string, any>;
  status: string; ai_reasoning: string; admin_comment: string; created_at: string | null
}

interface DecisionLogItem {
  merchant_ai: string; category: string; product_name: string;
  price: number; promotion: string; target_focus: string;
  description_update: string; reasoning: string;
  traffic_received: number; units_sold: number; revenue: number;
  rank: number; research_product: string
}

// ============ 常量 ============
const AI_COLORS: Record<string, string> = {
  GLM: '#6366f1', gpt: '#10b981', MiniMax: '#f59e0b',
  Kimi: '#ef4444', qwen: '#3b82f6',
}

const AI_LABELS: Record<string, string> = {
  GLM: 'GLM', gpt: 'GPT', MiniMax: 'MiniMax', Kimi: 'Kimi', qwen: '通义千问',
}

const DEMO_LABELS: Record<string, string> = {
  child: '儿童', youth: '青年', middle: '中年', elderly: '老年',
}

const TYPE_LABELS: Record<string, string> = {
  price_adjustment: '调价', promotion: '促销活动',
  bundle: '捆绑销售', recommendation_update: '推荐更新',
}

const AI_LIST = ['GLM', 'gpt', 'MiniMax', 'Kimi', 'qwen']

// ============ 状态 ============
const overview = ref<Overview | null>(null)
const rankings = ref<RankingItem[]>([])
const suggestions = ref<Suggestion[]>([])
const strategies = ref<Strategy[]>([])
const decisionLog = ref<DecisionLogItem[]>([])
const loading = ref(true)
const advancing = ref(false)
const commentModal = ref<{ id: number; action: 'approve' | 'reject' } | null>(null)
const comment = ref('')
const submitting = ref(false)
const showDecisionLog = ref(false)
const applePhase = ref<'idle' | 'rolling' | 'sprint' | 'done'>('idle')
const aiCompleted = ref<string[]>([])
const restockDrawer = ref(false)
const productList = ref<any[]>([])
const restockAmounts = ref<Record<string, number>>({})

const currentDay = computed(() => overview.value?.current_day || 0)
const pendingStrategies = computed(() => strategies.value.filter(s => s.status === 'pending'))

// ============ 方法 ============
onMounted(() => { loadAll() })
const confirm = window.confirm.bind(window)

async function loadAll() {
  loading.value = true
  try {
    const [ovRes, lbRes, sugRes, stRes] = await Promise.all([
      client.get('/admin/overview'),
      client.get('/admin/leaderboard'),
      client.get('/admin/platform-suggestions'),
      client.get('/marketing/strategies'),
    ])
    overview.value = ovRes.data
    rankings.value = lbRes.data.rankings || []
    suggestions.value = sugRes.data.suggestions || []
    strategies.value = stRes.data
  } catch (e) {
    console.error('加载失败', e)
  }
  loading.value = false
}

async function handleAdvanceDay() {
  advancing.value = true
  applePhase.value = 'rolling'
  aiCompleted.value = []
  try {
    const startRes = await client.post('/admin/advance-day')
    if (startRes.data.status === 'running') {
      message.info(startRes.data.message)
      advancing.value = false
      return
    }

    let attempts = 0
    const maxAttempts = 120

    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1500))
      attempts++

      const statusRes = await client.get('/admin/advance-day-status')
      const status = statusRes.data

      const completed = status.ai_completed || []
      aiCompleted.value = completed

      if (!status.running && status.result) {
        applePhase.value = 'sprint'
        aiCompleted.value = [...AI_LIST]
        await new Promise(resolve => setTimeout(resolve, 500))
        applePhase.value = 'done'
        const data = status.result
        message.success(`第${data.day}天完成！${data.total_orders}笔订单，¥${data.total_revenue.toFixed(0)}收入`)
        loadAll()
        setTimeout(() => { applePhase.value = 'idle'; aiCompleted.value = [] }, 800)
        break
      }
      if (!status.running && status.error) {
        applePhase.value = 'idle'
        message.error(`模拟失败: ${status.error}`)
        break
      }
    }
    if (attempts >= maxAttempts) {
      applePhase.value = 'idle'
      message.warning('模拟超时')
    }
  } catch (e: any) {
    applePhase.value = 'idle'
    message.error(e.response?.data?.detail || '推进失败')
  }
  advancing.value = false
}

async function openRestockDrawer() {
  try {
    const res = await client.get('/products')
    productList.value = res.data
    restockDrawer.value = true
  } catch { message.error('加载产品失败') }
}

async function doRestockAll() {
  for (const p of productList.value) {
    const amount = restockAmounts.value[p.ai_model] || 100
    if (amount > 0) {
      try { await client.post(`/admin/products/${p.id}/restock`, { amount }) } catch {}
    }
  }
  message.success('全部进货成功！')
  restockDrawer.value = false
  loadAll()
}

async function doRestock(productId: number, aiModel: string) {
  const amount = restockAmounts.value[aiModel] || 100
  if (amount < 1) return
  try {
    await client.post(`/admin/products/${productId}/restock`, { amount })
    message.success(`${AI_LABELS[aiModel] || aiModel} +${amount}`)
    restockAmounts.value = { ...restockAmounts.value, [aiModel]: 100 }
    loadAll()
  } catch { message.error('进货失败') }
}

async function handleAction() {
  if (!commentModal.value) return
  submitting.value = true
  try {
    const endpoint = commentModal.value.action === 'approve'
      ? `/marketing/strategies/${commentModal.value.id}/approve`
      : `/marketing/strategies/${commentModal.value.id}/reject`
    await client.post(endpoint, { comment: comment.value })
    message.success(commentModal.value.action === 'approve' ? '已批准' : '已驳回')
    commentModal.value = null; comment.value = ''; loadAll()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  }
  submitting.value = false
}

async function loadDecisionLog() {
  try {
    const res = await client.get('/admin/decision-log')
    decisionLog.value = res.data.decisions || []
    showDecisionLog.value = true
  } catch {
    message.error('加载决策日志失败')
  }
}

function getTrendIcon(r: RankingItem) {
  if (r.history.length < 2) return null
  const prev = r.history[r.history.length - 1].rank
  const prevPrev = r.history[r.history.length - 2].rank
  if (prev < prevPrev) return 'up'
  if (prev > prevPrev) return 'down'
  return 'same'
}

// 苹果位置计算
const appleLeft = computed(() => {
  if (applePhase.value === 'idle') return '3px'
  if (applePhase.value === 'done') return 'calc(100% - 26px)'
  return `calc(${Math.max(4, aiCompleted.value.length / 5 * 100)}% - 12px)`
})

const grassWidth = computed(() => {
  if (applePhase.value === 'idle') return '0%'
  if (applePhase.value === 'done') return '100%'
  return `${Math.max(4, aiCompleted.value.length / 5 * 100)}%`
})
</script>

<template>
  <div style="max-width: 1100px; margin: 0 auto; padding: 48px 24px">
    <a-spin v-if="loading" size="large" style="display: block; text-align: center; padding: 200px" />

    <template v-else>
      <!-- ===== 标题区 + 日期推进 ===== -->
      <div style="text-align: center; margin-bottom: 48px">
        <h1 style="font-size: 40px; font-weight: 600; color: #1d1d1f; margin-bottom: 8px">
          AI 竞争控制台
        </h1>
        <p style="font-size: 21px; color: #7a7a7a; margin-bottom: 24px">
          5个AI商家 · 4类人群 · 实时竞争
        </p>

        <!-- 日期显示 + 推进按钮 -->
        <div
          :style="{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '16px',
            background: '#f5f5f7',
            borderRadius: '18px',
            padding: '16px 32px',
          }"
        >
          <div style="text-align: left">
            <div style="font-size: 12px; color: #7a7a7a">模拟天数</div>
            <div style="font-size: 36px; font-weight: 700; color: #1d1d1f; line-height: 1">
              第 {{ currentDay }} 天
            </div>
          </div>
          <div style="width: 1px; height: 48px; background: #e0e0e0" />
          <a-button
            type="primary"
            :loading="advancing"
            @click="handleAdvanceDay"
            style="height: 52px; border-radius: 9999px; padding: 0 28px; font-size: 18px; font-weight: 600"
          >
            <RocketOutlined /> {{ advancing ? 'AI 正在竞争...' : '推进明天 →' }}
          </a-button>
        </div>

        <!-- 苹果吃豆进度条 -->
        <div style="width: 320px; margin: 18px auto 0">
          <div
            :style="{
              height: '24px',
              background: '#e8e8e8',
              borderRadius: '9999px',
              position: 'relative',
              overflow: 'hidden',
              border: '1px solid #ddd',
            }"
          >
            <!-- 草坪 -->
            <div
              v-if="applePhase !== 'idle'"
              :style="{
                position: 'absolute',
                left: 0,
                top: 0,
                height: '100%',
                width: grassWidth,
                background: `
                  repeating-linear-gradient(
                    90deg, #7bc67e 0px, #7bc67e 4px,
                    #5aae5e 4px, #5aae5e 6px,
                    #8dd491 6px, #8dd491 8px
                  ),
                  linear-gradient(180deg, #6dbd70 0%, #4a9e4e 100%)
                `,
                borderRadius: '9999px',
                transition: 'width 0.6s ease',
              }"
            />

            <!-- 5个圆点 -->
            <div
              v-for="(ai, i) in AI_LIST"
              v-show="!aiCompleted.includes(ai)"
              :key="ai"
              :style="{
                position: 'absolute',
                left: `calc(${20 + i * 15}% - 5px)`,
                top: '50%',
                marginTop: '-5px',
                width: '10px',
                height: '10px',
                borderRadius: '5px',
                background: AI_COLORS[ai],
                boxShadow: `0 0 4px ${AI_COLORS[ai]}`,
                zIndex: 2,
              }"
            />

            <!-- 苹果 -->
            <span
              :style="{
                position: 'absolute',
                left: appleLeft,
                top: 0,
                fontSize: '22px',
                lineHeight: '24px',
                zIndex: 3,
                transition: 'left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
                animation: applePhase === 'rolling' || applePhase === 'sprint'
                  ? 'appleSpin 0.7s linear infinite'
                  : applePhase === 'done'
                    ? 'appleWiggle 0.3s ease'
                    : 'none',
                filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.15))',
              }"
            >🍎</span>
          </div>
        </div>
      </div>

      <!-- ===== KPI 卡片 ===== -->
      <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 32px">
        <div
          v-for="s in [
            { label: '总订单', value: overview?.total_orders || 0, color: '#1d1d1f' },
            { label: '总销售额', value: `¥${(overview?.total_revenue || 0).toFixed(0)}`, color: '#1d1d1f' },
            { label: '今日订单', value: rankings.reduce((s, r) => s + r.units_sold, 0), color: '#30d158' },
            { label: '待审批策略', value: overview?.pending_strategies || 0, color: '#ff9f0a' },
            { label: '活跃商家', value: rankings.length || 5, color: '#0066cc' },
          ]"
          :key="s.label"
          :style="{
            background: '#fff',
            border: '1px solid #e0e0e0',
            borderRadius: '14px',
            padding: '18px',
            textAlign: 'center',
          }"
        >
          <div style="font-size: 11px; color: #7a7a7a; margin-bottom: 4px">{{ s.label }}</div>
          <div :style="{ fontSize: '24px', fontWeight: 700, color: s.color }">{{ s.value }}</div>
        </div>
      </div>

      <!-- ===== 操作按钮 ===== -->
      <div style="display: flex; gap: 12px; margin-bottom: 32px; justify-content: center; flex-wrap: wrap">
        <a-button style="height: 40px; border-radius: 9999px; padding: 0 20px" @click="loadDecisionLog">
          <BulbOutlined /> 查看今日决策
        </a-button>
        <a-button style="height: 40px; border-radius: 9999px; padding: 0 20px" @click="loadAll">
          <ReloadOutlined /> 刷新
        </a-button>
        <a-button
          danger
          style="height: 40px; border-radius: 9999px; padding: 0 20px"
          @click="async () => {
            if (confirm('确认重置？将清除所有模拟数据，天数归零，库存恢复初始值。此操作不可撤销。')) {
              await client.post('/admin/reset')
              message.success('已重置')
              loadAll()
            }
          }"
        >
          <WarningOutlined /> ⚠️ 一键重置
        </a-button>
        <a-button style="height: 40px; border-radius: 9999px; padding: 0 20px" @click="openRestockDrawer">
          <ShoppingCartOutlined /> 📦 进货管理
        </a-button>
      </div>

      <!-- ===== 平台建议 ===== -->
      <div v-if="suggestions.length > 0" style="margin-bottom: 32px">
        <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px">
          <BulbOutlined style="color: #ff9f0a" /> 平台建议
        </h2>
        <div style="display: flex; flex-direction: column; gap: 8px">
          <div
            v-for="(s, i) in suggestions"
            :key="i"
            :style="{
              background: s.type === 'alert' ? '#fef2f2' : s.type === 'warning' ? '#fffbeb' : '#f0f9ff',
              border: `1px solid ${s.type === 'alert' ? '#fecaca' : s.type === 'warning' ? '#fde68a' : '#bfdbfe'}`,
              borderRadius: '11px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }"
          >
            <a-tag
              :style="{
                background: AI_COLORS[s.merchant_ai] || '#666',
                color: '#fff',
                border: 'none',
                borderRadius: '9999px',
              }"
            >
              {{ AI_LABELS[s.merchant_ai] || s.merchant_ai }}
            </a-tag>
            <span style="font-size: 14px; color: #1d1d1f; flex: 1">
              {{ s.message }}
              <span v-if="s.advice" style="color: #7a7a7a; margin-left: 8px">{{ s.advice }}</span>
            </span>
          </div>
        </div>
      </div>

      <!-- ===== AI 商家排行榜 ===== -->
      <div v-if="rankings.length > 0" style="margin-bottom: 32px">
        <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px">
          <TrophyOutlined style="color: #f59e0b" /> AI 商家排行榜
        </h2>
        <div style="display: flex; flex-direction: column; gap: 8px">
          <div
            v-for="(r, i) in rankings"
            :key="r.merchant_ai"
            :style="{
              background: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '14px',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              borderLeft: `4px solid ${AI_COLORS[r.merchant_ai] || '#666'}`,
            }"
          >
            <!-- 排名 -->
            <div
              :style="{
                width: '40px',
                textAlign: 'center',
                fontSize: i < 3 ? '24px' : '18px',
                fontWeight: 700,
                color: i < 3 ? '#1d1d1f' : '#7a7a7a',
              }"
            >
              {{ i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}` }}
            </div>

            <!-- 商家信息 -->
            <div style="flex: 1; min-width: 0">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px">
                <span style="font-weight: 600; font-size: 16px; color: #1d1d1f">
                  {{ AI_LABELS[r.merchant_ai] || r.merchant_ai }}
                </span>
                <a-tag style="background: #f5f5f7; border: none; border-radius: 9999px; font-size: 12px; margin: 0">
                  {{ r.category }}
                </a-tag>
                <ArrowUpOutlined v-if="getTrendIcon(r) === 'up'" style="color: #30d158" />
                <ArrowDownOutlined v-else-if="getTrendIcon(r) === 'down'" style="color: #ff3b30" />
                <MinusOutlined v-else-if="getTrendIcon(r) === 'same'" style="color: #7a7a7a" />
              </div>
              <div style="font-size: 13px; color: #7a7a7a">
                {{ r.promotion ? `🎯 ${r.promotion}` : '无促销' }} ·
                重点: {{ DEMO_LABELS[r.target_focus] || r.target_focus }} ·
                流量: {{ r.traffic_received }}
              </div>
            </div>

            <!-- 数据 -->
            <div style="display: flex; gap: 24px; text-align: center">
              <div>
                <div style="font-size: 11px; color: #7a7a7a">销量</div>
                <div style="font-size: 20px; font-weight: 700; color: #1d1d1f">{{ r.units_sold }}</div>
              </div>
              <div>
                <div style="font-size: 11px; color: #7a7a7a">收入</div>
                <div style="font-size: 20px; font-weight: 700; color: #30d158">¥{{ r.revenue.toFixed(0) }}</div>
              </div>
              <div>
                <div style="font-size: 11px; color: #7a7a7a">定价</div>
                <div style="font-size: 20px; font-weight: 600; color: #1d1d1f">¥{{ r.price }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 决策因果链（弹窗） ===== -->
      <a-modal
        :title="`第 ${currentDay} 天 — 决策因果链`"
        :open="showDecisionLog"
        @cancel="showDecisionLog = false"
        :footer="null"
        :width="800"
      >
        <div style="display: flex; flex-direction: column; gap: 12px">
          <div
            v-for="d in decisionLog"
            :key="d.merchant_ai"
            :style="{
              background: '#f5f5f7',
              borderRadius: '11px',
              padding: '16px',
              borderLeft: `3px solid ${AI_COLORS[d.merchant_ai] || '#666'}`,
            }"
          >
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px">
              <div style="display: flex; align-items: center; gap: 8px">
                <a-tag
                  :style="{
                    background: AI_COLORS[d.merchant_ai] || '#666',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '9999px',
                  }"
                >
                  {{ AI_LABELS[d.merchant_ai] }}
                </a-tag>
                <span style="font-weight: 600">{{ d.product_name }}</span>
                <span style="font-size: 12px; color: #7a7a7a">第{{ d.rank }}名</span>
              </div>
              <div style="font-size: 14px; color: #7a7a7a">
                {{ d.units_sold }}件 · ¥{{ d.revenue.toFixed(0) }}
              </div>
            </div>
            <div style="font-size: 13px; color: #1d1d1f; line-height: 1.6">
              <strong>决策：</strong>定价¥{{ d.price }}
              <template v-if="d.promotion"> | 促销: {{ d.promotion }}</template>
              | 重点人群: {{ DEMO_LABELS[d.target_focus] || d.target_focus }}
            </div>
            <div style="font-size: 13px; color: #7a7a7a; margin-top: 4px">
              <strong>理由：</strong>{{ d.reasoning }}
            </div>
            <div v-if="d.research_product" style="font-size: 13px; color: #6366f1; margin-top: 4px">
              🔬 正在研发：{{ d.research_product }}
            </div>
          </div>
        </div>
      </a-modal>

      <!-- ===== 待审批策略 ===== -->
      <div v-if="pendingStrategies.length > 0" style="margin-top: 48px">
        <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 16px">待审批策略</h2>
        <div style="display: flex; flex-direction: column; gap: 12px">
          <div
            v-for="s in pendingStrategies"
            :key="s.id"
            :style="{
              background: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '14px',
              padding: '20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
            }"
          >
            <div style="flex: 1">
              <div style="display: flex; gap: 8px; margin-bottom: 8px">
                <a-tag style="background: #fff3e0; color: #ff9f0a; border: none; border-radius: 9999px">
                  {{ TYPE_LABELS[s.strategy_type] || s.strategy_type }}
                </a-tag>
                <a-tag style="background: #fff3e0; color: #ff9f0a; border: none; border-radius: 9999px">
                  ⚠️ 需审批
                </a-tag>
              </div>
              <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 4px">{{ s.title }}</h3>
              <p style="font-size: 14px; color: #1d1d1f; margin-bottom: 8px">{{ s.description }}</p>
              <div style="background: #f5f5f7; border-radius: 8px; padding: 10px; font-size: 12px; color: #7a7a7a">
                <strong>AI理由：</strong>{{ s.ai_reasoning }}
              </div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px; margin-left: 16px">
              <a-button type="primary" size="small" @click="commentModal = { id: s.id, action: 'approve' }">
                <CheckOutlined /> 批准
              </a-button>
              <a-button size="small" @click="commentModal = { id: s.id, action: 'reject' }">
                <CloseOutlined /> 驳回
              </a-button>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 空状态 ===== -->
      <div
        v-if="rankings.length === 0"
        :style="{
          textAlign: 'center',
          padding: '80px',
          color: '#7a7a7a',
          background: '#f5f5f7',
          borderRadius: '18px',
        }"
      >
        <RocketOutlined style="font-size: 48px; margin-bottom: 16px; color: #d0d0d0" />
        <p style="font-size: 21px; font-weight: 600; margin-bottom: 8px">尚未开始模拟</p>
        <p style="font-size: 17px">点击「推进明天」开始第一天的AI竞争</p>
      </div>

      <!-- ===== 审批弹窗 ===== -->
      <a-modal
        :title="commentModal?.action === 'approve' ? '批准策略' : '驳回策略'"
        :open="!!commentModal"
        @ok="handleAction"
        @cancel="commentModal = null; comment = ''"
        :confirm-loading="submitting"
        :ok-text="commentModal?.action === 'approve' ? '确认批准' : '确认驳回'"
        :ok-button-props="{ danger: commentModal?.action === 'reject' }"
      >
        <a-textarea
          v-model:value="comment"
          :rows="3"
          placeholder="输入批注（可选）..."
        />
      </a-modal>

      <!-- ===== 进货抽屉 ===== -->
      <a-drawer
        title="📦 进货管理"
        :open="restockDrawer"
        @close="restockDrawer = false"
        :width="420"
      >
        <div
          v-for="p in productList"
          :key="p.id"
          :style="{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '14px 0',
            borderBottom: '1px solid #f0f0f0',
          }"
        >
          <span
            :style="{
              width: '10px',
              height: '10px',
              borderRadius: '5px',
              background: AI_COLORS[p.ai_model] || '#999',
              flexShrink: 0,
            }"
          />
          <div style="flex: 1; min-width: 0">
            <div style="font-size: 14px; font-weight: 600">{{ p.name }}</div>
            <div style="font-size: 12px; color: #7a7a7a">
              {{ AI_LABELS[p.ai_model] || p.ai_model }} · {{ p.category }} · 当前库存 <b>{{ p.stock }}</b>
            </div>
          </div>
          <a-input-number
            :min="1"
            :max="99999"
            :value="restockAmounts[p.ai_model] || 100"
            @change="(v: number | null) => restockAmounts = { ...restockAmounts, [p.ai_model]: v || 0 }"
            style="width: 80px"
          />
          <a-button
            type="primary"
            size="small"
            style="border-radius: 9999px"
            @click="doRestock(p.id, p.ai_model)"
          >
            进货
          </a-button>
        </div>
        <div style="margin-top: 24px; text-align: right">
          <a-button type="primary" style="border-radius: 9999px" @click="doRestockAll">
            一键全部进货
          </a-button>
        </div>
      </a-drawer>
    </template>
  </div>
</template>

<style>
@keyframes appleSpin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(-360deg); }
}
@keyframes appleWiggle {
  0%, 100% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(-12deg) scale(1.25); }
}
</style>
