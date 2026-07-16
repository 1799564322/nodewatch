import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import HomeView from '@/views/HomeView.vue'

vi.mock('@/api/devices', () => ({
  getDashboard: vi.fn().mockResolvedValue({
    total_devices: 3,
    online_devices: 2,
    offline_devices: 1,
    top_cpu: [],
    top_memory: [],
  }),
}))

describe('HomeView', () => {
  it('显示设备总览统计', async () => {
    const wrapper = mount(HomeView)
    await flushPromises()
    expect(wrapper.text()).toContain('设备总数')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('等待 Agent 上报第一条指标')
  })
})
