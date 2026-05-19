import client from './client'

export const getCart = (customerId: number) =>
  client.get('/cart', { params: { customer_id: customerId } })

export const addToCart = (customerId: number, productId: number, quantity = 1) =>
  client.post('/cart/items', { product_id: productId, quantity }, { params: { customer_id: customerId } })

export const updateCartItem = (customerId: number, itemId: number, quantity: number) =>
  client.put(`/cart/items/${itemId}`, { quantity }, { params: { customer_id: customerId } })

export const removeCartItem = (customerId: number, itemId: number) =>
  client.delete(`/cart/items/${itemId}`, { params: { customer_id: customerId } })
