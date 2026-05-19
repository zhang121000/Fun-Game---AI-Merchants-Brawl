import client from './client'

export const getSalesTrend = (days = 30) =>
  client.get('/analytics/sales-trend', { params: { days } })

export const getDemographicDist = () =>
  client.get('/analytics/demographic-dist')

export const getProductCompare = () =>
  client.get('/analytics/product-compare')

export const getProductDemoBreakdown = (productId: number) =>
  client.get(`/analytics/product/${productId}/demographic-breakdown`)

export const getTopProducts = (limit = 10) =>
  client.get('/analytics/top-products', { params: { limit } })

export const getAdminOverview = () =>
  client.get('/admin/overview')

export const runSimulationTick = (count = 1) =>
  client.post(`/admin/simulation/tick?count=${count}`)
