<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useCustomerStore } from '../stores/customer'
import { getOrders } from '../api/orders'

const customerStore = useCustomerStore()
const orders = ref<any[]>([])
const loading = ref(true)

const current = computed(() => customerStore.current)

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: '待支付', color: 'orange' },
  paid: { label: '已支付', color: 'blue' },
  shipped: { label: '已发货', color: 'cyan' },
  completed: { label: '已完成', color: 'green' },
  cancelled: { label: '已取消', color: 'default' },
}

watch(() => current.value?.id, (id) => {
  if (id) {
    loading.value = true
    getOrders(id).then((res) => {
      orders.value = res.data
      loading.value = false
    })
  }
}, { immediate: true })
</script>

<template>
  <div style="max-width: 800px; margin: 0 auto; padding: 48px 0">
    <h3 style="font-size: 21px; font-weight: 600; margin-bottom: 24px">📦 我的订单</h3>

    <a-empty v-if="!current" description="请先选择身份" />

    <a-spin v-else-if="loading" style="display: block; text-align: center; padding: 60px" />

    <a-empty v-else-if="orders.length === 0" description="暂无订单" />

    <template v-else>
      <a-card
        v-for="order in orders"
        :key="order.id"
        style="margin-bottom: 12px"
      >
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px">
          <span>订单号: {{ order.id }}</span>
          <a-tag :color="STATUS_MAP[order.status]?.color || 'default'">
            {{ STATUS_MAP[order.status]?.label || order.status }}
          </a-tag>
        </div>
        <div
          v-for="item in order.items"
          :key="item.id"
          style="display: flex; justify-content: space-between; padding: 4px 0"
        >
          <span>商品#{{ item.product_id }} × {{ item.quantity }}</span>
          <span>¥{{ (item.unit_price * item.quantity).toFixed(2) }}</span>
        </div>
        <div style="text-align: right; margin-top: 8px">
          <span style="font-weight: 600; color: #ff4d4f; font-size: 16px">
            合计: ¥{{ order.total_amount }}
          </span>
        </div>
      </a-card>
    </template>
  </div>
</template>
