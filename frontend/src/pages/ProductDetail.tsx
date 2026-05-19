import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Tag, Button, Spin, Space } from 'antd'
import { ArrowLeftOutlined, RobotOutlined } from '@ant-design/icons'
import { getProduct } from '../api/products'
import client from '../api/client'

const AI_LABELS: Record<string, string> = {
  GLM: 'GLM', gpt: 'GPT', MiniMax: 'MiniMax', Kimi: 'Kimi', qwen: '通义千问',
}
const AI_COLORS: Record<string, string> = {
  GLM: '#1677ff', gpt: '#722ed1', MiniMax: '#ff4d4f', Kimi: '#ff6600', qwen: '#52c41a',
}
const DEMO_LABELS: Record<string, string> = {
  elderly: '老年人', female: '女性', male: '男性', child: '儿童',
}

export default function ProductDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState<any>(null)
  const [demoBreakdown, setDemoBreakdown] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [id])

  async function loadData() {
    setLoading(true)
    try {
      const [pRes, dRes] = await Promise.all([
        getProduct(Number(id)),
        client.get(`/analytics/product/${id}/demographic-breakdown`),
      ])
      setProduct(pRes.data)
      setDemoBreakdown(dRes.data)
    } catch {
      const pRes = await getProduct(Number(id))
      setProduct(pRes.data)
    }
    setLoading(false)
  }

  if (loading || !product) return <div style={{ textAlign: 'center', padding: 200 }}><Spin size="large" /></div>

  const discount = product.original_price > product.price
    ? Math.round((1 - product.price / product.original_price) * 100) : 0
  const aiColor = AI_COLORS[product.ai_model] || '#666'
  const strategyHistory = product.ai_strategy_history || []

  return (
    <div style={{ margin: '0 -48px' }}>
      {/* Hero */}
      <section style={{
        background: '#272729', color: '#ffffff', padding: '60px 48px',
      }}>
        <div style={{ maxWidth: 980, margin: '0 auto' }}>
          <Button type="text" icon={<ArrowLeftOutlined />}
            style={{ color: '#a1a1a6', marginBottom: 24, fontSize: 14 }}
            onClick={() => navigate('/')}>
            返回产品总览
          </Button>
          <div style={{ display: 'flex', gap: 48, flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{
              flex: '0 0 240px', height: 240,
              background: 'rgba(255,255,255,0.06)', borderRadius: 18,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 80,
              boxShadow: 'rgba(0, 0, 0, 0.22) 3px 5px 30px 0',
            }}>
              💊
            </div>
            <div style={{ flex: 1 }}>
              <Space style={{ marginBottom: 12 }}>
                <Tag style={{
                  background: aiColor + '25', color: aiColor,
                  border: 'none', borderRadius: 9999, padding: '4px 14px',
                }}>
                  <RobotOutlined /> {AI_LABELS[product.ai_model]} AI 独立管理
                </Tag>
                <Tag style={{
                  background: 'rgba(255,255,255,0.12)', color: '#cccccc',
                  border: 'none', borderRadius: 9999, padding: '4px 14px',
                }}>
                  {product.category}
                </Tag>
              </Space>
              <h1 style={{
                fontSize: 40, fontWeight: 600, color: '#ffffff',
                letterSpacing: 0, lineHeight: 1.1, marginBottom: 12,
              }}>
                {product.name}
              </h1>
              <p style={{ fontSize: 17, color: '#cccccc', lineHeight: 1.47, marginBottom: 20 }}>
                {product.description}
              </p>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 16 }}>
                <span style={{ fontSize: 28, fontWeight: 600 }}>¥{product.price}</span>
                {discount > 0 && (
                  <>
                    <span style={{ fontSize: 17, color: '#7a7a7a', textDecoration: 'line-through' }}>¥{product.original_price}</span>
                    <span style={{ fontSize: 14, color: '#2997ff', fontWeight: 600 }}>省 {discount}%</span>
                  </>
                )}
              </div>
              <div style={{ display: 'flex', gap: 24, fontSize: 14, color: '#7a7a7a' }}>
                <span>库存：{product.stock}</span>
                <span>AI 模型：{AI_LABELS[product.ai_model]}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* AI 策略历史 + 人群分布 */}
      <section style={{ background: '#f5f5f7', padding: '48px 48px 80px' }}>
        <div style={{ maxWidth: 980, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32 }}>
            {/* AI 策略历史 */}
            <div style={{
              background: '#ffffff', border: '1px solid #e0e0e0',
              borderRadius: 18, padding: 32,
            }}>
              <h2 style={{ fontSize: 21, fontWeight: 600, marginBottom: 24 }}>
                🤖 AI 策略历史
              </h2>
              {strategyHistory.length === 0 ? (
                <p style={{ color: '#7a7a7a', fontSize: 17 }}>暂无策略记录，请先触发 AI 策略生成</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {strategyHistory.map((s: any, i: number) => (
                    <div key={i} style={{
                      background: '#f5f5f7', borderRadius: 11, padding: '12px 16px',
                      display: 'flex', alignItems: 'center', gap: 12,
                    }}>
                      <span style={{ fontSize: 12, color: '#7a7a7a', whiteSpace: 'nowrap' }}>
                        {s.time?.slice(0, 16).replace('T', ' ')}
                      </span>
                      <span style={{ fontSize: 14, color: '#1d1d1f', flex: 1 }}>{s.title}</span>
                      <Tag style={{
                        background: s.auto_executed ? '#d4edda' : '#fff3e0',
                        color: s.auto_executed ? '#30d158' : '#ff9f0a',
                        border: 'none', borderRadius: 9999, fontSize: 11,
                      }}>
                        {s.auto_executed ? '自动执行' : '需审批'}
                      </Tag>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 购买人群分布 */}
            <div style={{
              background: '#ffffff', border: '1px solid #e0e0e0',
              borderRadius: 18, padding: 32,
            }}>
              <h2 style={{ fontSize: 21, fontWeight: 600, marginBottom: 24 }}>
                👥 购买人群分布
              </h2>
              {demoBreakdown.length === 0 ? (
                <p style={{ color: '#7a7a7a', fontSize: 17 }}>暂无购买数据，请先运行模拟</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {demoBreakdown.map((d: any) => {
                    const total = demoBreakdown.reduce((s: number, x: any) => s + x.count, 0)
                    const pct = total > 0 ? (d.count / total * 100) : 0
                    return (
                      <div key={d.demographic}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                          <span style={{ fontSize: 14, fontWeight: 600 }}>{DEMO_LABELS[d.demographic] || d.demographic}</span>
                          <span style={{ fontSize: 14, color: '#7a7a7a' }}>{d.count}单 · ¥{d.revenue.toFixed(0)}</span>
                        </div>
                        <div style={{ height: 8, background: '#f0f0f0', borderRadius: 4, overflow: 'hidden' }}>
                          <div style={{
                            height: '100%', width: `${pct}%`,
                            background: '#0066cc', borderRadius: 4,
                            transition: 'width 0.3s',
                          }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
