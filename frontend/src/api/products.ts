import client from './client'

export function getProducts(params?: {
  demographic?: string
  category?: string
  merchant_id?: number
  sort?: string
}) {
  return client.get('/products', { params })
}

export function getProduct(id: number) {
  return client.get(`/products/${id}`)
}
