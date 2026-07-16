import axios from 'axios'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as authApi from '@/api/auth'
import type { User } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const initialized = ref(false)
  const isAuthenticated = computed(() => user.value !== null)

  async function login(username: string, password: string): Promise<void> {
    const response = await authApi.login(username, password)
    user.value = response.user
    initialized.value = true
  }

  async function fetchCurrentUser(): Promise<void> {
    if (initialized.value) return
    try {
      const response = await authApi.getCurrentUser()
      user.value = response.user
    } catch (error) {
      if (!axios.isAxiosError(error) || error.response?.status !== 401) throw error
      user.value = null
    } finally {
      initialized.value = true
    }
  }

  async function logout(): Promise<void> {
    await authApi.logout()
    user.value = null
    initialized.value = true
  }

  return { user, initialized, isAuthenticated, login, fetchCurrentUser, logout }
})

