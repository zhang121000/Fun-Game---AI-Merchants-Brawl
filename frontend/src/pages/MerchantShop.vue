<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { RobotOutlined, RiseOutlined } from '@ant-design/icons-vue'
import { getMerchant, getMerchantProducts } from '../api/merchants'
import ProductCard from '../components/product/ProductCard.vue'
import client from '../api/client'

const MODEL_LABELS: Record<string, string> = {
  GLM: 'GLM', gpt: 'GPT', MiniMax: 'MiniMax', Kimi: 'Kimi', qwen: '通义千问',
}

const DEMOGRAPHIC_TABS = [
  { key: '', label: '全部' },
  { key: 'child', label: '孩童' },
  { key: 'male', label: '男性' },
  { key: 'female', label: '女性' },
  { key: 'elderly', label: '老年人' },
]

const route = useRoute()
const merchantId = computed(() => Number(route.params.id))

const merchant = ref<any>(null)
const products = ref<any[]>([])
const stats = ref<any>(null)
const demographic = ref('')
const loading = ref(true)
async function loadMerchant() {
  const res = await getMerchant(merchantId.value)
  merchant.value = res.data
}

async function loadProducts() {
  loading.value = true
  const res = await getMerchantProducts(merchantId.value, demographic.value || undefined)
  products.value = res.data
  loading.value = false
}

async function loadStats() {
  try {
    const res = await client.get('/admin/leaderboard')
    const rankings = res.data.rankings || []
    stats.value = {
      orders: rankings.reduce((sum: number, r: any) => sum + (r.units_sold || 0), 0),
      revenue: rankings.reduce((sum: number, r: any) => sum + (r.revenue || 0), 0),
    }
  } catch { /* */ }
}

onMounted(() => {
  loadMerchant()
  loadStats()
  loadProducts()
})

watch(() => merchantId.value, () => {
  loadMerchant()
  loadStats()
  loadProducts()
})

watch(demographic, () => {
  loadProducts()
})
</script>

<template>
  <div>
    <a-spin v-if="!merchant" size="large" style="display: block; text-align: center; padding: 200px" />

    <template v-else>
      <!-- Hero Section -->
      <section style="background: #272729; color: #ffffff; padding: 80px 48px; text-align: center; margin: 0 -48px">
        <RobotOutlined style="font-size: 48px; color: #2997ff; display: block; margin-bottom: 16px" />
        <h1 style="font-size: 40px; font-weight: 600; color: #ffffff; letter-spacing: 0; line-height: 1.1; margin-bottom: 8px">
          {{ merchant.name }}
        </h1>
        <p style="font-size: 21px; font-weight: 600; color: #cccccc; letter-spacing: 0.011em; margin-bottom: 16px">
          {{ merchant.main_category }}专营 · {{ MODEL_LABELS[merchant.ai_model] }} AI 驱动
        </p>
        <div v-if="stats" style="display: flex; gap: 48px; justify-content: center; margin-top: 24px">
          <a-statistic
            title="总订单"
            :value="stats.orders"
            :value-style="{ color: '#ffffff', fontSize: '28px', fontWeight: 600 }"
          />
          <a-statistic
            title="总销售额"
            :value="stats.revenue"
            prefix="¥"
            :precision="0"
            :value-style="{ color: '#ffffff', fontSize: '28px', fontWeight: 600 }"
          />
        </div>
      </section>

      <!-- AI 简介 -->
      <section style="background: #ffffff; padding: 48px 48px 32px; border-bottom: 1px solid #f0f0f0; margin: 0 -48px">
        <p style="font-size: 17px; color: #7a7a7a; line-height: 1.47; max-width: 680px; margin: 0 auto; text-align: center; letter-spacing: -0.022em">
          🤖 {{ merchant.persona_prompt }}
        </p>
      </section>

      <!-- 人群筛选标签 -->
      <section style="background: #f5f5f7; padding: 16px 48px; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin: 0 -48px">
        <button
          v-for="tab in DEMOGRAPHIC_TABS"
          :key="tab.key"
          @click="demographic = tab.key"
          :style="{
            background: demographic === tab.key ? '#0066cc' : '#ffffff',
            color: demographic === tab.key ? '#ffffff' : '#1d1d1f',
            border: demographic === tab.key ? 'none' : '1px solid #e0e0e0',
            borderRadius: '9999px',
            padding: '8px 18px',
            fontSize: '14px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            fontFamily: 'inherit',
          }"
        >
          {{ tab.label }}
        </button>
      </section>

      <!-- 商品网格 -->
      <section style="background: #f5f5f7; padding: 32px 48px 80px; margin: 0 -48px">
        <div style="max-width: 1440px; margin: 0 auto">
          <a-spin v-if="loading" style="display: block; text-align: center; padding: 80px" />
          <template v-else>
            <p style="font-size: 14px; color: #7a7a7a; margin-bottom: 24px; letter-spacing: -0.016em">
              共 {{ products.length }} 件商品
            </p>
            <div
              :style="{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: '24px',
              }"
            >
              <ProductCard v-for="p in products" :key="p.id" :product="p" />
            </div>
            <div
              v-if="products.length === 0"
              style="text-align: center; padding: 80px; color: #7a7a7a; font-size: 17px"
            >
              暂无该人群分类的商品
            </div>
          </template>
        </div>
      </section>
    </template>
  </div>
</template>
