import client from './client'

export function getCart(customerId: number) {
  return client.get('/cart', { params: { customer_id: customerId } })
}

export function addToCart(customerId: number, productId: number, quantity = 1) {
  return client.post('/cart/items', { product_id: productId, quantity }, { params: { customer_id: customerId } })
}

export function updateCartItem(customerId: number, itemId: number, quantity: number) {
  return client.put(`/cart/items/${itemId}`, { quantity }, { params: { customer_id: customerId } })
}

export function removeCartItem(customerId: number, itemId: number) {
  return client.delete(`/cart/items/${itemId}`, { params: { customer_id: customerId } })
}
