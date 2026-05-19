import { useEffect, useState } from 'react'
import { Card, Tag, Button, Space, Statistic, message, Spin, Modal, Input, Empty, Alert } from 'antd'
import { CheckOutlined, CloseOutlined, ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons'
import client from '../api/client'

const { TextArea } = Input

interface Strategy {
  id: number; merchant_id: number; strategy_type: string; title: string;
  description: string; proposed_changes: Record<string, any>;
  status: string; ai_reasoning: string; admin_comment: string; created_at: string | null
}
interface Merchant { id: number; name: string; ai_model: string; main_category: string; brand_color: string }

const TYPE_LABELS: Record<string, string> = {
  price_adjustment: '调价', promotion: '促销活动',
  bundle: '捆绑销售', recommendation_update: '推荐更新',
}

export default function MarketingApproval() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [merchants, setMerchants] = useState<Merchant[]>([])
  const [loading, setLoading] = useState(true)
  const [commentModal, setCommentModal] = useState<{ id: number; action: 'approve' | 'reject' } | null>(null)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [genResult, setGenResult] = useState<string | null>(null)

  const merchantMap = Object.fromEntries(merchants.map(m => [m.id, m]))

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    const [sRes, mRes] = await Promise.all([
      client.get('/marketing/strategies'),
      client.get('/merchants'),
    ])
    setStrategies(sRes.data)
    setMerchants(mRes.data)
    setLoading(false)
  }

  async function handleAction() {
    if (!commentModal) return
    setSubmitting(true)
    try {
      const endpoint = commentModal.action === 'approve'
        ? `/marketing/strategies/${commentModal.id}/approve`
        : `/marketing/strategies/${commentModal.id}/reject`
      await client.post(endpoint, { comment })
      message.success(commentModal.action === 'approve' ? '已批准并执行' : '已驳回')
      setCommentModal(null); setComment(''); loadData()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '操作失败')
    } finally { setSubmitting(false) }
  }

  const [generating, setGenerating] = useState(false)

  async function triggerGeneration() {
    setGenerating(true)
    try {
      const res = await client.post('/admin/generate-strategies')
      const { auto_executed, pending_approval, results } = res.data
      const errorCount = results?.filter((r: any) => r.status === 'error').length || 0
      if (errorCount > 0 && auto_executed === 0 && pending_approval === 0) {
        message.warning(`生成完成，但有 ${errorCount} 个产品出错，请检查后端日志`)
      } else {
        setGenResult(`✅ 已生成：${auto_executed} 条自动执行，${pending_approval} 条待审批`)
      }
      loadData()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '触发失败，请检查 API Key 配置')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <div style={{ textAlign: 'center', padding: 200 }}><Spin size="large" /></div>

  const pending = strategies.filter(s => s.status === 'pending')
  const approved = strategies.filter(s => s.status === 'approved')

  return (
    <div style={{ maxWidth: 980, margin: '0 auto', padding: '48px 0' }}>

      {/* 标题区 */}
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <h1 style={{
          fontSize: 40, fontWeight: 600, color: '#1d1d1f',
          letterSpacing: 0, marginBottom: 8,
        }}>
          营销策略中心
        </h1>
        <p style={{ fontSize: 21, color: '#7a7a7a', letterSpacing: '0.011em' }}>
          AI 自动生成 · 小幅自动执行 · 大幅变更需审批
        </p>
      </div>

      {/* KPI 卡片 */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
        gap: 24, marginBottom: 32,
      }}>
        <div style={{
          background: '#ffffff', border: '1px solid #e0e0e0', borderRadius: 18,
          padding: 24, textAlign: 'center',
        }}>
          <div style={{ fontSize: 12, color: '#7a7a7a', marginBottom: 4 }}>待审批</div>
          <div style={{ fontSize: 28, fontWeight: 600, color: '#ff9f0a' }}>{pending.length}</div>
        </div>
        <div style={{
          background: '#ffffff', border: '1px solid #e0e0e0', borderRadius: 18,
          padding: 24, textAlign: 'center',
        }}>
          <div style={{ fontSize: 12, color: '#7a7a7a', marginBottom: 4 }}>已执行</div>
          <div style={{ fontSize: 28, fontWeight: 600, color: '#30d158' }}>{approved.length}</div>
        </div>
        <div style={{
          background: '#ffffff', border: '1px solid #e0e0e0', borderRadius: 18,
          padding: 24, textAlign: 'center',
        }}>
          <div style={{ fontSize: 12, color: '#7a7a7a', marginBottom: 4 }}>总策略</div>
          <div style={{ fontSize: 28, fontWeight: 600, color: '#1d1d1f' }}>{strategies.length}</div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 32, justifyContent: 'center' }}>
        <Button type="primary" icon={<ThunderboltOutlined />} onClick={triggerGeneration}
          loading={generating}
          style={{ height: 44, borderRadius: 9999, padding: '0 22px', fontSize: 17 }}>
          {generating ? 'AI 正在分析...' : '触发 AI 策略生成'}
        </Button>
        <Button icon={<ReloadOutlined />} onClick={loadData}
          style={{ height: 44, borderRadius: 9999, padding: '0 22px', fontSize: 17 }}>
          刷新
        </Button>
      </div>

      {genResult && (
        <Alert message={genResult} type="success" showIcon closable
          onClose={() => setGenResult(null)} style={{ marginBottom: 24, borderRadius: 11 }} />
      )}

      {/* 待审批策略列表 */}
      {pending.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: 80, color: '#7a7a7a',
          background: '#f5f5f7', borderRadius: 18,
        }}>
          <p style={{ fontSize: 21, fontWeight: 600, marginBottom: 8 }}>暂无待审批策略</p>
          <p style={{ fontSize: 17 }}>点击上方按钮触发 AI 生成新策略</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {pending.map(s => {
            const merchant = merchantMap[s.merchant_id]
            return (
              <div key={s.id} style={{
                background: '#ffffff', border: '1px solid #e0e0e0',
                borderRadius: 18, padding: 32,
                borderLeft: `4px solid ${merchant?.brand_color || '#0066cc'}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <Space style={{ marginBottom: 12 }}>
                      <Tag style={{ background: '#f5f5f7', border: 'none', borderRadius: 9999 }}>
                        {merchant?.name}
                      </Tag>
                      <Tag style={{ background: '#f5f5f7', border: 'none', borderRadius: 9999 }}>
                        {merchant?.main_category}
                      </Tag>
                      <Tag style={{ background: '#fff3e0', color: '#ff9f0a', border: 'none', borderRadius: 9999 }}>
                        ⚠️ 需审批
                      </Tag>
                    </Space>
                    <h3 style={{
                      fontSize: 21, fontWeight: 600, color: '#1d1d1f',
                      letterSpacing: '0.011em', marginBottom: 8,
                    }}>
                      {s.title}
                    </h3>
                    <p style={{ fontSize: 17, color: '#1d1d1f', lineHeight: 1.47, marginBottom: 16 }}>
                      {s.description}
                    </p>
                    <div style={{
                      background: '#f5f5f7', borderRadius: 11, padding: 16, marginBottom: 12,
                    }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: '#1d1d1f', marginBottom: 4 }}>
                        AI 决策理由
                      </div>
                      <div style={{ fontSize: 14, color: '#7a7a7a' }}>{s.ai_reasoning}</div>
                    </div>
                    {s.proposed_changes && Object.keys(s.proposed_changes).length > 0 && (
                      <div style={{
                        background: '#ffffff', border: '1px solid #e0e0e0',
                        borderRadius: 11, padding: 16,
                      }}>
                        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>变更内容</div>
                        <pre style={{
                          fontSize: 12, margin: 0, whiteSpace: 'pre-wrap',
                          color: '#7a7a7a', fontFamily: 'SF Mono, Menlo, monospace',
                        }}>
                          {JSON.stringify(s.proposed_changes, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginLeft: 16 }}>
                    <Button type="primary" icon={<CheckOutlined />}
                      onClick={() => setCommentModal({ id: s.id, action: 'approve' })}>
                      批准
                    </Button>
                    <Button icon={<CloseOutlined />}
                      onClick={() => setCommentModal({ id: s.id, action: 'reject' })}>
                      驳回
                    </Button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* 已执行历史 */}
      {approved.length > 0 && (
        <div style={{ marginTop: 48 }}>
          <h2 style={{
            fontSize: 28, fontWeight: 600, color: '#1d1d1f',
            letterSpacing: 0, marginBottom: 24,
          }}>
            已执行策略
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {approved.slice(0, 10).map(s => {
              const merchant = merchantMap[s.merchant_id]
              return (
                <div key={s.id} style={{
                  background: '#f5f5f7', borderRadius: 11, padding: '12px 16px',
                  display: 'flex', alignItems: 'center', gap: 12,
                }}>
                  <Tag style={{
                    background: '#ffffff', border: '1px solid #e0e0e0',
                    borderRadius: 9999, fontSize: 12,
                  }}>
                    {merchant?.name}
                  </Tag>
                  <span style={{ fontSize: 14, color: '#1d1d1f', flex: 1 }}>{s.title}</span>
                  <span style={{ fontSize: 12, color: '#30d158' }}>✓ 已执行</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

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
    </div>
  )
}
