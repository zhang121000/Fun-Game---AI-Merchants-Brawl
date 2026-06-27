<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { RobotOutlined } from '@ant-design/icons-vue'

const AI_LABELS: Record<string, string> = {
  GLM: 'GLM', gpt: 'GPT', MiniMax: 'MiniMax', Kimi: 'Kimi', qwen: '通义千问',
}
const AI_COLORS: Record<string, string> = {
  GLM: '#1677ff', gpt: '#722ed1', MiniMax: '#ff4d4f', Kimi: '#ff6600', qwen: '#52c41a',
}

interface Product {
  id: number
  name: string
  description: string
  ai_model: string
  category: string
  price: number
  original_price: number
  stock: number
}

const props = defineProps<{ product: Product }>()
const router = useRouter()

const discount = computed(() =>
  props.product.original_price > props.product.price
    ? Math.round((1 - props.product.price / props.product.original_price) * 100)
    : 0
)

const aiColor = computed(() => AI_COLORS[props.product.ai_model] || '#666')
const aiLabel = computed(() => AI_LABELS[props.product.ai_model] || props.product.ai_model)

function goToDetail() {
  router.push(`/product/${props.product.id}`)
}
</script>

<template>
  <div class="product-card" @click="goToDetail">
    <div class="product-image">
      💊
    </div>

    <div class="product-tags">
      <a-tag :style="{ background: aiColor + '15', color: aiColor, border: 'none', borderRadius: '9999px', fontSize: '12px', padding: '2px 10px' }">
        <RobotOutlined /> {{ aiLabel }}
      </a-tag>
      <a-tag :style="{ background: '#f5f5f7', color: '#7a7a7a', border: 'none', borderRadius: '9999px', fontSize: '12px', padding: '2px 10px' }">
        {{ product.category }}
      </a-tag>
    </div>

    <h3 class="product-name">{{ product.name }}</h3>

    <p class="product-desc">{{ product.description }}</p>

    <div class="product-footer">
      <span class="product-price">¥{{ product.price }}</span>
      <template v-if="discount > 0">
        <span class="product-original-price">¥{{ product.original_price }}</span>
        <span class="product-discount">省{{ discount }}%</span>
      </template>
      <span class="product-stock">库存 {{ product.stock }}</span>
    </div>
  </div>
</template>

<style scoped>
.product-card {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 18px;
  padding: 24px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.product-card:hover {
  border-color: #0066cc;
}

.product-image {
  height: 160px;
  background: #f5f5f7;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56px;
  margin-bottom: 20px;
  box-shadow: rgba(0, 0, 0, 0.22) 3px 5px 30px 0;
}

.product-tags {
  margin-bottom: 8px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.product-name {
  font-size: 17px;
  font-weight: 600;
  color: #1d1d1f;
  letter-spacing: -0.022em;
  line-height: 1.24;
  margin-bottom: 4px;
}

.product-desc {
  font-size: 14px;
  color: #7a7a7a;
  line-height: 1.43;
  letter-spacing: -0.016em;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}

.product-footer {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.product-price {
  font-size: 21px;
  font-weight: 600;
  color: #1d1d1f;
  letter-spacing: -0.016em;
}

.product-original-price {
  font-size: 14px;
  color: #7a7a7a;
  text-decoration: line-through;
}

.product-discount {
  font-size: 12px;
  color: #0066cc;
  font-weight: 600;
}

.product-stock {
  margin-left: auto;
  font-size: 12px;
  color: #7a7a7a;
}
</style>
