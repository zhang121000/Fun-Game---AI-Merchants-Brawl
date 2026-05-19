import client from './client'

export const getProducts = (params?: {
  demographic?: string; category?: string; merchant_id?: number; sort?: string
}) => client.get('/products', { params })

export const getProduct = (id: number) => client.get(`/products/${id}`)
