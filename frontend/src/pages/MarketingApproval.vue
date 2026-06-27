<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { CheckOutlined, CloseOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import client from '../api/client'
import { getStrategies, approveStrategy, rejectStrategy } from '../api/marketing'

interface Strategy {
  id: number
  merchant_id: number
  strategy_type: string
  title: string
  description: string
  proposed_changes: Record<string, any>
  status: string
  ai_reasoning: string
  admin_comment: string
  created_at: string | null
}

const AI_LABELS: Record<string, string> = {
  GLM: 'GLM', gpt: 'GPT', MiniMax: 'MiniMax', Kimi: 'Kimi', qwen: '通义千问',
}
const AI_COLORS: Record<string, string> = {
  GLM: '#6366f1', gpt: '#10b981', MiniMax: '#f59e0b', Kimi: '#ef4444', qwen: '#3b82f6',
}
const TYPE_LABELS: Record<string, string> = {
  price_adjustment: '调价', promotion: '促销活动',
  bundle: '捆绑销售', recommendation_update: '推荐更新',
}
const STATUS_LABELS: Record<string, string> = {
  pending: '待审批', approved: '已批准', rejected: '已驳回', executed: '已执行',
}
const STATUS_COLORS: Record<string, string> = {
  pending: 'orange', approved: 'green', rejected: 'red', executed: 'blue',
}

const strategies = ref<Strategy[]>([])
const merchants = ref<Record<number, any>>({})
const loading = ref(true)
const commentModal = ref<{ id: number; action: 'approve' | 'reject' } | null>(null)
const comment = ref('')
const submitting = ref(false)

const pendingStrategies = computed(() => strategies.value.filter(s => s.status === 'pending'))
const executedCount = computed(() => strategies.value.filter(s => s.status === 'executed').length)

async function loadAll() {
  loading.value = true
  try {
    const [stRes, mRes] = await Promise.all([
      getStrategies({}),
      client.get('/merchants'),
    ])
    strategies.value = Array.isArray(stRes.data) ? stRes.data : []
    const map: Record<number, any> = {}
    for (const m of mRes.data) {
      map[m.id] = m
    }
    merchants.value = map
  } catch (e) {
    console.error('加载失败', e)
  }
  loading.value = false
}

async function handleAction() {
  if (!commentModal.value) return
  submitting.value = true
  try {
    const { id, action } = commentModal.value
    if (action === 'approve') {
      await approveStrategy(id, comment.value)
    } else {
      await rejectStrategy(id, comment.value)
    }
    message.success(action === 'approve' ? '已批准' : '已驳回')
    commentModal.value = null
    comment.value = ''
    loadAll()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  }
  submitting.value = false
}

onMounted(loadAll)
</script>

<template>
  <div style="max-width: 1100px; margin: 0 auto; padding: 48px 24px">
    <div style="text-align: center; margin-bottom: 48px">
      <h1 style="font-size: 40px; font-weight: 600; color: '#1d1d1f'; margin-bottom: 8px">营销策略审批</h1>
      <p style="font-size: 21px; color: '#7a7a7a'">AI 商家提交的策略变更需要人工审批</p>
    </div>

    <a-spin v-if="loading" size="large" style="display: block; text-align: center; padding: 100px" />

    <template v-else>
      <!-- KPI -->
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 32px">
        <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 14px; padding: 18px; text-align: center">
          <div style="font-size: 11px; color: #7a7a7a; margin-bottom: 4px">待审批</div>
          <div style="font-size: 24px; font-weight: 700; color: #ff9f0a">{{ pendingStrategies.length }}</div>
        </div>
        <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 14px; padding: 18px; text-align: center">
          <div style="font-size: 11px; color: #7a7a7a; margin-bottom: 4px">已执行</div>
          <div style="font-size: 24px; font-weight: 700; color: #30d158">{{ executedCount }}</div>
        </div>
        <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 14px; padding: 18px; text-align: center">
          <div style="font-size: 11px; color: #7a7a7a; margin-bottom: 4px">总策略</div>
          <div style="font-size: 24px; font-weight: 700; color: #1d1d1f">{{ strategies.length }}</div>
        </div>
      </div>

      <!-- 待审批策略 -->
      <template v-if="pendingStrategies.length > 0">
        <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 16px">待审批策略</h2>
        <div style="display: flex; flex-direction: column; gap: 12px">
          <div
            v-for="s in pendingStrategies"
            :key="s.id"
            style="background: #fff; border: 1px solid #e0e0e0; border-radius: 14px; padding: 20px; display: flex; justify-content: space-between; align-items: flex-start"
          >
            <div style="flex: 1">
              <div style="display: flex; gap: 8px; margin-bottom: 8px">
                <a-tag style="background: #fff3e0; color: #ff9f0a; border: none; border-radius: 9999px">
                  {{ TYPE_LABELS[s.strategy_type] || s.strategy_type }}
                </a-tag>
                <a-tag
                  v-if="merchants[s.merchant_id]"
                  :style="{ background: (AI_COLORS[merchants[s.merchant_id]?.ai_model] || '#666') + '20', color: AI_COLORS[merchants[s.merchant_id]?.ai_model] || '#666', border: 'none', borderRadius: '9999px' }"
                >
                  {{ AI_LABELS[merchants[s.merchant_id]?.ai_model] || '' }}
                </a-tag>
                <a-tag style="background: #fff3e0; color: #ff9f0a; border: none; border-radius: 9999px">⚠️ 需审批</a-tag>
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
      </template>

      <!-- 所有策略历史 -->
      <div style="margin-top: 48px">
        <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 16px">全部策略</h2>
        <div style="display: flex; flex-direction: column; gap: 8px">
          <div
            v-for="s in strategies"
            :key="s.id"
            style="background: #fff; border: 1px solid #e0e0e0; border-radius: 11px; padding: 12px 16px; display: flex; align-items: center; gap: 12px"
          >
            <a-tag :color="STATUS_COLORS[s.status] || 'default'" style="border-radius: 9999px">
              {{ STATUS_LABELS[s.status] || s.status }}
            </a-tag>
            <span style="font-weight: 600; flex: 1">{{ s.title }}</span>
            <span v-if="s.created_at" style="font-size: 12px; color: #7a7a7a">
              {{ s.created_at.slice(0, 16).replace('T', ' ') }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- 审批弹窗 -->
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
  </div>
</template>
