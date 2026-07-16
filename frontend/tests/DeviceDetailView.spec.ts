import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import DeviceDetailView from '@/views/DeviceDetailView.vue'

vi.mock('vue-router', () => ({ useRoute: () => ({ params: { deviceId: 'device-1' } }) }))
vi.mock('@/api/devices', () => ({
  getDevice: vi.fn().mockResolvedValue({
    id: 'device-1', name: '测试设备', hostname: 'host', os_name: 'Windows', os_version: '11',
    status: 'offline',
  }),
  getDisks: vi.fn().mockResolvedValue([]),
  getHistory: vi.fn().mockResolvedValue({ resolution: 'raw', points: [] }),
}))
vi.mock('@/api/alerts', () => ({
  listAlerts: vi.fn().mockResolvedValue([]),
  startMaintenance: vi.fn(),
  stopMaintenance: vi.fn(),
}))

describe('DeviceDetailView', () => {
  it('历史为空时展示明确空状态', async () => {
    const wrapper = mount(DeviceDetailView, { global: { stubs: { RouterLink: true } } })
    await flushPromises()
    expect(wrapper.text()).toContain('测试设备')
    expect(wrapper.text()).toContain('当前时间范围暂无指标')
    expect(wrapper.text()).toContain('Agent 尚未上报磁盘信息')
  })
})
