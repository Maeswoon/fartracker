import { defineStore } from 'pinia'
import { ref } from 'vue'
import { postLogin, postLogout, getCurrentUser } from '@/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  async function restoreSession() {
    try {
      user.value = await getCurrentUser()
    } catch {
      user.value = null
    }
  }

  async function login(username: string, password: string) {
    await postLogin(username, password)
    user.value = await getCurrentUser()
  }

  async function logout() {
    try {
      await postLogout()
    } catch {
      // Clear user even if logout API fails
    }
    user.value = null
  }

  return { user, restoreSession, login, logout }
})
