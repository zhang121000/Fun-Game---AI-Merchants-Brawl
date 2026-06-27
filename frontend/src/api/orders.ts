import client from './client'

export function createOrder(customerId: number) {
  return client.post('/orders', null, { params: { customer_id: customerId } })
}

export function getOrders(customerId?: number) {
  return client.get('/orders', { params: { customer_id: customerId } })
}

export function getOrder(id: number) {
  return client.get(`/orders/${id}`)
}
