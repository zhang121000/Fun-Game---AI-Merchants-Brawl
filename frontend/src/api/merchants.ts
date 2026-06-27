import client from './client'

export function getMerchants() {
  return client.get('/merchants')
}

export function getMerchant(id: number) {
  return client.get(`/merchants/${id}`)
}

export function getMerchantProducts(id: number, demographic?: string) {
  return client.get(`/merchants/${id}/products`, { params: { demographic } })
}
