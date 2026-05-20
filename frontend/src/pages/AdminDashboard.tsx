import { useEffect, useState } from 'react'
import {
  Button, Space, Spin, Tag, Modal, Input, Tooltip, Progress, Badge, Drawer, InputNumber,
} from 'antd'
import {
  ReloadOutlined, RocketOutlined,
  TrophyOutlined, BulbOutlined, WarningOutlined,
  CheckOutlined, CloseOutlined, ExperimentOutlined,
  RightOutlined, ArrowUpOutlined, ArrowDownOutlined, MinusOutlined,
  ShoppingCartOutlined,
} from '@ant-design/icons'
import client, { getMessageApi } from '../api/client'

const { TextArea } = Input

// ============ 类型定义 ============
interface Overview {
  total_orders: number; total_revenue: number; total_customers: number;
  total_merchants: number; total_products: number;
  current_day: number; pending_strategies: number
}

interface RankingItem {
  merchant_ai: string; category: string; product_name: string;
  rank: number; units_sold: number; revenue: number; price: number;
  promotion: string; target_focus: string; reasoning: string;
  traffic_received: number;
  history: { rank: number; units: number }[]
}

interface Suggestion {
  merchant_ai: string; category: string; type: string;
  message: string; advice: string
}

interface Strategy {
  id: number; merchant_id: number; strategy_type: string; title: string;
  description: string; proposed_changes: Record<string, any>;
  status: string; ai_reasoning: string; admin_comment: string; created_at: string | null
}

interface DecisionLogItem {
  merchant_ai: string; category: string; product_name: string;
  price: number; promotion: string; target_focus: string;
  description_update: string; reasoning: string;
  traffic_received: number; units_sold: number; revenue: number;
  rank: number; research_product: string
}

// ============ 常量 ============
const AI_COLORS: Record<string, string> = {
  GLM: '#6366f1', gpt: '#10b981', MiniMax: '#f59e0b',
  Kimi: '#ef4444', qwen: '#3b82f6',
}

const AI_LABELS: Record<string, string> = {
  GLM: 'GLM', gpt: 'GPT', MiniMax: 'MiniMax', Kimi: 'Kimi', qwen: '通义千问',
}

const DEMO_LABELS: Record<string, string> = {
  child: '儿童', youth: '青年', middle: '中年', elderly: '老年',
}

const TYPE_LABELS: Record<string, string> = {
  price_adjustment: '调价', promotion: '促销活动',
  bundle: '捆绑销售', recommendation_update: '推荐更新',
}

// ============ 主组件 ============
export default function AdminDashboard() {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [rankings, setRankings] = useState<RankingItem[]>([])
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [decisionLog, setDecisionLog] = useState<DecisionLogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [advancing, setAdvancing] = useState(false)
  const [commentModal, setCommentModal] = useState<{ id: number; action: 'approve' | 'reject' } | null>(null)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showDecisionLog, setShowDecisionLog] = useState(false)
  const [applePhase, setApplePhase] = useState<'idle' | 'rolling' | 'sprint' | 'done'>('idle')
  const [aiCompleted, setAiCompleted] = useState<string[]>([])
  const [restockDrawer, setRestockDrawer] = useState(false)
  const [productList, setProductList] = useState<any[]>([])
  const [restockAmounts, setRestockAmounts] = useState<Record<string, number>>({})

  useEffect(() => { loadAll() }, [])

  async function loadAll() {
    setLoading(true)
    try {
      const [ovRes, lbRes, sugRes, stRes] = await Promise.all([
        client.get('/admin/overview'),
        client.get('/admin/leaderboard'),
        client.get('/admin/platform-suggestions'),
        client.get('/marketing/strategies'),
      ])
      setOverview(ovRes.data)
      setRankings(lbRes.data.rankings || [])
      setSuggestions(sugRes.data.suggestions || [])
      setStrategies(stRes.data)
    } catch (e) {
      console.error('加载失败', e)
    }
    setLoading(false)
  }

  async function handleAdvanceDay() {
    setAdvancing(true)
    setApplePhase('rolling')
    setAiCompleted([])
    try {
      const startRes = await client.post('/admin/advance-day')
      if (startRes.data.status === 'running') {
        getMessageApi()?.info(startRes.data.message)
        setAdvancing(false)
        return
      }

      let attempts = 0
      const maxAttempts = 120

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1500))
        attempts++

        const statusRes = await client.get('/admin/advance-day-status')
        const status = statusRes.data

        // 更新AI完成列表（驱动苹果位置）
        const completed = status.ai_completed || []
        setAiCompleted(completed)

        if (!status.running && status.result) {
          setApplePhase('sprint')
          setAiCompleted(['GLM', 'gpt', 'MiniMax', 'Kimi', 'qwen'])
          await new Promise(resolve => setTimeout(resolve, 500))
          setApplePhase('done')
          const data = status.result
          getMessageApi()?.success(`第${data.day}天完成！${data.total_orders}笔订单，¥${data.total_revenue.toFixed(0)}收入`)
          loadAll()
          setTimeout(() => { setApplePhase('idle'); setAiCompleted([]) }, 800)
          break
        }
        if (!status.running && status.error) {
          setApplePhase('idle')
          getMessageApi()?.error(`模拟失败: ${status.error}`)
          break
        }
      }
      if (attempts >= maxAttempts) {
        setApplePhase('idle')
        getMessageApi()?.warning('模拟超时')
      }
    } catch (e: any) {
      setApplePhase('idle')
      getMessageApi()?.error(e.response?.data?.detail || '推进失败')
    }
    setAdvancing(false)
  }

  async function openRestockDrawer() {
    try {
      const res = await client.get('/products')
      setProductList(res.data)
      setRestockDrawer(true)
    } catch { getMessageApi()?.error('加载产品失败') }
  }

  async function doRestockAll() {
    for (const p of productList) {
      const amount = restockAmounts[p.ai_model] || 100
      if (amount > 0) {
        try { await client.post(`/admin/products/${p.id}/restock`, { amount }) } catch {}
      }
    }
    getMessageApi()?.success('全部进货成功！')
    setRestockDrawer(false)
    loadAll()
  }

  async function doRestock(productId: number, aiModel: string) {
    const amount = restockAmounts[aiModel] || 100
    if (amount < 1) return
    try {
      await client.post(`/admin/products/${productId}/restock`, { amount })
      getMessageApi()?.success(`${AI_LABELS[aiModel] || aiModel} +${amount}`)
      setRestockAmounts(prev => ({ ...prev, [aiModel]: 100 }))
      loadAll()
    } catch { getMessageApi()?.error('进货失败') }
  }

  async function handleAction() {
    if (!commentModal) return
    setSubmitting(true)
    try {
      const endpoint = commentModal.action === 'approve'
        ? `/marketing/strategies/${commentModal.id}/approve`
        : `/marketing/strategies/${commentModal.id}/reject`
      await client.post(endpoint, { comment })
      getMessageApi()?.success(commentModal.action === 'approve' ? '已批准' : '已驳回')
      setCommentModal(null); setComment(''); loadAll()
    } catch (e: any) {
      getMessageApi()?.error(e.response?.data?.detail || '操作失败')
    }
    setSubmitting(false)
  }

  async function loadDecisionLog() {
    try {
      const res = await client.get('/admin/decision-log')
      setDecisionLog(res.data.decisions || [])
      setShowDecisionLog(true)
    } catch {
      getMessageApi()?.error('加载决策日志失败')
    }
  }

  if (loading) return <div style={{ textAlign: 'center', padding: 200 }}><Spin size="large" /></div>

  const currentDay = overview?.current_day || 0
  const pendingStrategies = strategies.filter(s => s.status === 'pending')

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 24px' }}>

      {/* ===== 标题区 + 日期推进 ===== */}
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <h1 style={{ fontSize: 40, fontWeight: 600, color: '#1d1d1f', marginBottom: 8 }}>
          AI 竞争控制台
        </h1>
        <p style={{ fontSize: 21, color: '#7a7a7a', marginBottom: 24 }}>
          5个AI商家 · 4类人群 · 实时竞争
        </p>

        {/* 日期显示 + 推进按钮 */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 16,
          background: '#f5f5f7', borderRadius: 18, padding: '16px 32px',
        }}>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontSize: 12, color: '#7a7a7a' }}>模拟天数</div>
            <div style={{ fontSize: 36, fontWeight: 700, color: '#1d1d1f', lineHeight: 1 }}>
              第 {currentDay} 天
            </div>
          </div>
          <div style={{ width: 1, height: 48, background: '#e0e0e0' }} />
          <Button
            type="primary"
            icon={<RocketOutlined />}
            loading={advancing}
            onClick={handleAdvanceDay}
            style={{
              height: 52, borderRadius: 9999, padding: '0 28px',
              fontSize: 18, fontWeight: 600,
            }}
          >
            {advancing ? 'AI 正在竞争...' : '推进明天 →'}
          </Button>
        </div>

        {/* 苹果吃豆进度条 */}
        <div style={{
          width: 320, margin: '18px auto 0',
        }}>
          {/* 轨道 */}
          <div style={{
            height: 24, background: '#e8e8e8', borderRadius: 9999,
            position: 'relative', overflow: 'hidden',
            border: '1px solid #ddd',
          }}>
            {/* 草坪 — 苹果经过的部分变绿 */}
            {applePhase !== 'idle' && (
              <div style={{
                position: 'absolute', left: 0, top: 0, height: '100%',
                width: applePhase === 'done' ? '100%'
                  : `${Math.max(4, (aiCompleted.length) / 5 * 100)}%`,
                background: `
                  repeating-linear-gradient(
                    90deg, #7bc67e 0px, #7bc67e 4px,
                    #5aae5e 4px, #5aae5e 6px,
                    #8dd491 6px, #8dd491 8px
                  ),
                  linear-gradient(180deg, #6dbd70 0%, #4a9e4e 100%)
                `,
                borderRadius: 9999,
                transition: 'width 0.6s ease',
              }} />
            )}

            {/* 5个圆点 — 嵌在轨道内 */}
            {['GLM', 'gpt', 'MiniMax', 'Kimi', 'qwen'].map((ai, i) => {
              const eaten = aiCompleted.includes(ai)
              if (eaten) return null
              return (
                <div key={ai} style={{
                  position: 'absolute',
                  left: `calc(${20 + i * 15}% - 5px)`,
                  top: '50%', marginTop: -5,
                  width: 10, height: 10, borderRadius: 5,
                  background: AI_COLORS[ai],
                  boxShadow: `0 0 4px ${AI_COLORS[ai]}`,
                  zIndex: 2,
                  transition: 'opacity 0.2s',
                }} />
              )
            })}

            {/* 苹果 */}
            <span style={{
              position: 'absolute',
              left: applePhase === 'idle' ? 3
                : applePhase === 'done' ? 'calc(100% - 26px)'
                : `calc(${Math.max(4, (aiCompleted.length) / 5 * 100)}% - 12px)`,
              top: 0, fontSize: 22, lineHeight: '24px',
              zIndex: 3,
              transition: 'left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
              animation: applePhase === 'rolling' || applePhase === 'sprint'
                ? 'appleSpin 0.7s linear infinite'
                : applePhase === 'done' ? 'appleWiggle 0.3s ease' : 'none',
              filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.15))',
            }}>🍎</span>
          </div>
        </div>

        <style>{`
          @keyframes appleSpin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-360deg); }
          }
          @keyframes appleWiggle {
            0%, 100% { transform: rotate(0deg) scale(1); }
            50% { transform: rotate(-12deg) scale(1.25); }
          }
        `}</style>
      </div>

      {/* ===== KPI 卡片 ===== */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)',
        gap: 16, marginBottom: 32,
      }}>
        {[
          { label: '总订单', value: overview?.total_orders || 0, color: '#1d1d1f' },
          { label: '总销售额', value: `¥${(overview?.total_revenue || 0).toFixed(0)}`, color: '#1d1d1f' },
          { label: '今日订单', value: rankings.reduce((s, r) => s + r.units_sold, 0), color: '#30d158' },
          { label: '待审批策略', value: overview?.pending_strategies || 0, color: '#ff9f0a' },
          { label: '活跃商家', value: rankings.length || 5, color: '#0066cc' },
        ].map(s => (
          <div key={s.label} style={{
            background: '#fff', border: '1px solid #e0e0e0',
            borderRadius: 14, padding: 18, textAlign: 'center',
          }}>
            <div style={{ fontSize: 11, color: '#7a7a7a', marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* ===== 操作按钮 ===== */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 32, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Button icon={<BulbOutlined />} onClick={loadDecisionLog}
          style={{ height: 40, borderRadius: 9999, padding: '0 20px' }}>
          查看今日决策
        </Button>
        <Button icon={<ReloadOutlined />} onClick={loadAll}
          style={{ height: 40, borderRadius: 9999, padding: '0 20px' }}>
          刷新
        </Button>
        <Button
          danger
          icon={<WarningOutlined />}
          onClick={async () => {
            if (confirm('确认重置？将清除所有模拟数据，天数归零，库存恢复初始值。此操作不可撤销。')) {
              await client.post('/admin/reset')
              getMessageApi()?.success('已重置')
              loadAll()
            }
          }}
          style={{ height: 40, borderRadius: 9999, padding: '0 20px' }}>
          ⚠️ 一键重置
        </Button>
        <Button
          icon={<ShoppingCartOutlined />}
          onClick={openRestockDrawer}
          style={{ height: 40, borderRadius: 9999, padding: '0 20px' }}>
          📦 进货管理
        </Button>
      </div>

      {/* ===== 平台建议 ===== */}
      {suggestions.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <BulbOutlined style={{ color: '#ff9f0a' }} /> 平台建议
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {suggestions.map((s, i) => (
              <div key={i} style={{
                background: s.type === 'alert' ? '#fef2f2' : s.type === 'warning' ? '#fffbeb' : '#f0f9ff',
                border: `1px solid ${s.type === 'alert' ? '#fecaca' : s.type === 'warning' ? '#fde68a' : '#bfdbfe'}`,
                borderRadius: 11, padding: '12px 16px',
                display: 'flex', alignItems: 'center', gap: 12,
              }}>
                <Tag style={{
                  background: AI_COLORS[s.merchant_ai] || '#666',
                  color: '#fff', border: 'none', borderRadius: 9999,
                }}>
                  {AI_LABELS[s.merchant_ai] || s.merchant_ai}
                </Tag>
                <span style={{ fontSize: 14, color: '#1d1d1f', flex: 1 }}>
                  {s.message}
                  {s.advice && <span style={{ color: '#7a7a7a', marginLeft: 8 }}>{s.advice}</span>}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ===== AI 商家排行榜 ===== */}
      {rankings.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrophyOutlined style={{ color: '#f59e0b' }} /> AI 商家排行榜
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {rankings.map((r, i) => {
              const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}`
              const trendIcon = r.history.length >= 2
                ? r.history[r.history.length - 1].rank < r.history[r.history.length - 2].rank
                  ? <ArrowUpOutlined style={{ color: '#30d158' }} />
                  : r.history[r.history.length - 1].rank > r.history[r.history.length - 2].rank
                    ? <ArrowDownOutlined style={{ color: '#ff3b30' }} />
                    : <MinusOutlined style={{ color: '#7a7a7a' }} />
                : null

              return (
                <div key={r.merchant_ai} style={{
                  background: '#fff', border: '1px solid #e0e0e0',
                  borderRadius: 14, padding: '16px 20px',
                  display: 'flex', alignItems: 'center', gap: 16,
                  borderLeft: `4px solid ${AI_COLORS[r.merchant_ai] || '#666'}`,
                }}>
                  {/* 排名 */}
                  <div style={{
                    width: 40, textAlign: 'center', fontSize: i < 3 ? 24 : 18,
                    fontWeight: 700, color: i < 3 ? '#1d1d1f' : '#7a7a7a',
                  }}>
                    {medal}
                  </div>

                  {/* 商家信息 */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, fontSize: 16, color: '#1d1d1f' }}>
                        {AI_LABELS[r.merchant_ai] || r.merchant_ai}
                      </span>
                      <Tag style={{
                        background: '#f5f5f7', border: 'none', borderRadius: 9999,
                        fontSize: 12, margin: 0,
                      }}>
                        {r.category}
                      </Tag>
                      {trendIcon}
                    </div>
                    <div style={{ fontSize: 13, color: '#7a7a7a' }}>
                      {r.promotion ? `🎯 ${r.promotion}` : '无促销'} ·
                      重点: {DEMO_LABELS[r.target_focus] || r.target_focus} ·
                      流量: {r.traffic_received}
                    </div>
                  </div>

                  {/* 数据 */}
                  <div style={{ display: 'flex', gap: 24, textAlign: 'center' }}>
                    <div>
                      <div style={{ fontSize: 11, color: '#7a7a7a' }}>销量</div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: '#1d1d1f' }}>{r.units_sold}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, color: '#7a7a7a' }}>收入</div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: '#30d158' }}>¥{r.revenue.toFixed(0)}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, color: '#7a7a7a' }}>定价</div>
                      <div style={{ fontSize: 20, fontWeight: 600, color: '#1d1d1f' }}>¥{r.price}</div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ===== 决策因果链（弹窗） ===== */}
      <Modal
        title={`第 ${overview?.current_day || 0} 天 — 决策因果链`}
        open={showDecisionLog}
        onCancel={() => setShowDecisionLog(false)}
        footer={null}
        width={800}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {decisionLog.map((d, i) => (
            <div key={i} style={{
              background: '#f5f5f7', borderRadius: 11, padding: 16,
              borderLeft: `3px solid ${AI_COLORS[d.merchant_ai] || '#666'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Tag style={{
                    background: AI_COLORS[d.merchant_ai] || '#666',
                    color: '#fff', border: 'none', borderRadius: 9999,
                  }}>
                    {AI_LABELS[d.merchant_ai]}
                  </Tag>
                  <span style={{ fontWeight: 600 }}>{d.product_name}</span>
                  <span style={{ fontSize: 12, color: '#7a7a7a' }}>第{d.rank}名</span>
                </div>
                <div style={{ fontSize: 14, color: '#7a7a7a' }}>
                  {d.units_sold}件 · ¥{d.revenue.toFixed(0)}
                </div>
              </div>
              <div style={{ fontSize: 13, color: '#1d1d1f', lineHeight: 1.6 }}>
                <strong>决策：</strong>定价¥{d.price}
                {d.promotion && ` | 促销: ${d.promotion}`}
                {` | 重点人群: ${DEMO_LABELS[d.target_focus] || d.target_focus}`}
              </div>
              <div style={{ fontSize: 13, color: '#7a7a7a', marginTop: 4 }}>
                <strong>理由：</strong>{d.reasoning}
              </div>
              {d.research_product && (
                <div style={{ fontSize: 13, color: '#6366f1', marginTop: 4 }}>
                  🔬 正在研发：{d.research_product}
                </div>
              )}
            </div>
          ))}
        </div>
      </Modal>

      {/* ===== 待审批策略 ===== */}
      {pendingStrategies.length > 0 && (
        <div style={{ marginTop: 48 }}>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 16 }}>
            待审批策略
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {pendingStrategies.map(s => (
              <div key={s.id} style={{
                background: '#fff', border: '1px solid #e0e0e0',
                borderRadius: 14, padding: 20,
                display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                    <Tag style={{ background: '#fff3e0', color: '#ff9f0a', border: 'none', borderRadius: 9999 }}>
                      {TYPE_LABELS[s.strategy_type] || s.strategy_type}
                    </Tag>
                    <Tag style={{ background: '#fff3e0', color: '#ff9f0a', border: 'none', borderRadius: 9999 }}>
                      ⚠️ 需审批
                    </Tag>
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{s.title}</h3>
                  <p style={{ fontSize: 14, color: '#1d1d1f', marginBottom: 8 }}>{s.description}</p>
                  <div style={{ background: '#f5f5f7', borderRadius: 8, padding: 10, fontSize: 12, color: '#7a7a7a' }}>
                    <strong>AI理由：</strong>{s.ai_reasoning}
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginLeft: 16 }}>
                  <Button type="primary" size="small" icon={<CheckOutlined />}
                    onClick={() => setCommentModal({ id: s.id, action: 'approve' })}>
                    批准
                  </Button>
                  <Button size="small" icon={<CloseOutlined />}
                    onClick={() => setCommentModal({ id: s.id, action: 'reject' })}>
                    驳回
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ===== 空状态 ===== */}
      {rankings.length === 0 && (
        <div style={{
          textAlign: 'center', padding: 80, color: '#7a7a7a',
          background: '#f5f5f7', borderRadius: 18,
        }}>
          <RocketOutlined style={{ fontSize: 48, marginBottom: 16, color: '#d0d0d0' }} />
          <p style={{ fontSize: 21, fontWeight: 600, marginBottom: 8 }}>尚未开始模拟</p>
          <p style={{ fontSize: 17 }}>点击「推进明天」开始第一天的AI竞争</p>
        </div>
      )}

      {/* ===== 审批弹窗 ===== */}
      <Modal
        title={commentModal?.action === 'approve' ? '批准策略' : '驳回策略'}
        open={!!commentModal}
        onOk={handleAction}
        onCancel={() => { setCommentModal(null); setComment('') }}
        confirmLoading={submitting}
        okText={commentModal?.action === 'approve' ? '确认批准' : '确认驳回'}
        okButtonProps={{ danger: commentModal?.action === 'reject' }}
      >
        <TextArea rows={3} placeholder="输入批注（可选）..." value={comment}
          onChange={e => setComment(e.target.value)} />
      </Modal>

      {/* ===== 进货抽屉 ===== */}
      <Drawer
        title="📦 进货管理"
        open={restockDrawer}
        onClose={() => setRestockDrawer(false)}
        width={420}
      >
        {productList.map((p: any) => (
          <div key={p.id} style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '14px 0', borderBottom: '1px solid #f0f0f0',
          }}>
            <span style={{
              width: 10, height: 10, borderRadius: 5,
              background: AI_COLORS[p.ai_model] || '#999',
              flexShrink: 0,
            }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{p.name}</div>
              <div style={{ fontSize: 12, color: '#7a7a7a' }}>
                {AI_LABELS[p.ai_model] || p.ai_model} · {p.category} · 当前库存 <b>{p.stock}</b>
              </div>
            </div>
            <InputNumber
              min={1} max={99999}
              value={restockAmounts[p.ai_model] || 100}
              onChange={v => setRestockAmounts(prev => ({ ...prev, [p.ai_model]: v || 0 }))}
              style={{ width: 80 }}
            />
            <Button
              type="primary" size="small"
              style={{ borderRadius: 9999 }}
              onClick={() => doRestock(p.id, p.ai_model)}
            >
              进货
            </Button>
          </div>
        ))}
        <div style={{ marginTop: 24, textAlign: 'right' }}>
          <Button type="primary" onClick={doRestockAll} style={{ borderRadius: 9999 }}>
            一键全部进货
          </Button>
        </div>
      </Drawer>
    </div>
  )
}
