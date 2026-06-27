<script setup lang="ts">
import AppHeader from './components/layout/AppHeader.vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import { appleTheme } from './composables/useAppleTheme'
</script>

<template>
  <a-config-provider :locale="zhCN" :theme="appleTheme">
    <a-layout style="min-height: 100vh; background: #ffffff">
      <AppHeader />
      <a-layout-content style="padding: 0 48px; background: #ffffff">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-config-provider>
</template>
