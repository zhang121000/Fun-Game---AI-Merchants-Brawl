import client from './client'

export const getCustomers = () => client.get('/customers')
export const getCurrentCustomer = () => client.get('/customers/current')
export const switchCustomer = (id: number) => client.post(`/customers/switch/${id}`)
