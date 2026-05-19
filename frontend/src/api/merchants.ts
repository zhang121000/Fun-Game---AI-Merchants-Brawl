import client from './client'

export const getMerchants = () => client.get('/merchants')
export const getMerchant = (id: number) => client.get(`/merchants/${id}`)
export const getMerchantProducts = (id: number, demographic?: string) =>
  client.get(`/merchants/${id}/products`, { params: { demographic } })
