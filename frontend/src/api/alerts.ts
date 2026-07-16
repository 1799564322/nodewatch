import { apiClient } from './client'
import type { AlertEvent, AlertRule } from '@/types/alert'

export async function listAlerts(status?: string, deviceId?: string): Promise<AlertEvent[]> {
  return (await apiClient.get<AlertEvent[]>('/alerts', { params: { status, device_id: deviceId } })).data
}
export async function acknowledgeAlert(id: string): Promise<AlertEvent> {
  return (await apiClient.post<AlertEvent>(`/alerts/${id}/acknowledge`)).data
}
export async function listRules(): Promise<AlertRule[]> {
  return (await apiClient.get<AlertRule[]>('/alert-rules')).data
}
export async function updateRule(id: string, values: Partial<AlertRule>): Promise<AlertRule> {
  return (await apiClient.patch<AlertRule>(`/alert-rules/${id}`, values)).data
}
export async function startMaintenance(deviceId: string, until: Date): Promise<void> {
  await apiClient.post(`/devices/${deviceId}/maintenance`, { until: until.toISOString() })
}
export async function stopMaintenance(deviceId: string): Promise<void> {
  await apiClient.delete(`/devices/${deviceId}/maintenance`)
}
