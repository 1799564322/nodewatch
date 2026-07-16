import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import DevicesView from '@/views/DevicesView.vue'

vi.mock('@/api/devices', () => ({
  listDevices: vi.fn().mockResolvedValue({ items: [], page: 1, page_size: 20, total: 0 }),
  createDevice: vi.fn(),
  createToken: vi.fn(),
}))

describe('DevicesView', () => {
  it('设备为空时显示引导和创建按钮', async () => {
    const wrapper = mount(DevicesView, { global: { stubs: { RouterLink: true } } })
    await flushPromises()

    expect(wrapper.text()).toContain('还没有设备')
    expect(wrapper.text()).toContain('创建设备')
  })
})
