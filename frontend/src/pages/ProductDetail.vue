<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeftOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { getProduct } from '../api/products'
import client from '../api/client'

const AI_LABELS: Record<string, string> = {
  GLM: 'GLM', gpt: 'GPT', MiniMax: 'MiniMax', Kimi: 'Kimi', qwen: '通义千问',
}
const AI_COLORS: Record<string, string> = {
  GLM: '#1677ff', gpt: '#722ed1', MiniMax: '#ff4d4f', Kimi: '#ff6600', qwen: '#52c41a',
}
const DEMO_LABELS: Record<string, string> = {
  elderly: '老年人', female: '女性', male: '男性', child: '儿童',
}

const route = useRoute()
const router = useRouter()
const product = ref<any>(null)
const demoBreakdown = ref<any[]>([])
const loading = ref(true)

async function loadData() {
  loading.value = true
  const id = Number(route.params.id)
  try {
    const [pRes, dRes] = await Promise.all([
      getProduct(id),
      client.get(`/analytics/product/${id}/demographic-breakdown`),
    ])
    product.value = pRes.data
    demoBreakdown.value = dRes.data
  } catch {
    const pRes = await getProduct(id)
    product.value = pRes.data
  }
  loading.value = false
}

onMounted(loadData)
watch(() => route.params.id, loadData)

const discount = computed(() =>
  product.value?.original_price > product.value?.price
    ? Math.round((1 - product.value.price / product.value.original_price) * 100)
    : 0
)
const aiColor = computed(() => AI_COLORS[product.value?.ai_model] || '#666')
const strategyHistory = computed(() => product.value?.ai_strategy_history || [])
</script>

<template>
  <div>
    <a-spin v-if="loading || !product" size="large" style="display: block; text-align: center; padding: 200px" />

    <template v-else>
      <!-- Hero -->
      <section style="background: #272729; color: #ffffff; padding: 60px 48px; margin: 0 -48px">
        <div style="max-width: 980px; margin: 0 auto">
          <a-button
            type="text"
            style="color: #a1a1a6; margin-bottom: 24px; font-size: 14px"
            @click="router.push('/')"
          >
            <ArrowLeftOutlined /> 返回产品总览
          </a-button>
          <div style="display: flex; gap: 48px; flex-wrap: wrap; align-items: center">
            <div
              :style="{
                flex: '0 0 240px',
                height: '240px',
                background: 'rgba(255,255,255,0.06)',
                borderRadius: '18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '80px',
                boxShadow: 'rgba(0, 0, 0, 0.22) 3px 5px 30px 0',
              }"
            >
              💊
            </div>
            <div style="flex: 1">
              <div style="margin-bottom: 12px; display: flex; gap: 8px">
                <a-tag
                  :style="{
                    background: aiColor + '25',
                    color: aiColor,
                    border: 'none',
                    borderRadius: '9999px',
                    padding: '4px 14px',
                  }"
                >
                  <RobotOutlined /> {{ AI_LABELS[product.ai_model] }} AI 独立管理
                </a-tag>
                <a-tag
                  :style="{
                    background: 'rgba(255,255,255,0.12)',
                    color: '#cccccc',
                    border: 'none',
                    borderRadius: '9999px',
                    padding: '4px 14px',
                  }"
                >
                  {{ product.category }}
                </a-tag>
              </div>
              <h1 style="font-size: 40px; font-weight: 600; color: #ffffff; letter-spacing: 0; line-height: 1.1; margin-bottom: 12px">
                {{ product.name }}
              </h1>
              <p style="font-size: 17px; color: #cccccc; line-height: 1.47; margin-bottom: 20px">
                {{ product.description }}
              </p>
              <div style="display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px">
                <span style="font-size: 28px; font-weight: 600">¥{{ product.price }}</span>
                <template v-if="discount > 0">
                  <span style="font-size: 17px; color: #7a7a7a; text-decoration: line-through">¥{{ product.original_price }}</span>
                  <span style="font-size: 14px; color: #2997ff; font-weight: 600">省 {{ discount }}%</span>
                </template>
              </div>
              <div style="display: flex; gap: 24px; font-size: 14px; color: #7a7a7a">
                <span>库存：{{ product.stock }}</span>
                <span>AI 模型：{{ AI_LABELS[product.ai_model] }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- AI 策略历史 + 人群分布 -->
      <section style="background: #f5f5f7; padding: 48px 48px 80px; margin: 0 -48px">
        <div style="max-width: 980px; margin: 0 auto">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px">
            <!-- AI 策略历史 -->
            <div
              :style="{
                background: '#ffffff',
                border: '1px solid #e0e0e0',
                borderRadius: '18px',
                padding: '32px',
              }"
            >
              <h2 style="font-size: 21px; font-weight: 600; margin-bottom: 24px">🤖 AI 策略历史</h2>
              <p v-if="strategyHistory.length === 0" style="color: #7a7a7a; font-size: 17px">暂无策略记录</p>
              <div v-else style="display: flex; flex-direction: column; gap: 12px">
                <div
                  v-for="(s, i) in strategyHistory"
                  :key="i"
                  style="background: #f5f5f7; border-radius: 11px; padding: 12px 16px; display: flex; align-items: center; gap: 12px"
                >
                  <span style="font-size: 12px; color: #7a7a7a; white-space: nowrap">
                    {{ (s.time || '').slice(0, 16).replace('T', ' ') }}
                  </span>
                  <span style="font-size: 14px; color: #1d1d1f; flex: 1">{{ s.title }}</span>
                  <a-tag
                    :style="{
                      background: s.auto_executed ? '#d4edda' : '#fff3e0',
                      color: s.auto_executed ? '#30d158' : '#ff9f0a',
                      border: 'none',
                      borderRadius: '9999px',
                      fontSize: '11px',
                    }"
                  >
                    {{ s.auto_executed ? '自动执行' : '需审批' }}
                  </a-tag>
                </div>
              </div>
            </div>

            <!-- 购买人群分布 -->
            <div
              :style="{
                background: '#ffffff',
                border: '1px solid #e0e0e0',
                borderRadius: '18px',
                padding: '32px',
              }"
            >
              <h2 style="font-size: 21px; font-weight: 600; margin-bottom: 24px">👥 购买人群分布</h2>
              <p v-if="demoBreakdown.length === 0" style="color: #7a7a7a; font-size: 17px">暂无购买数据，请先运行模拟</p>
              <div v-else style="display: flex; flex-direction: column; gap: 16px">
                <div v-for="d in demoBreakdown" :key="d.demographic">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px">
                    <span style="font-size: 14px; font-weight: 600">
                      {{ DEMO_LABELS[d.demographic] || d.demographic }}
                    </span>
                    <span style="font-size: 14px; color: #7a7a7a">
                      {{ d.count }}单 · ¥{{ d.revenue.toFixed(0) }}
                    </span>
                  </div>
                  <div style="height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden">
                    <div
                      :style="{
                        height: '100%',
                        width: (demoBreakdown.reduce((s: number, x: any) => s + x.count, 0) > 0
                          ? d.count / demoBreakdown.reduce((s: number, x: any) => s + x.count, 0) * 100
                          : 0) + '%',
                        background: '#0066cc',
                        borderRadius: '4px',
                        transition: 'width 0.3s',
                      }"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
