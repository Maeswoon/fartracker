import { defineStore } from 'pinia'
import { ref } from 'vue'
import { postLogin, postLogout, getCurrentUser } from '@/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)

  async function restoreSession() {
    try {
      user.value = await getCurrentUser()
    } catch {
      user.value = null
    }
  }

  async function login(username: string, password: string) {
    const data = await postLogin(username, password)
    accessToken.value = data.access
    refreshToken.value = data.refresh
    user.value = await getCurrentUser()
  }

  async function logout() {
    try {
      await postLogout()
    } catch {
      // Clear user even if logout API fails
    }
    user.value = null
    accessToken.value = null
    refreshToken.value = null
  }

  return { user, accessToken, refreshToken, restoreSession, login, logout }
})
