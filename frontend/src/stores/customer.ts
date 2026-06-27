import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../api/customers'

export interface Customer {
  id: number
  demographic: string
  name: string | null
  age_range: string
  preferences: Record<string, number>
  purchase_weight: number
  is_star: boolean
}

export const useCustomerStore = defineStore('customer', () => {
  const current = ref<Customer | null>(null)
  const customers = ref<Customer[]>([])
  const loading = ref(false)

  async function fetchCurrent() {
    const res = await api.getCurrentCustomer()
    current.value = res.data
  }

  async function fetchAll() {
    const res = await api.getCustomers()
    customers.value = res.data
  }

  async function switchTo(id: number) {
    loading.value = true
    const res = await api.switchCustomer(id)
    current.value = res.data
    loading.value = false
  }

  return { current, customers, loading, fetchCurrent, fetchAll, switchTo }
})
