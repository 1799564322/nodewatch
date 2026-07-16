import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  timeout: 10_000,
})

