import { defineStore } from 'pinia'
import { ref } from 'vue'

import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const checked = ref(false)
  const authenticated = ref(false)
  const username = ref('')

  async function checkSession(): Promise<boolean> {
    try {
      const session = await authApi.currentSession()
      username.value = session.username
      authenticated.value = true
    } catch {
      username.value = ''
      authenticated.value = false
    } finally {
      checked.value = true
    }
    return authenticated.value
  }

  async function login(name: string, password: string): Promise<void> {
    const session = await authApi.login(name, password)
    username.value = session.username
    authenticated.value = true
    checked.value = true
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } finally {
      username.value = ''
      authenticated.value = false
      checked.value = true
    }
  }

  function clearSession(): void {
    username.value = ''
    authenticated.value = false
    checked.value = true
  }

  return { checked, authenticated, username, checkSession, login, logout, clearSession }
})
