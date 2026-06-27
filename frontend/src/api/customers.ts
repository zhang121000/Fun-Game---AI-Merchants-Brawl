import client from './client'

export function getCustomers() {
  return client.get('/customers')
}

export function getCurrentCustomer() {
  return client.get('/customers/current')
}

export function switchCustomer(id: number) {
  return client.post(`/customers/switch/${id}`)
}
