import client from './client'

export const createOrder = (customerId: number) =>
  client.post('/orders', null, { params: { customer_id: customerId } })

export const getOrders = (customerId?: number) =>
  client.get('/orders', { params: { customer_id: customerId } })

export const getOrder = (id: number) => client.get(`/orders/${id}`)
