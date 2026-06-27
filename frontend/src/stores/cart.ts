import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../api/cart'

export interface CartItem {
  id: number
  product_id: number
  quantity: number
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const cartId = ref<number | null>(null)

  async function fetch(customerId: number) {
    const res = await api.getCart(customerId)
    items.value = res.data.items || []
    cartId.value = res.data.id
  }

  async function addItem(customerId: number, productId: number, qty = 1) {
    const res = await api.addToCart(customerId, productId, qty)
    items.value = res.data.items || []
  }

  async function updateItem(customerId: number, itemId: number, qty: number) {
    const res = await api.updateCartItem(customerId, itemId, qty)
    items.value = res.data.items || []
  }

  async function removeItem(customerId: number, itemId: number) {
    const res = await api.removeCartItem(customerId, itemId)
    items.value = res.data.items || []
  }

  function clear() {
    items.value = []
    cartId.value = null
  }

  return { items, cartId, fetch, addItem, updateItem, removeItem, clear }
})
