import { apiClient } from './client'
import type { AgentToken, Dashboard, Device, DeviceList, DiskMetric, HistoryResponse } from '@/types/device'

export async function listDevices(): Promise<DeviceList> {
  return (await apiClient.get<DeviceList>('/devices')).data
}

export async function createDevice(name: string): Promise<Device> {
  return (await apiClient.post<Device>('/devices', { name })).data
}

export async function createToken(deviceId: string): Promise<AgentToken> {
  return (await apiClient.post<AgentToken>(`/devices/${deviceId}/tokens`)).data
}

export async function getDashboard(): Promise<Dashboard> {
  return (await apiClient.get<Dashboard>('/dashboard')).data
}

export async function getDevice(deviceId: string): Promise<Device> {
  return (await apiClient.get<Device>(`/devices/${deviceId}`)).data
}

export async function getHistory(deviceId: string, from: Date, to: Date): Promise<HistoryResponse> {
  return (await apiClient.get<HistoryResponse>(`/devices/${deviceId}/metrics/history`, {
    params: { from: from.toISOString(), to: to.toISOString() },
  })).data
}

export async function getDisks(deviceId: string): Promise<DiskMetric[]> {
  return (await apiClient.get<DiskMetric[]>(`/devices/${deviceId}/disks`)).data
}
