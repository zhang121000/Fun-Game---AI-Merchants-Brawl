<script setup lang="ts">
import { ref, computed, h, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { DeleteOutlined, ShoppingOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useCustomerStore } from '../stores/customer'
import { useCartStore } from '../stores/cart'
import { getProduct } from '../api/products'
import { createOrder } from '../api/orders'

const router = useRouter()
const customerStore = useCustomerStore()
const cartStore = useCartStore()

const products = ref<Record<number, any>>({})
const submitting = ref(false)

const current = computed(() => customerStore.current)
const items = computed(() => cartStore.items)

watch(() => current.value?.id, (id) => {
  if (id) cartStore.fetch(id)
})

watch(() => items.value, () => {
  loadProducts()
})

async function loadProducts() {
  const map: Record<number, any> = {}
  for (const item of items.value) {
    if (!products.value[item.product_id]) {
      const res = await getProduct(item.product_id)
      map[item.product_id] = res.data
    }
  }
  products.value = { ...products.value, ...map }
}

const total = computed(() =>
  items.value.reduce((sum, item) => {
    const p = products.value[item.product_id]
    return sum + (p ? p.price * item.quantity : 0)
  }, 0)
)

const totalQuantity = computed(() =>
  items.value.reduce((s, i) => s + i.quantity, 0)
)

async function handleCheckout() {
  if (!current.value || items.value.length === 0) return
  submitting.value = true
  try {
    await createOrder(current.value.id)
    cartStore.clear()
    message.success('下单成功！')
    router.push('/orders')
  } catch {
    message.error('下单失败')
  }
  submitting.value = false
}

onMounted(() => {
  if (current.value) cartStore.fetch(current.value.id)
})
</script>

<template>
  <div style="max-width: 800px; margin: 0 auto; padding: 48px 0">
    <h3 style="font-size: 21px; font-weight: 600; margin-bottom: 24px">🛒 购物车</h3>

    <a-empty v-if="!current" description="请先选择身份" />

    <template v-else-if="items.length === 0">
      <a-empty description="购物车是空的">
        <a-button type="primary" @click="router.push('/')">去逛逛</a-button>
      </a-empty>
    </template>

    <template v-else>
      <a-card
        v-for="item in items"
        :key="item.id"
        style="margin-bottom: 12px"
      >
        <div style="display: flex; justify-content: space-between; align-items: center">
          <div>
            <div style="font-weight: 600; margin-bottom: 4px">
              {{ products[item.product_id]?.name || '加载中...' }}
            </div>
            <div>
              <a-tag color="blue">{{ products[item.product_id]?.category }}</a-tag>
              <span style="margin-left: 8px; color: #7a7a7a; font-size: 14px">
                ¥{{ products[item.product_id]?.price }}/件
              </span>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 12px">
            <a-input-number
              :min="1"
              :max="products[item.product_id]?.stock || 99"
              :value="item.quantity"
              @change="(v: number | null) => current && cartStore.updateItem(current.id, item.id, v || 1)"
              style="width: 80px"
            />
            <span style="font-weight: 600; color: #ff4d4f; min-width: 80px; text-align: right">
              ¥{{ products[item.product_id] ? (products[item.product_id].price * item.quantity).toFixed(2) : '--' }}
            </span>
            <a-popconfirm
              title="确定移除？"
              @confirm="current && cartStore.removeItem(current.id, item.id)"
            >
              <a-button danger :icon="h(DeleteOutlined)" />
            </a-popconfirm>
          </div>
        </div>
      </a-card>

      <a-card style="margin-top: 16px">
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>共 {{ totalQuantity }} 件商品</span>
          <div style="display: flex; align-items: center; gap: 16px">
            <span>
              合计:
              <span style="font-weight: 600; color: #ff4d4f; font-size: 24px">¥{{ total.toFixed(2) }}</span>
            </span>
            <a-button
              type="primary"
              size="large"
              @click="handleCheckout"
              :loading="submitting"
            >
              <ShoppingOutlined /> 立即下单
            </a-button>
          </div>
        </div>
      </a-card>
    </template>
  </div>
</template>
