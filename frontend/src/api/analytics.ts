import client from './client'

export function getSalesTrend(days = 30) {
  return client.get('/analytics/sales-trend', { params: { days } })
}

export function getDemographicDist() {
  return client.get('/analytics/demographic-dist')
}

export function getProductCompare() {
  return client.get('/analytics/product-compare')
}

export function getProductDemoBreakdown(productId: number) {
  return client.get(`/analytics/product/${productId}/demographic-breakdown`)
}

export function getTopProducts(limit = 10) {
  return client.get('/analytics/top-products', { params: { limit } })
}

export function getAdminOverview() {
  return client.get('/admin/overview')
}

export function runSimulationTick(count = 1) {
  return client.post(`/admin/simulation/tick?count=${count}`)
}
