import { apiClient } from './client'
import type { AuthResponse } from '@/types/auth'

export async function login(username: string, password: string): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/login', { username, password })
  return response.data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}

export async function getCurrentUser(): Promise<AuthResponse> {
  const response = await apiClient.get<AuthResponse>('/auth/me')
  return response.data
}

