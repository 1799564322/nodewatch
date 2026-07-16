export interface AlertRule {
  id: string
  name: string
  metric: string
  threshold: number | null
  duration_seconds: number
  severity: string
  is_enabled: boolean
}

export interface AlertEvent {
  id: string
  device_id: string
  status: 'firing' | 'acknowledged' | 'resolved'
  severity: string
  title: string
  message: string
  observed_value: number | null
  threshold_value: number | null
  started_at: string
  resolved_at: string | null
}
