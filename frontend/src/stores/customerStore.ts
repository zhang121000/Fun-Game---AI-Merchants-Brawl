import { create } from 'zustand'
import * as api from '../api/customers'

interface Customer {
  id: number
  demographic: string
  name: string | null
  age_range: string
  preferences: Record<string, number>
  purchase_weight: number
  is_star: boolean
}

interface CustomerStore {
  current: Customer | null
  customers: Customer[]
  loading: boolean
  fetchCurrent: () => Promise<void>
  fetchAll: () => Promise<void>
  switchTo: (id: number) => Promise<void>
}

export const useCustomerStore = create<CustomerStore>((set) => ({
  current: null,
  customers: [],
  loading: false,
  fetchCurrent: async () => {
    const res = await api.getCurrentCustomer()
    set({ current: res.data })
  },
  fetchAll: async () => {
    const res = await api.getCustomers()
    set({ customers: res.data })
  },
  switchTo: async (id: number) => {
    set({ loading: true })
    const res = await api.switchCustomer(id)
    set({ current: res.data, loading: false })
  },
}))
