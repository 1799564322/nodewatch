export interface Device {
  id: string
  name: string
  hostname: string | null
  os_name: string | null
  os_version: string | null
  architecture: string | null
  agent_version: string | null
  last_seen_at: string | null
  is_enabled: boolean
  cpu_percent: number | null
  memory_percent: number | null
  root_disk_percent: number | null
  net_tx_bytes_per_sec: number | null
  net_rx_bytes_per_sec: number | null
  status: 'online' | 'offline' | 'disabled'
  maintenance_until: string | null
}

export interface Dashboard {
  total_devices: number
  online_devices: number
  offline_devices: number
  firing_alerts: number
  alert_devices: number
  top_cpu: Device[]
  top_memory: Device[]
}

export interface HistoryPoint {
  collected_at: string
  cpu_percent: number
  memory_percent: number
  root_disk_percent: number | null
  net_tx_bytes_per_sec: number
  net_rx_bytes_per_sec: number
}

export interface HistoryResponse { resolution: string; points: HistoryPoint[] }
export interface DiskMetric {
  mountpoint: string
  filesystem: string | null
  total_bytes: number
  used_bytes: number
  percent: number
  collected_at: string
}

export interface DeviceList {
  items: Device[]
  page: number
  page_size: number
  total: number
}

export interface AgentToken {
  token: string
  token_id: string
  token_prefix: string
  warning: string
}
