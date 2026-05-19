import { useEffect, useState } from 'react'
import { Card, Typography, Tag, List, Empty, Descriptions, Spin } from 'antd'
import { useCustomerStore } from '../stores/customerStore'
import { getOrders } from '../api/orders'

const { Title, Text } = Typography

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: '待支付', color: 'orange' },
  paid: { label: '已支付', color: 'blue' },
  shipped: { label: '已发货', color: 'cyan' },
  completed: { label: '已完成', color: 'green' },
  cancelled: { label: '已取消', color: 'default' },
}

export default function OrderHistory() {
  const { current } = useCustomerStore()
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (current) {
      setLoading(true)
      getOrders(current.id).then((res) => {
        setOrders(res.data)
        setLoading(false)
      })
    }
  }, [current?.id])

  if (!current) return <Empty description="请先选择身份" />
  if (loading) return <div style={{ textAlign: 'center', padding: 60 }}><Spin /></div>

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={3}>📦 我的订单</Title>
      {orders.length === 0 ? (
        <Empty description="暂无订单" />
      ) : (
        <List
          dataSource={orders}
          renderItem={(order: any) => {
            const st = STATUS_MAP[order.status] || { label: order.status, color: 'default' }
            return (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <Text>订单号: {order.id}</Text>
                  <Tag color={st.color}>{st.label}</Tag>
                </div>
                {order.items?.map((item: any) => (
                  <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                    <Text>商品#{item.product_id} × {item.quantity}</Text>
                    <Text>¥{(item.unit_price * item.quantity).toFixed(2)}</Text>
                  </div>
                ))}
                <div style={{ textAlign: 'right', marginTop: 8 }}>
                  <Text strong style={{ color: '#ff4d4f', fontSize: 16 }}>
                    合计: ¥{order.total_amount}
                  </Text>
                </div>
              </Card>
            )
          }}
        />
      )}
    </div>
  )
}
