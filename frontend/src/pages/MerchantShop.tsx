import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Tag, Spin, Space, Statistic } from 'antd'
import { RiseOutlined, RobotOutlined } from '@ant-design/icons'
import { getMerchant, getMerchantProducts } from '../api/merchants'
import { useCustomerStore } from '../stores/customerStore'
import ProductCard from '../components/product/ProductCard'
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

export default function MerchantShop() {
  const { id } = useParams()
  const merchantId = Number(id)
  const [merchant, setMerchant] = useState<any>(null)
  const [products, setProducts] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [demographic, setDemographic] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadMerchant(); loadStats() }, [merchantId])
  useEffect(() => { loadProducts() }, [merchantId, demographic])

  async function loadMerchant() {
    const res = await getMerchant(merchantId)
    setMerchant(res.data)
  }

  async function loadProducts() {
    setLoading(true)
    const res = await getMerchantProducts(merchantId, demographic || undefined)
    setProducts(res.data)
    setLoading(false)
  }

  async function loadStats() {
    try {
      const res = await client.get('/admin/leaderboard')
      const rankings = res.data.rankings || []
      setStats({
        orders: rankings.reduce((sum: number, r: any) => sum + (r.units_sold || 0), 0),
        revenue: rankings.reduce((sum: number, r: any) => sum + (r.revenue || 0), 0),
      })
    } catch { /* */ }
  }

  if (!merchant) return <div style={{ textAlign: 'center', padding: 200 }}><Spin size="large" /></div>

  return (
    <div style={{ margin: '0 -48px' }}>

      {/* Hero Section — 深色瓷砖 */}
      <section style={{
        background: '#272729', color: '#ffffff',
        padding: '80px 48px', textAlign: 'center',
      }}>
        <RobotOutlined style={{ fontSize: 48, color: '#2997ff', display: 'block', marginBottom: 16 }} />
        <h1 style={{
          fontSize: 40, fontWeight: 600, color: '#ffffff',
          letterSpacing: 0, lineHeight: 1.1, marginBottom: 8,
        }}>
          {merchant.name}
        </h1>
        <p style={{
          fontSize: 21, fontWeight: 600, color: '#cccccc',
          letterSpacing: '0.011em', marginBottom: 16,
        }}>
          {merchant.main_category}专营 · {MODEL_LABELS[merchant.ai_model]} AI 驱动
        </p>
        {stats && (
          <Space size="large" style={{ marginTop: 24 }}>
            <Statistic
              title={<span style={{ color: '#7a7a7a', fontSize: 12 }}>总订单</span>}
              value={stats.orders}
              valueStyle={{ color: '#ffffff', fontSize: 28, fontWeight: 600 }}
            />
            <Statistic
              title={<span style={{ color: '#7a7a7a', fontSize: 12 }}>总销售额</span>}
              value={stats.revenue}
              prefix="¥"
              precision={0}
              valueStyle={{ color: '#ffffff', fontSize: 28, fontWeight: 600 }}
            />
          </Space>
        )}
      </section>

      {/* AI 简介 — 白色瓷砖 */}
      <section style={{
        background: '#ffffff', padding: '48px 48px 32px',
        borderBottom: '1px solid #f0f0f0',
      }}>
        <p style={{
          fontSize: 17, color: '#7a7a7a', lineHeight: 1.47,
          maxWidth: 680, margin: '0 auto', textAlign: 'center',
          letterSpacing: '-0.022em',
        }}>
          🤖 {merchant.persona_prompt}
        </p>
      </section>

      {/* 人群筛选标签 — 羊皮纸 */}
      <section style={{
        background: '#f5f5f7', padding: '16px 48px',
        display: 'flex', gap: 12, justifyContent: 'center',
        flexWrap: 'wrap',
      }}>
        {DEMOGRAPHIC_TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setDemographic(tab.key)}
            style={{
              background: demographic === tab.key ? '#0066cc' : '#ffffff',
              color: demographic === tab.key ? '#ffffff' : '#1d1d1f',
              border: demographic === tab.key ? 'none' : '1px solid #e0e0e0',
              borderRadius: 9999, padding: '8px 18px',
              fontSize: 14, cursor: 'pointer',
              transition: 'all 0.2s',
              fontFamily: 'inherit',
            }}
          >
            {tab.label}
          </button>
        ))}
      </section>

      {/* 商品网格 — 羊皮纸底 */}
      <section style={{ background: '#f5f5f7', padding: '32px 48px 80px' }}>
        <div style={{ maxWidth: 1440, margin: '0 auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 80 }}><Spin /></div>
          ) : (
            <>
              <p style={{
                fontSize: 14, color: '#7a7a7a', marginBottom: 24,
                letterSpacing: '-0.016em',
              }}>
                共 {products.length} 件商品
              </p>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: 24,
              }}>
                {products.map((p: any) => (
                  <ProductCard key={p.id} product={p} />
                ))}
              </div>
              {products.length === 0 && (
                <div style={{
                  textAlign: 'center', padding: 80, color: '#7a7a7a',
                  fontSize: 17,
                }}>
                  暂无该人群分类的商品
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  )
}
