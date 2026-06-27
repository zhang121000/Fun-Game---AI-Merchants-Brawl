import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('../pages/Home.vue'),
    },
    {
      path: '/product/:id',
      name: 'ProductDetail',
      component: () => import('../pages/ProductDetail.vue'),
    },
    {
      path: '/shop/:id',
      name: 'MerchantShop',
      component: () => import('../pages/MerchantShop.vue'),
    },
    {
      path: '/cart',
      name: 'Cart',
      component: () => import('../pages/Cart.vue'),
    },
    {
      path: '/orders',
      name: 'OrderHistory',
      component: () => import('../pages/OrderHistory.vue'),
    },
    {
      path: '/admin',
      name: 'AdminDashboard',
      component: () => import('../pages/AdminDashboard.vue'),
    },
    {
      path: '/admin/analytics',
      name: 'AnalyticsBoard',
      component: () => import('../pages/AnalyticsBoard.vue'),
    },
    {
      path: '/admin/marketing',
      name: 'MarketingApproval',
      component: () => import('../pages/MarketingApproval.vue'),
    },
  ],
})

export default router
