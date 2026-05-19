import client from './client'

export const getStrategies = (params?: { status?: string; merchant_id?: number }) =>
  client.get('/marketing/strategies', { params })

export const getStrategy = (id: number) => client.get(`/marketing/strategies/${id}`)

export const approveStrategy = (id: number, comment = '') =>
  client.post(`/marketing/strategies/${id}/approve`, { comment })

export const rejectStrategy = (id: number, comment = '') =>
  client.post(`/marketing/strategies/${id}/reject`, { comment })
