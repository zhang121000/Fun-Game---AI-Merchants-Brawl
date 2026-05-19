import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Spin, Tag, Carousel } from 'antd'
import { ArrowRightOutlined, RobotOutlined, LineChartOutlined, ThunderboltOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons'
import { getProducts } from '../api/products'

const AI_LABELS: Record<string, { name: string; color: string; icon: string }> = {
  deepseek: { name: 'DeepSeek AI', color: '#1677ff', icon: '🔬' },
  gpt:      { name: 'GPT AI', color: '#722ed1', icon: '🌍' },
  doubao:   { name: '豆包 AI', color: '#ff4d4f', icon: '🔥' },
  mimo:     { name: 'MiMo AI', color: '#ff6600', icon: '🤖' },
  qwen:     { name: '通义千问 AI', color: '#52c41a', icon: '🍃' },
}

const TILE_BACKGROUNDS = [
  { bg: '#ffffff', color: '#1d1d1f', isDark: false },
  { bg: '#272729', color: '#ffffff', isDark: true },
  { bg: '#f5f5f7', color: '#1d1d1f', isDark: false },
  { bg: '#2a2a2c', color: '#ffffff', isDark: true },
  { bg: '#000000', color: '#ffffff', isDark: true },
]

interface Product {
  id: number; name: string; description: string;
  ai_model: string; category: string;
  price: number; original_price: number; stock: number;
  ai_selling_points: string[]
}

export default function Home() {
  const navigate = useNavigate()
  const carouselRef = useRef<any>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    const res = await getProducts({})
    setProducts(res.data)
    setLoading(false)
  }

  if (loading) return <div style={{ textAlign: 'center', padding: 200 }}><Spin size="large" /></div>

  return (
    <div style={{ margin: '0 -48px' }}>

      {/* Hero Tile */}
      <section style={{
        background: '#ffffff', padding: '80px 48px', textAlign: 'center',
      }}>
        <h1 style={{
          fontSize: 56, fontWeight: 600, color: '#1d1d1f',
          letterSpacing: '-0.016em', lineHeight: 1.07, marginBottom: 12,
        }}>
          AI 健康生活馆
        </h1>
        <p style={{
          fontSize: 28, fontWeight: 400, color: '#1d1d1f',
          letterSpacing: '0.007em', lineHeight: 1.14, marginBottom: 16,
        }}>
          5 款明星保健品，每款由独立 AI 专家智能管理
        </p>
        <p style={{
          fontSize: 17, color: '#7a7a7a', marginBottom: 32, letterSpacing: '-0.022em',
        }}>
          DeepSeek · GPT · 豆包 · MiMo · 通义千问 — 五大 AI 各展所长，自主优化定价、文案和经营策略
        </p>
        <div style={{
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          gap: 16, flexWrap: 'wrap',
        }}>
          <Button
            type="primary"
            size="large"
            icon={<ThunderboltOutlined />}
            className="hero-btn"
            onClick={() => navigate('/admin')}
          >
            电竞控制台
          </Button>
          <Button
            type="primary"
            size="large"
            icon={<LineChartOutlined />}
            className="hero-btn"
            onClick={() => navigate('/admin/analytics')}
          >
            查看数据看板
          </Button>
        </div>
      </section>

      {/* 5 个产品轮播 */}
      <div style={{ position: 'relative' }}>
        <Carousel
          ref={carouselRef}
          autoplay
          autoplaySpeed={4000}
          dots
          effect="scrollx"
          style={{ background: '#1d1d1f' }}
        >
        {products.map((product, i) => {
          const tile = TILE_BACKGROUNDS[i % TILE_BACKGROUNDS.length]
          const aiInfo = AI_LABELS[product.ai_model] || { name: product.ai_model, color: '#666', icon: '🤖' }
          const discount = product.original_price > product.price
            ? Math.round((1 - product.price / product.original_price) * 100) : 0
          const icons = ['💊', '🐟', '💪', '🦠', '✨']

          return (
            <div key={product.id}>
              <section style={{
                background: tile.bg, color: tile.color,
                padding: '80px 48px', minHeight: 420,
              }}>
                <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 80, flexWrap: 'wrap' }}>
                  {/* 产品图 */}
                  <div style={{
                    flex: '0 0 280px', height: 280,
                    background: tile.isDark ? 'rgba(255,255,255,0.06)' : '#f5f5f7',
                    borderRadius: 18, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 96,
                    boxShadow: 'rgba(0, 0, 0, 0.22) 3px 5px 30px 0',
                  }}>
                    {icons[i] || '💊'}
                  </div>

                  {/* 产品信息 */}
                  <div style={{ flex: 1, minWidth: 300 }}>
                    <div style={{ marginBottom: 16 }}>
                      <Tag style={{
                        background: tile.isDark ? 'rgba(255,255,255,0.12)' : '#f5f5f7',
                        color: tile.isDark ? '#cccccc' : '#7a7a7a',
                        border: 'none', borderRadius: 9999, padding: '4px 14px', fontSize: 14,
                      }}>
                        <RobotOutlined /> {aiInfo.name} 独立管理
                      </Tag>
                      <Tag style={{
                        background: tile.isDark ? 'rgba(255,255,255,0.08)' : '#f0f0f0',
                        color: tile.isDark ? '#cccccc' : '#7a7a7a',
                        border: 'none', borderRadius: 9999, padding: '4px 14px', fontSize: 14,
                      }}>
                        {product.category}
                      </Tag>
                      <Tag style={{
                        background: tile.isDark ? 'rgba(255,255,255,0.08)' : '#f0f0f0',
                        color: tile.isDark ? '#cccccc' : '#7a7a7a',
                        border: 'none', borderRadius: 9999, padding: '4px 14px', fontSize: 14,
                      }}>
                        库存 {product.stock}
                      </Tag>
                    </div>

                    <h2 style={{
                      fontSize: 40, fontWeight: 600, color: tile.color,
                      letterSpacing: 0, lineHeight: 1.1, marginBottom: 12,
                    }}>
                      {product.name}
                    </h2>

                    <p style={{
                      fontSize: 21, fontWeight: 400,
                      color: tile.isDark ? '#cccccc' : '#7a7a7a',
                      letterSpacing: '0.011em', lineHeight: 1.19, marginBottom: 20,
                    }}>
                      {product.description}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 24 }}>
                      <span style={{ fontSize: 28, fontWeight: 600, color: tile.color, letterSpacing: '-0.016em' }}>
                        ¥{product.price}
                      </span>
                      {discount > 0 && (
                        <>
                          <span style={{ fontSize: 17, color: tile.isDark ? '#7a7a7a' : '#a1a1a6', textDecoration: 'line-through' }}>
                            ¥{product.original_price}
                          </span>
                          <span style={{ fontSize: 14, color: '#0066cc', fontWeight: 600 }}>省 {discount}%</span>
                        </>
                      )}
                    </div>

                    <Button size="large"
                      style={{
                        fontSize: 17, fontWeight: 400, height: 48, padding: '0 24px', borderRadius: 9999,
                        borderColor: tile.isDark ? '#ffffff' : '#0066cc',
                        color: tile.isDark ? '#ffffff' : '#0066cc',
                      }}
                      onClick={() => navigate(`/product/${product.id}`)}>
                      查看 AI 策略详情 <ArrowRightOutlined />
                    </Button>
                  </div>
                </div>
              </section>
            </div>
          )
        })}
      </Carousel>

        {/* 左右切换箭头 */}
        <div
          onClick={() => carouselRef.current?.prev()}
          className="carousel-arrow carousel-arrow-left"
        >
          <LeftOutlined />
        </div>
        <div
          onClick={() => carouselRef.current?.next()}
          className="carousel-arrow carousel-arrow-right"
        >
          <RightOutlined />
        </div>

        <style>{`
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
          .hero-btn {
            font-size: 18px;
            font-weight: 300;
            height: 52px;
            padding: 0 28px;
            border-radius: 9999px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
          }
          .hero-btn:hover {
            transform: scale(1.03);
            box-shadow: 0 4px 16px rgba(24, 144, 255, 0.35);
          }
        `}</style>
      </div>

      {/* Footer */}
      <footer style={{
        background: '#f5f5f7', padding: '48px 48px 32px',
        borderTop: '1px solid #e0e0e0',
      }}>
        <div style={{ maxWidth: 980, margin: '0 auto', textAlign: 'center' }}>
          <p style={{ fontSize: 12, color: '#7a7a7a', marginBottom: 4 }}>
            AI 健康生活馆 · 商家后台 ©2026
          </p>
          <p style={{ fontSize: 12, color: '#a1a1a6' }}>
            每款产品由独立 AI 专家管理 — DeepSeek · GPT · 豆包 · MiMo · 通义千问
          </p>
        </div>
      </footer>
    </div>
  )
}
