import { useEffect, useState } from 'react'
import { Card, Typography, Button, List, InputNumber, Empty, message, Popconfirm, Space, Tag } from 'antd'
import { DeleteOutlined, ShoppingOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useCustomerStore } from '../stores/customerStore'
import { useCartStore } from '../stores/cartStore'
import { getProduct } from '../api/products'
import { createOrder } from '../api/orders'

const { Title, Text } = Typography

export default function Cart() {
  const navigate = useNavigate()
  const { current } = useCustomerStore()
  const { items, fetch, updateItem, removeItem, clear } = useCartStore()
  const [products, setProducts] = useState<Record<number, any>>({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (current) fetch(current.id)
  }, [current?.id])

  useEffect(() => {
    loadProducts()
  }, [items])

  async function loadProducts() {
    const map: Record<number, any> = {}
    for (const item of items) {
      if (!products[item.product_id]) {
        const res = await getProduct(item.product_id)
        map[item.product_id] = res.data
      }
    }
    setProducts((prev) => ({ ...prev, ...map }))
  }

  const total = items.reduce((sum, item) => {
    const p = products[item.product_id]
    return sum + (p ? p.price * item.quantity : 0)
  }, 0)

  async function handleCheckout() {
    if (!current || items.length === 0) return
    setSubmitting(true)
    try {
      await createOrder(current.id)
      clear()
      message.success('下单成功！')
      navigate('/orders')
    } catch {
      message.error('下单失败')
    }
    setSubmitting(false)
  }

  if (!current) return <Empty description="请先选择身份" />

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={3}>🛒 购物车</Title>
      {items.length === 0 ? (
        <Empty description="购物车是空的">
          <Button type="primary" onClick={() => navigate('/')}>去逛逛</Button>
        </Empty>
      ) : (
        <>
          <List
            dataSource={items}
            renderItem={(item) => {
              const p = products[item.product_id]
              return (
                <Card style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <Text strong>{p?.name || '加载中...'}</Text>
                      <div>
                        <Tag color="blue">{p?.category}</Tag>
                        <Text type="secondary" style={{ marginLeft: 8 }}>¥{p?.price}/件</Text>
                      </div>
                    </div>
                    <Space>
                      <InputNumber
                        min={1} max={p?.stock || 99}
                        value={item.quantity}
                        onChange={(v) => current && updateItem(current.id, item.id, v || 1)}
                        style={{ width: 80 }}
                      />
                      <Text strong style={{ color: '#ff4d4f', minWidth: 80, textAlign: 'right' }}>
                        ¥{p ? (p.price * item.quantity).toFixed(2) : '--'}
                      </Text>
                      <Popconfirm title="确定移除？" onConfirm={() => current && removeItem(current.id, item.id)}>
                        <Button danger icon={<DeleteOutlined />} />
                      </Popconfirm>
                    </Space>
                  </div>
                </Card>
              )
            }}
          />
          <Card style={{ marginTop: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>共 {items.reduce((s, i) => s + i.quantity, 0)} 件商品</Text>
              <Space>
                <Text>合计: <Text strong style={{ color: '#ff4d4f', fontSize: 24 }}>¥{total.toFixed(2)}</Text></Text>
                <Button type="primary" size="large" icon={<ShoppingOutlined />}
                  onClick={handleCheckout} loading={submitting}>
                  立即下单
                </Button>
              </Space>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
