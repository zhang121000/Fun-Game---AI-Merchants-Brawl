import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { AntDesignVueResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')

  return {
    plugins: [
      vue(),
      Components({
        resolvers: [
          AntDesignVueResolver({
            importStyle: false,
          }),
        ],
      }),
    ],
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules/vue-echarts')) {
              return 'vue-echarts'
            }

            if (id.includes('node_modules/echarts')) {
              return 'echarts'
            }

            if (id.includes('node_modules/zrender')) {
              return 'zrender'
            }

            if (
              id.includes('node_modules/vue/') ||
              id.includes('node_modules/vue-router/') ||
              id.includes('node_modules/pinia/')
            ) {
              return 'vue-vendor'
            }
          },
        },
      },
    },
    server: {
      port: 5174,
      proxy: {
        '/api': env.VITE_BACKEND_URL || 'http://localhost:8000',
      },
    },
  }
})
