<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navLinks = [
  { path: '/', label: '产品总览' },
  { path: '/admin', label: 'AI 竞争控制台' },
  { path: '/admin/analytics', label: '数据看板' },
]

const pageTitle = computed(() => {
  const p = route.path
  if (p === '/') return '产品总览'
  if (p === '/admin') return 'AI 竞争控制台'
  if (p === '/admin/analytics') return '数据看板'
  if (p.startsWith('/product/')) return '产品详情'
  if (p.startsWith('/shop/')) return '商家店铺'
  if (p === '/cart') return '购物车'
  if (p === '/orders') return '我的订单'
  if (p === '/admin/marketing') return '营销策略审批'
  return ''
})
</script>

<template>
  <div>
    <!-- Global Nav — 纯黑顶栏 44px -->
    <nav class="global-nav">
      <router-link to="/" class="brand-link">
        AI 健康生活馆
      </router-link>
      <div class="nav-links">
        <router-link
          v-for="link in navLinks"
          :key="link.path"
          :to="link.path"
          class="nav-link"
          :class="{ active: route.path === link.path }"
        >
          {{ link.label }}
        </router-link>
      </div>
      <router-link to="/shop/1" class="shop-link">商家后台</router-link>
    </nav>

    <!-- Sub Nav — 磨砂副导航 52px -->
    <div class="sub-nav">
      <span class="sub-nav-title">{{ pageTitle }}</span>
    </div>
  </div>
</template>

<style scoped>
.global-nav {
  height: 44px;
  background: #000000;
  display: flex;
  align-items: center;
  padding: 0 48px;
  gap: 24px;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.brand-link {
  font-size: 18px;
  font-weight: 600;
  color: #f5f5f7;
  letter-spacing: -0.01em;
  margin-right: 32px;
  white-space: nowrap;
}

.nav-links {
  display: flex;
  gap: 24px;
  flex: 1;
  overflow-x: auto;
  scrollbar-width: none;
}

.nav-link {
  font-size: 12px;
  color: #a1a1a6;
  font-weight: 400;
  letter-spacing: -0.01em;
  transition: color 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.nav-link.active {
  color: #ffffff;
}

.shop-link {
  font-size: 12px;
  color: #7a7a7a;
  white-space: nowrap;
  flex-shrink: 0;
}

.sub-nav {
  height: 52px;
  background: rgba(245, 245, 247, 0.8);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  display: flex;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid #e0e0e0;
  position: sticky;
  top: 44px;
  z-index: 999;
}

.sub-nav-title {
  font-size: 21px;
  font-weight: 600;
  color: #1d1d1f;
  letter-spacing: 0.011em;
}
</style>
