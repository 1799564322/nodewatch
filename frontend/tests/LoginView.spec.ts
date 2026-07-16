import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import LoginView from '@/views/LoginView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: () => Promise.resolve() }),
}))

describe('LoginView', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('显示登录表单', () => {
    const wrapper = mount(LoginView, {
      global: {
        stubs: {
          ElForm: { template: '<form><slot /></form>' },
          ElFormItem: { template: '<label><slot /></label>' },
          ElInput: { template: '<input />' },
          ElAlert: true,
          ElButton: { template: '<button><slot /></button>' },
        },
      },
    })

    expect(wrapper.get('h1').text()).toBe('登录 NodeWatch')
    expect(wrapper.get('button').text()).toBe('登录')
  })
})
