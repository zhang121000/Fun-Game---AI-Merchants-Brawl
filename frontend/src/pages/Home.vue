<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRightOutlined, RobotOutlined, LineChartOutlined, ThunderboltOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons-vue'
import { getProducts } from '../api/products'

const AI_LABELS: Record<string, { name: string; color: string; icon: string }> = {
  GLM: { name: 'DeepSeek AI', color: '#1677ff', icon: '🔬' },
  gpt: { name: 'GPT AI', color: '#722ed1', icon: '🌍' },
  MiniMax: { name: '豆包 AI', color: '#ff4d4f', icon: '🔥' },
  Kimi: { name: 'Kimi AI', color: '#ff6600', icon: '🤖' },
  qwen: { name: '通义千问 AI', color: '#52c41a', icon: '🍃' },
}

const TILE_BACKGROUNDS = [
  { bg: '#ffffff', color: '#1d1d1f', isDark: false },
  { bg: '#272729', color: '#ffffff', isDark: true },
  { bg: '#f5f5f7', color: '#1d1d1f', isDark: false },
  { bg: '#2a2a2c', color: '#ffffff', isDark: true },
  { bg: '#000000', color: '#ffffff', isDark: true },
]

interface Product {
  id: number
  name: string
  description: string
  ai_model: string
  category: string
  price: number
  original_price: number
  stock: number
  ai_selling_points: string[]
}

const router = useRouter()
const products = ref<Product[]>([])
const loading = ref(true)
const carouselRef = ref<any>(null)

const icons = ['💊', '🐟', '💪', '🦠', '✨']

onMounted(async () => {
  loading.value = true
  const res = await getProducts({})
  products.value = res.data
  loading.value = false
})

function prevSlide() {
  carouselRef.value?.prev()
}

function nextSlide() {
  carouselRef.value?.next()
}
</script>

<template>
  <div>
    <a-spin v-if="loading" size="large" style="display: block; text-align: center; padding: 200px" />

    <template v-else>
      <!-- Hero Tile -->
      <section class="hero-section">
        <h1 class="hero-title">AI 健康生活馆</h1>
        <p class="hero-subtitle">5 款明星保健品，每款由独立 AI 专家智能管理</p>
        <p class="hero-desc">
          GLM · GPT · MiniMax · Kimi · 通义千问 — 五大 AI 各展所长，自主优化定价、文案和经营策略
        </p>
        <div class="hero-buttons">
          <a-button type="primary" size="large" class="hero-btn" @click="router.push('/admin')">
            <ThunderboltOutlined /> 电竞控制台
          </a-button>
          <a-button type="primary" size="large" class="hero-btn" @click="router.push('/admin/analytics')">
            <LineChartOutlined /> 查看数据看板
          </a-button>
        </div>
      </section>

      <!-- 5 个产品轮播 -->
      <div class="carousel-wrapper">
        <a-carousel ref="carouselRef" autoplay :autoplay-speed="4000" dots effect="scrollx">
          <template v-for="(product, i) in products" :key="product.id">
            <div>
              <section
                :style="{
                  background: TILE_BACKGROUNDS[i % 5].bg,
                  color: TILE_BACKGROUNDS[i % 5].color,
                  padding: '80px 48px',
                  minHeight: '420px',
                }"
              >
                <div style="max-width: 1200px; margin: 0 auto; display: flex; align-items: center; gap: 80px; flex-wrap: wrap">
                  <!-- 产品图 -->
                  <div
                    :style="{
                      flex: '0 0 280px',
                      height: '280px',
                      background: TILE_BACKGROUNDS[i % 5].isDark ? 'rgba(255,255,255,0.06)' : '#f5f5f7',
                      borderRadius: '18px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '96px',
                      boxShadow: 'rgba(0, 0, 0, 0.22) 3px 5px 30px 0',
                    }"
                  >
                    {{ icons[i] || '💊' }}
                  </div>

                  <!-- 产品信息 -->
                  <div style="flex: 1; min-width: 300px">
                    <div style="margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap">
                      <a-tag
                        :style="{
                          background: TILE_BACKGROUNDS[i % 5].isDark ? 'rgba(255,255,255,0.12)' : '#f5f5f7',
                          color: TILE_BACKGROUNDS[i % 5].isDark ? '#cccccc' : '#7a7a7a',
                          border: 'none',
                          borderRadius: '9999px',
                          padding: '4px 14px',
                          fontSize: '14px',
                        }"
                      >
                        <RobotOutlined /> {{ AI_LABELS[product.ai_model]?.name || product.ai_model }} 独立管理
                      </a-tag>
                      <a-tag
                        :style="{
                          background: TILE_BACKGROUNDS[i % 5].isDark ? 'rgba(255,255,255,0.08)' : '#f0f0f0',
                          color: TILE_BACKGROUNDS[i % 5].isDark ? '#cccccc' : '#7a7a7a',
                          border: 'none',
                          borderRadius: '9999px',
                          padding: '4px 14px',
                          fontSize: '14px',
                        }"
                      >
                        {{ product.category }}
                      </a-tag>
                      <a-tag
                        :style="{
                          background: TILE_BACKGROUNDS[i % 5].isDark ? 'rgba(255,255,255,0.08)' : '#f0f0f0',
                          color: TILE_BACKGROUNDS[i % 5].isDark ? '#cccccc' : '#7a7a7a',
                          border: 'none',
                          borderRadius: '9999px',
                          padding: '4px 14px',
                          fontSize: '14px',
                        }"
                      >
                        库存 {{ product.stock }}
                      </a-tag>
                    </div>

                    <h2
                      :style="{
                        fontSize: '40px',
                        fontWeight: 600,
                        color: TILE_BACKGROUNDS[i % 5].color,
                        letterSpacing: 0,
                        lineHeight: 1.1,
                        marginBottom: '12px',
                      }"
                    >
                      {{ product.name }}
                    </h2>

                    <p
                      :style="{
                        fontSize: '21px',
                        fontWeight: 400,
                        color: TILE_BACKGROUNDS[i % 5].isDark ? '#cccccc' : '#7a7a7a',
                        letterSpacing: '0.011em',
                        lineHeight: 1.19,
                        marginBottom: '20px',
                      }"
                    >
                      {{ product.description }}
                    </p>

                    <div style="display: flex; align-items: baseline; gap: 12px; margin-bottom: 24px">
                      <span
                        :style="{
                          fontSize: '28px',
                          fontWeight: 600,
                          color: TILE_BACKGROUNDS[i % 5].color,
                          letterSpacing: '-0.016em',
                        }"
                      >
                        ¥{{ product.price }}
                      </span>
                      <template v-if="product.original_price > product.price">
                        <span
                          :style="{
                            fontSize: '17px',
                            color: TILE_BACKGROUNDS[i % 5].isDark ? '#7a7a7a' : '#a1a1a6',
                            textDecoration: 'line-through',
                          }"
                        >
                          ¥{{ product.original_price }}
                        </span>
                        <span style="font-size: 14px; color: #0066cc; font-weight: 600">
                          省 {{ Math.round((1 - product.price / product.original_price) * 100) }}%
                        </span>
                      </template>
                    </div>

                    <a-button
                      size="large"
                      :style="{
                        fontSize: '17px',
                        fontWeight: 400,
                        height: '48px',
                        padding: '0 24px',
                        borderRadius: '9999px',
                        borderColor: TILE_BACKGROUNDS[i % 5].isDark ? '#ffffff' : '#0066cc',
                        color: TILE_BACKGROUNDS[i % 5].isDark ? '#ffffff' : '#0066cc',
                      }"
                      @click="router.push(`/product/${product.id}`)"
                    >
                      查看 AI 策略详情 <ArrowRightOutlined />
                    </a-button>
                  </div>
                </div>
              </section>
            </div>
          </template>
        </a-carousel>

        <!-- 左右切换箭头 -->
        <div class="carousel-arrow carousel-arrow-left" @click="prevSlide">
          <LeftOutlined />
        </div>
        <div class="carousel-arrow carousel-arrow-right" @click="nextSlide">
          <RightOutlined />
        </div>
      </div>

      <!-- Footer -->
      <footer class="site-footer">
        <div style="max-width: 980px; margin: 0 auto; text-align: center">
          <p style="font-size: 12px; color: #7a7a7a; margin-bottom: 4px">
            AI 健康生活馆 · 商家后台 ©2026
          </p>
          <p style="font-size: 12px; color: #a1a1a6">
            每款产品由独立 AI 专家管理 — GLM · GPT · MiniMax · Kimi · 通义千问
          </p>
        </div>
      </footer>
    </template>
  </div>
</template>

<style scoped>
.hero-section {
  background: #ffffff;
  padding: 80px 48px;
  text-align: center;
  margin: 0 -48px;
}

.hero-title {
  font-size: 56px;
  font-weight: 600;
  color: #1d1d1f;
  letter-spacing: -0.016em;
  line-height: 1.07;
  margin-bottom: 12px;
}

.hero-subtitle {
  font-size: 28px;
  font-weight: 400;
  color: #1d1d1f;
  letter-spacing: 0.007em;
  line-height: 1.14;
  margin-bottom: 16px;
}

.hero-desc {
  font-size: 17px;
  color: #7a7a7a;
  margin-bottom: 32px;
  letter-spacing: -0.022em;
}

.hero-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-btn {
  font-size: 18px !important;
  font-weight: 300 !important;
  height: 52px !important;
  padding: 0 28px !important;
  border-radius: 9999px !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hero-btn:hover {
  transform: scale(1.03);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.35);
}

.carousel-wrapper {
  position: relative;
  margin: 0 -48px;
}

.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  z-index: 10;
  transition: transform 0.2s ease, background 0.2s ease;
  user-select: none;
}

.carousel-arrow-left { left: 20px; }
.carousel-arrow-right { right: 20px; }

.carousel-arrow:hover {
  transform: translateY(-50%) scale(1.3);
  background: rgba(0, 0, 0, 0.55);
}

.site-footer {
  background: #f5f5f7;
  padding: 48px 48px 32px;
  border-top: 1px solid #e0e0e0;
  margin: 0 -48px;
}
</style>
