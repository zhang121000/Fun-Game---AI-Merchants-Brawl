import { useEffect, useState } from 'react'
import { Typography, Spin, Select, Tag, Space, Tabs } from 'antd'
import ReactECharts from 'echarts-for-react'
import client from '../api/client'

const { Option } = Select

const AI_LABELS: Record<string, string> = {
  deepseek: 'DeepSeek', gpt: 'GPT', doubao: '豆包', mimo: 'MiMo', qwen: '通义千问',
}
const AI_COLORS: Record<string, string> = {
  deepseek: '#6366f1', gpt: '#10b981', doubao: '#f59e0b', mimo: '#ef4444', qwen: '#3b82f6',
}
const DEMO_LABELS: Record<string, string> = {
  elderly: '老年', youth: '青年', middle: '中年', child: '儿童',
}
const DEMO_COLORS: Record<string, string> = {
  elderly: '#fa541c', youth: '#2f54eb', middle: '#722ed1', child: '#52c41a',
}
const CATEGORY_COLORS: Record<string, string> = {
  '蛋白粉': '#6366f1', '维生素': '#10b981', '钙片': '#f59e0b',
  '益生菌': '#ef4444', '鱼油': '#3b82f6',
}

interface SalesTrendPoint { date: string; orders: number; revenue: number }
interface DemoDist { demographic: string; count: number; revenue: number }
interface ProductCompare {
  product_id: number; product_name: string; ai_model: string;
  category: string; orders: number; units_sold: number; revenue: number
}

export default function AnalyticsBoard() {
  const [trendData, setTrendData] = useState<{ days: number[]; series: Record<string, number[]> }>({ days: [], series: {} })
  const [dimension, setDimension] = useState<string>('ai')
  const [demoDist, setDemoDist] = useState<DemoDist[]>([])
  const [products, setProducts] = useState<ProductCompare[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [dimension])

  async function loadData() {
    setLoading(true)
    try {
      const [tRes, dRes, pRes] = await Promise.all([
        client.get(`/analytics/sales-trend?dimension=${dimension}`),
        client.get('/analytics/demographic-dist'),
        client.get('/analytics/product-compare'),
      ])
      setTrendData(tRes.data)
      setDemoDist(dRes.data)
      setProducts(pRes.data)
    } catch { /* */ }
    setLoading(false)
  }

  // 计算趋势图的系列
  const allDays = trendData.days || []
  const trendSeries = Object.entries(trendData.series || {}).map(([key, values]) => {
    const colorMap: Record<string, string> = {
      ...AI_COLORS, ...DEMO_COLORS, ...CATEGORY_COLORS,
    }
    return {
      name: AI_LABELS[key] || DEMO_LABELS[key] || key,
      type: 'line' as const,
      data: values,
      smooth: true,
      lineStyle: { width: 2 },
      itemStyle: { color: colorMap[key] || '#999' },
      symbol: 'circle',
      symbolSize: 6,
    }
  })

  const totalRevenue = products.reduce((s, p) => s + p.revenue, 0)
  const totalOrders = products.reduce((s, p) => s + p.orders, 0)
  const totalUnits = products.reduce((s, p) => s + p.units_sold, 0)
  const avgOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0

  // 销售趋势图
  const trendOption = {
    tooltip: { trigger: 'axis' as const },
    legend: { data: trendSeries.map(s => s.name), bottom: 0 },
    grid: { top: 20, bottom: 50, left: 50, right: 30 },
    xAxis: {
      type: 'category' as const,
      data: allDays.map(d => `第${d}天`),
      axisLine: { lineStyle: { color: '#e0e0e0' } },
    },
    yAxis: {
      type: 'value' as const, name: '销量(件)',
      splitLine: { lineStyle: { color: '#f0f0f0' } },
    },
    series: trendSeries,
  }

  const DIM_TABS = [
    { key: 'ai', label: '按 AI 商家' },
    { key: 'category', label: '按品类' },
    { key: 'demographic', label: '按人群' },
  ]

  // 人群购买饼图
  const pieOption = {
    tooltip: { trigger: 'item' as const },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '70%'],
      data: demoDist.map(d => ({
        name: DEMO_LABELS[d.demographic] || d.demographic, value: d.count,
        itemStyle: { color: DEMO_COLORS[d.demographic] },
      })),
      label: { formatter: '{b}\n{d}%', fontSize: 12 },
    }],
  }

  // 产品 AI 对比柱状图
  const productBarOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { top: 20, bottom: 40, left: 100, right: 20 },
    xAxis: { type: 'value' as const, name: '销售额(元)', splitLine: { lineStyle: { color: '#f0f0f0' } } },
    yAxis: {
      type: 'category' as const,
      data: products.map(p => `${p.product_name}`),
      axisLabel: { width: 120, overflow: 'truncate' },
    },
    series: [{
      type: 'bar',
      data: products.map(p => ({
        value: p.revenue,
        itemStyle: { color: AI_COLORS[p.ai_model] || '#0066cc', borderRadius: [0, 4, 4, 0] },
      })),
      label: { show: true, position: 'right', formatter: '¥{c}', fontSize: 12 },
    }],
  }

  if (loading) return <div style={{ textAlign: 'center', padding: 200 }}><Spin size="large" /></div>

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 0' }}>

      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <h1 style={{ fontSize: 40, fontWeight: 600, letterSpacing: 0, marginBottom: 8 }}>数据看板</h1>
        <p style={{ fontSize: 21, color: '#7a7a7a' }}>5 款产品 · 5 个 AI · 实时销售洞察</p>
      </div>

      {/* 时间筛选 — 用 tabs 代替 */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Tabs
          activeKey={dimension}
          onChange={setDimension}
          centered
          items={DIM_TABS}
          style={{ marginBottom: 0 }}
        />
      </div>

      {/* KPI */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 24, marginBottom: 48,
      }}>
        {[
          { label: '总销售额', value: `¥${totalRevenue.toFixed(0)}` },
          { label: '总订单量', value: String(totalOrders) },
          { label: '平均客单价', value: `¥${avgOrderValue.toFixed(0)}` },
        ].map(s => (
          <div key={s.label} style={{
            background: '#ffffff', border: '1px solid #e0e0e0',
            borderRadius: 18, padding: 24, textAlign: 'center',
          }}>
            <div style={{ fontSize: 12, color: '#7a7a7a', marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontSize: 28, fontWeight: 600, color: '#1d1d1f' }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* 销售趋势 */}
      <div style={{
        background: '#ffffff', border: '1px solid #e0e0e0',
        borderRadius: 18, padding: 32, marginBottom: 32,
      }}>
        <h2 style={{ fontSize: 21, fontWeight: 600, marginBottom: 16 }}>
          销售趋势 · {DIM_TABS.find(t => t.key === dimension)?.label || dimension}
        </h2>
        {allDays.length > 0
          ? <ReactECharts option={trendOption} style={{ height: 350 }} />
          : <div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#7a7a7a' }}>
              暂无数据，请先启动模拟
            </div>
        }
      </div>

      {/* 两列：人群分布 + 产品对比 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, marginBottom: 32 }}>
        {/* 人群购买分布 */}
        <div style={{
          background: '#ffffff', border: '1px solid #e0e0e0',
          borderRadius: 18, padding: 32,
        }}>
          <h2 style={{ fontSize: 21, fontWeight: 600, marginBottom: 16 }}>购买人群分布</h2>
          {demoDist.length > 0
            ? <ReactECharts option={pieOption} style={{ height: 300 }} />
            : <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#7a7a7a' }}>暂无数据</div>
          }
        </div>

        {/* 产品 AI 对比 */}
        <div style={{
          background: '#ffffff', border: '1px solid #e0e0e0',
          borderRadius: 18, padding: 32,
        }}>
          <h2 style={{ fontSize: 21, fontWeight: 600, marginBottom: 16 }}>产品 AI 经营对比</h2>
          {products.length > 0
            ? <ReactECharts option={productBarOption} style={{ height: 300 }} />
            : <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#7a7a7a' }}>暂无数据</div>
          }
        </div>
      </div>

      {/* 产品明细表 */}
      <div style={{
        background: '#ffffff', border: '1px solid #e0e0e0',
        borderRadius: 18, padding: 32,
      }}>
        <h2 style={{ fontSize: 21, fontWeight: 600, marginBottom: 24 }}>产品明细</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 17 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
              <th style={{ textAlign: 'left', padding: '12px 0', color: '#7a7a7a', fontWeight: 400, fontSize: 14 }}>产品</th>
              <th style={{ textAlign: 'left', padding: '12px 0', color: '#7a7a7a', fontWeight: 400, fontSize: 14 }}>AI 管理</th>
              <th style={{ textAlign: 'left', padding: '12px 0', color: '#7a7a7a', fontWeight: 400, fontSize: 14 }}>品类</th>
              <th style={{ textAlign: 'right', padding: '12px 0', color: '#7a7a7a', fontWeight: 400, fontSize: 14 }}>销量</th>
              <th style={{ textAlign: 'right', padding: '12px 0', color: '#7a7a7a', fontWeight: 400, fontSize: 14 }}>销售额</th>
            </tr>
          </thead>
          <tbody>
            {products.map(p => (
              <tr key={p.product_id} style={{ borderBottom: '1px solid #f5f5f7' }}>
                <td style={{ padding: '12px 0', fontWeight: 600 }}>{p.product_name}</td>
                <td style={{ padding: '12px 0' }}>
                  <Tag style={{
                    background: AI_COLORS[p.ai_model] + '15', color: AI_COLORS[p.ai_model],
                    border: 'none', borderRadius: 9999, fontSize: 12,
                  }}>
                    {AI_LABELS[p.ai_model] || p.ai_model}
                  </Tag>
                </td>
                <td style={{ padding: '12px 0', color: '#7a7a7a' }}>{p.category}</td>
                <td style={{ padding: '12px 0', textAlign: 'right' }}>{p.units_sold}</td>
                <td style={{ padding: '12px 0', textAlign: 'right', fontWeight: 600 }}>¥{p.revenue.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
