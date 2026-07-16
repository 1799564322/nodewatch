import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import AlertsView from '@/views/AlertsView.vue'

vi.mock('@/api/alerts', () => ({
  listAlerts: vi.fn().mockResolvedValue([]),
  listRules: vi.fn().mockResolvedValue([{ id: '1', name: 'CPU 使用率过高', metric: 'cpu', threshold: 90, duration_seconds: 300, severity: 'warning', is_enabled: true }]),
  updateRule: vi.fn(),
  acknowledgeAlert: vi.fn(),
}))

describe('AlertsView', () => {
  it('显示默认规则和告警空状态', async () => {
    const wrapper = mount(AlertsView)
    await flushPromises()
    expect(wrapper.text()).toContain('CPU 使用率过高')
    expect(wrapper.text()).toContain('暂无告警事件')
  })
})
