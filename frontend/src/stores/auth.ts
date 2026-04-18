import { defineStore } from 'pinia'
import { ref } from 'vue'
import { postLogin, getCurrentUser } from '@/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  async function restoreSession() {
    const token = localStorage.getItem('access')
    if (!token) return
    try {
      user.value = await getCurrentUser()
    } catch {
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
    }
  }

  async function login(username: string, password: string) {
    const { access, refresh } = await postLogin(username, password)
    localStorage.setItem('access', access)
    localStorage.setItem('refresh', refresh)
    user.value = await getCurrentUser()
  }

  function logout() {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    user.value = null
  }

  return { user, restoreSession, login, logout }
})
