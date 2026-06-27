import client from './client'

export function getStrategies(params?: { status?: string; merchant_id?: number }) {
  return client.get('/marketing/strategies', { params })
}

export function getStrategy(id: number) {
  return client.get(`/marketing/strategies/${id}`)
}

export function approveStrategy(id: number, comment = '') {
  return client.post(`/marketing/strategies/${id}/approve`, { comment })
}

export function rejectStrategy(id: number, comment = '') {
  return client.post(`/marketing/strategies/${id}/reject`, { comment })
}
