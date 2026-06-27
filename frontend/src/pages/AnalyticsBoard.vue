<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import client from '../api/client'

// 注册 ECharts 必要组件
use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const AI_LABELS: Record<string, string> = {
  GLM: 'GLM', gpt: 'GPT', MiniMax: 'MiniMax', Kimi: 'Kimi', qwen: '通义千问',
}
const AI_COLORS: Record<string, string> = {
  GLM: '#6366f1', gpt: '#10b981', MiniMax: '#f59e0b', Kimi: '#ef4444', qwen: '#3b82f6',
}
const DEMO_LABELS: Record<string, string> = {
  elderly: '老年', youth: '青年', middle: '中年', child: '儿童',
}
const DEMO_COLORS: Record<string, string> = {
  elderly: '#fa541c', youth: '#2f54eb', middle: '#722ed1', child: '#52c41a',
}

interface SalesTrendPoint { date: string; orders: number; revenue: number }
interface DemoDist { demographic: string; count: number; revenue: number }
interface ProductCompare {
  product_id: number; product_name: string; ai_model: string;
  category: string; orders: number; units_sold: number; revenue: number
}
interface Iteration {
  id: number; merchant_ai: string; day: number;
  old_name: string; new_name: string;
  old_description: string; new_description: string;
  old_price: number; new_price: number
}

const DIM_TABS = [
  { key: 'ai', label: '按商家' },
  { key: 'demographic', label: '按人群' },
]

const trendData = ref<{ days: number[]; series: Record<string, number[]> }>({ days: [], series: {} })
const dimension = ref<string>('ai')
const demoDist = ref<DemoDist[]>([])
const categoryDemoData = ref<DemoDist[]>([])
const demoCategory = ref<string>('all')
const products = ref<ProductCompare[]>([])
const loading = ref(true)
const iterations = ref<Iteration[]>([])
const iterMerchant = ref<string>('gpt')
const expandedIter = ref<number | null>(null)
const iterLoading = ref(false)

// 品类 → product_id 映射
const categoryProductMap = computed(() => {
  const map: Record<string, number> = {}
  products.value.forEach(p => { map[p.category] = p.product_id })
  return map
})

// AI → 品类名映射
const aiCategoryMap = computed(() => {
  const map: Record<string, string> = {}
  products.value.forEach(p => { map[p.ai_model] = p.category })
  return map
})

const totalRevenue = computed(() => products.value.reduce((s, p) => s + p.revenue, 0))
const totalOrders = computed(() => products.value.reduce((s, p) => s + p.orders, 0))
const totalUnits = computed(() => products.value.reduce((s, p) => s + p.units_sold, 0))
const avgOrderValue = computed(() => totalOrders.value > 0 ? totalRevenue.value / totalOrders.value : 0)

const allDays = computed(() => trendData.value.days || [])

async function loadIterations() {
  iterLoading.value = true
  try {
    const res = await client.get(`/admin/product-iterations?merchant_ai=${iterMerchant.value}`)
    iterations.value = res.data
  } catch { iterations.value = [] }
  iterLoading.value = false
}

onMounted(() => {
  loadData()
  loadIterations()
})

watch(dimension, () => { loadData() })
watch(iterMerchant, () => { loadIterations() })

watch(demoCategory, async (cat) => {
  if (cat === 'all') {
    categoryDemoData.value = []
    return
  }
  const pid = categoryProductMap.value[cat]
  if (!pid) return
  try {
    const res = await client.get(`/analytics/product/${pid}/demographic-breakdown`)
    categoryDemoData.value = res.data
  } catch { categoryDemoData.value = [] }
})

async function loadData() {
  loading.value = true
  try {
    const [tRes, dRes, pRes] = await Promise.all([
      client.get(`/analytics/sales-trend?dimension=${dimension.value}`),
      client.get('/analytics/demographic-dist'),
      client.get('/analytics/product-compare'),
    ])
    trendData.value = tRes.data
    demoDist.value = dRes.data
    products.value = pRes.data
  } catch { /* */ }
  loading.value = false
}

// 趋势图系列
const trendSeries = computed(() =>
  Object.entries(trendData.value.series || {}).map(([key, values]) => {
    const colorMap: Record<string, string> = { ...AI_COLORS, ...DEMO_COLORS }
    const label = AI_LABELS[key] || DEMO_LABELS[key] || key
    const categoryLabel = aiCategoryMap.value[key]
    const displayName = dimension.value === 'ai' && categoryLabel ? `${label} · ${categoryLabel}` : label
    return {
      name: displayName,
      type: 'line' as const,
      data: values,
      smooth: true,
      lineStyle: { width: 2 },
      itemStyle: { color: colorMap[key] || '#999' },
      symbol: 'circle',
      symbolSize: 6,
    }
  })
)

// 趋势图 ECharts option
const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' as const },
  legend: { data: trendSeries.value.map(s => s.name), bottom: 0 },
  grid: { top: 20, bottom: 50, left: 50, right: 30 },
  xAxis: {
    type: 'category' as const,
    data: allDays.value.map(d => `第${d}天`),
    axisLine: { lineStyle: { color: '#e0e0e0' } },
  },
  yAxis: {
    type: 'value' as const,
    name: '销量(件)',
    splitLine: { lineStyle: { color: '#f0f0f0' } },
  },
  series: trendSeries.value,
}))

// 人群购买饼图
const pieSource = computed(() => demoCategory.value === 'all' ? demoDist.value : categoryDemoData.value)

const pieOption = computed(() => ({
  tooltip: { trigger: 'item' as const },
  legend: { bottom: 0 },
  series: [{
    type: 'pie' as const,
    radius: ['40%', '70%'],
    data: pieSource.value.map(d => ({
      name: DEMO_LABELS[d.demographic] || d.demographic,
      value: d.count,
      itemStyle: { color: DEMO_COLORS[d.demographic] },
    })),
    label: { formatter: '{b}\n{d}%', fontSize: 12 },
  }],
}))

// 产品对比柱状图
const productBarOption = computed(() => ({
  tooltip: { trigger: 'axis' as const },
  grid: { top: 20, bottom: 40, left: 100, right: 20 },
  xAxis: { type: 'value' as const, name: '销售额(元)', splitLine: { lineStyle: { color: '#f0f0f0' } } },
  yAxis: {
    type: 'category' as const,
    data: products.value.map(p => p.product_name),
    axisLabel: { width: 120, overflow: 'truncate' },
  },
  series: [{
    type: 'bar' as const,
    data: products.value.map(p => ({
      value: p.revenue,
      itemStyle: { color: AI_COLORS[p.ai_model] || '#0066cc', borderRadius: [0, 4, 4, 0] },
    })),
    label: { show: true, position: 'right', formatter: '¥{c}', fontSize: 12 },
  }],
}))
</script>

<template>
  <div style="max-width: 1200px; margin: 0 auto; padding: 48px 0">
    <div style="text-align: center; margin-bottom: 48px">
      <h1 style="font-size: 40px; font-weight: 600; letter-spacing: 0; margin-bottom: 8px">数据看板</h1>
      <p style="font-size: 21px; color: #7a7a7a">5 款产品 · 5 个 AI · 实时销售洞察</p>
    </div>

    <a-spin v-if="loading" size="large" style="display: block; text-align: center; padding: 200px" />

    <template v-else>
      <!-- 维度切换 -->
      <div style="text-align: center; margin-bottom: 32px">
        <a-tabs v-model:activeKey="dimension" centered>
          <a-tab-pane v-for="t in DIM_TABS" :key="t.key" :tab="t.label" />
        </a-tabs>
      </div>

      <!-- KPI -->
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 48px">
        <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 18px; padding: 24px; text-align: center">
          <div style="font-size: 12px; color: #7a7a7a; margin-bottom: 4px">总销售额</div>
          <div style="font-size: 28px; font-weight: 600; color: #1d1d1f">¥{{ totalRevenue.toFixed(0) }}</div>
        </div>
        <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 18px; padding: 24px; text-align: center">
          <div style="font-size: 12px; color: #7a7a7a; margin-bottom: 4px">总订单量</div>
          <div style="font-size: 28px; font-weight: 600; color: #1d1d1f">{{ totalOrders }}</div>
        </div>
        <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 18px; padding: 24px; text-align: center">
          <div style="font-size: 12px; color: #7a7a7a; margin-bottom: 4px">平均客单价</div>
          <div style="font-size: 28px; font-weight: 600; color: #1d1d1f">¥{{ avgOrderValue.toFixed(0) }}</div>
        </div>
      </div>

      <!-- 销售趋势 -->
      <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 18px; padding: 32px; margin-bottom: 32px">
        <h2 style="font-size: 21px; font-weight: 600; margin-bottom: 16px">
          销售趋势 · {{ DIM_TABS.find(t => t.key === dimension)?.label || dimension }}
        </h2>
        <v-chart v-if="allDays.length > 0" :option="trendOption" style="height: 350px" autoresize />
        <div v-else style="height: 350px; display: flex; align-items: center; justify-content: center; color: #7a7a7a">
          暂无数据，请先启动模拟
        </div>
      </div>

      <!-- 两列：人群分布 + 产品对比 -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-bottom: 32px">
        <!-- 购买人群分布 -->
        <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 18px; padding: 32px">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
            <h2 style="font-size: 21px; font-weight: 600; margin: 0">购买人群分布</h2>
            <a-select v-model:value="demoCategory" style="width: 120px" size="small">
              <a-select-option value="all">全部品类</a-select-option>
              <a-select-option v-for="p in products" :key="p.category" :value="p.category">
                {{ p.category }}
              </a-select-option>
            </a-select>
          </div>
          <v-chart v-if="pieSource.length > 0" :option="pieOption" style="height: 300px" autoresize />
          <div v-else style="height: 300px; display: flex; align-items: center; justify-content: center; color: #7a7a7a">暂无数据</div>
        </div>

        <!-- 产品 AI 对比 -->
        <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 18px; padding: 32px">
          <h2 style="font-size: 21px; font-weight: 600; margin-bottom: 16px">产品 AI 经营对比</h2>
          <v-chart v-if="products.length > 0" :option="productBarOption" style="height: 300px" autoresize />
          <div v-else style="height: 300px; display: flex; align-items: center; justify-content: center; color: #7a7a7a">暂无数据</div>
        </div>
      </div>

      <!-- 产品明细表 -->
      <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 18px; padding: 32px">
        <h2 style="font-size: 21px; font-weight: 600; margin-bottom: 24px">产品明细</h2>
        <table style="width: 100%; border-collapse: collapse; font-size: 17px">
          <thead>
            <tr style="border-bottom: 1px solid #f0f0f0">
              <th style="text-align: left; padding: 12px 0; color: #7a7a7a; font-weight: 400; font-size: 14px">产品</th>
              <th style="text-align: left; padding: 12px 0; color: #7a7a7a; font-weight: 400; font-size: 14px">AI 管理</th>
              <th style="text-align: left; padding: 12px 0; color: #7a7a7a; font-weight: 400; font-size: 14px">品类</th>
              <th style="text-align: right; padding: 12px 0; color: #7a7a7a; font-weight: 400; font-size: 14px">销量</th>
              <th style="text-align: right; padding: 12px 0; color: #7a7a7a; font-weight: 400; font-size: 14px">销售额</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in products" :key="p.product_id" style="border-bottom: 1px solid #f5f5f7">
              <td style="padding: 12px 0; font-weight: 600">{{ p.product_name }}</td>
              <td style="padding: 12px 0">
                <a-tag
                  :style="{
                    background: (AI_COLORS[p.ai_model] || '#666') + '15',
                    color: AI_COLORS[p.ai_model] || '#666',
                    border: 'none',
                    borderRadius: '9999px',
                    fontSize: '12px',
                  }"
                >
                  {{ AI_LABELS[p.ai_model] || p.ai_model }}
                </a-tag>
              </td>
              <td style="padding: 12px 0; color: #7a7a7a">{{ p.category }}</td>
              <td style="padding: 12px 0; text-align: right">{{ p.units_sold }}</td>
              <td style="padding: 12px 0; text-align: right; font-weight: 600">¥{{ p.revenue.toFixed(0) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 产品迭代历史 -->
      <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 18px; padding: 32px; margin-top: 32px">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
          <h2 style="font-size: 21px; font-weight: 600; margin: 0">产品迭代历史</h2>
          <a-select v-model:value="iterMerchant" style="width: 160px">
            <a-select-option v-for="(label, key) in AI_LABELS" :key="key" :value="key">{{ label }}</a-select-option>
          </a-select>
        </div>

        <a-spin v-if="iterLoading" style="display: block; text-align: center" />

        <div v-else-if="iterations.length === 0" style="text-align: center; padding: 40px; color: #7a7a7a; font-size: 14px">
          暂无产品迭代记录
        </div>

        <div v-else style="display: flex; flex-direction: column">
          <div v-for="(it, idx) in iterations" :key="it.id" style="display: flex; gap: 0">
            <div style="display: flex; flex-direction: column; align-items: center; width: 32px; flex-shrink: 0">
              <div
                :style="{
                  width: idx === 0 ? '14px' : '10px',
                  height: idx === 0 ? '14px' : '10px',
                  borderRadius: '50%',
                  background: idx === 0 ? (AI_COLORS[it.merchant_ai] || '#0066cc') : '#d0d0d0',
                  border: idx === 0 ? `3px solid ${(AI_COLORS[it.merchant_ai] || '#0066cc')}33` : '2px solid #e0e0e0',
                  flexShrink: 0,
                  marginTop: '8px',
                }"
              />
              <div
                :style="{
                  width: '2px',
                  flex: 1,
                  background: idx < iterations.length - 1 ? '#e8e8e8' : 'transparent',
                  minHeight: '20px',
                }"
              />
            </div>

            <div
              style="flex: 1; padding: 10px 0 10px 12px; cursor: pointer"
              @click="expandedIter = expandedIter === it.id ? null : it.id"
            >
              <div style="font-size: 13px; color: #7a7a7a; margin-bottom: 2px">第 {{ it.day }} 天</div>
              <div style="font-size: 15px; color: #1d1d1f; line-height: 1.4">
                <span style="text-decoration: line-through; color: #7a7a7a">{{ it.old_name }}</span>
                {{ ' → ' }}
                <span :style="{ fontWeight: 600, color: AI_COLORS[it.merchant_ai] || '#0066cc' }">{{ it.new_name }}</span>
              </div>

              <div
                v-if="expandedIter === it.id"
                :style="{
                  marginTop: '12px',
                  background: '#f9f9fb',
                  borderRadius: '10px',
                  padding: '16px',
                  border: '1px solid #eee',
                }"
              >
                <table style="width: 100%; border-collapse: collapse; font-size: 13px">
                  <thead>
                    <tr style="border-bottom: 1px solid #e0e0e0">
                      <th style="text-align: left; padding: 6px 8px; color: #7a7a7a; font-weight: 400; font-size: 12px">字段</th>
                      <th style="text-align: left; padding: 6px 8px; color: #7a7a7a; font-weight: 400; font-size: 12px">旧值</th>
                      <th :style="{ textAlign: 'left', padding: '6px 8px', color: AI_COLORS[it.merchant_ai] || '#0066cc', fontWeight: 400, fontSize: '12px' }">新值</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style="border-bottom: 1px solid #f0f0f0">
                      <td style="padding: 8px; color: #7a7a7a; font-size: 12px">产品名</td>
                      <td style="padding: 8px; color: #7a7a7a">{{ it.old_name }}</td>
                      <td :style="{ padding: '8px', color: AI_COLORS[it.merchant_ai] || '#0066cc', fontWeight: 500 }">{{ it.new_name }}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f0f0f0">
                      <td style="padding: 8px; color: #7a7a7a; font-size: 12px">描述</td>
                      <td style="padding: 8px; color: #7a7a7a">{{ it.old_description }}</td>
                      <td :style="{ padding: '8px', color: AI_COLORS[it.merchant_ai] || '#0066cc', fontWeight: 500 }">{{ it.new_description }}</td>
                    </tr>
                    <tr>
                      <td style="padding: 8px; color: #7a7a7a; font-size: 12px">价格</td>
                      <td style="padding: 8px; color: #7a7a7a">¥{{ it.old_price }}</td>
                      <td :style="{ padding: '8px', color: AI_COLORS[it.merchant_ai] || '#0066cc', fontWeight: 500 }">¥{{ it.new_price }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
