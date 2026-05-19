import { create } from 'zustand'
import * as api from '../api/cart'

interface CartItem {
  id: number
  product_id: number
  quantity: number
}

interface CartStore {
  items: CartItem[]
  cartId: number | null
  fetch: (customerId: number) => Promise<void>
  addItem: (customerId: number, productId: number, qty?: number) => Promise<void>
  updateItem: (customerId: number, itemId: number, qty: number) => Promise<void>
  removeItem: (customerId: number, itemId: number) => Promise<void>
  clear: () => void
}

export const useCartStore = create<CartStore>((set) => ({
  items: [],
  cartId: null,
  fetch: async (customerId) => {
    const res = await api.getCart(customerId)
    set({ items: res.data.items || [], cartId: res.data.id })
  },
  addItem: async (customerId, productId, qty = 1) => {
    const res = await api.addToCart(customerId, productId, qty)
    set({ items: res.data.items || [] })
  },
  updateItem: async (customerId, itemId, qty) => {
    const res = await api.updateCartItem(customerId, itemId, qty)
    set({ items: res.data.items || [] })
  },
  removeItem: async (customerId, itemId) => {
    const res = await api.removeCartItem(customerId, itemId)
    set({ items: res.data.items || [] })
  },
  clear: () => set({ items: [], cartId: null }),
}))
