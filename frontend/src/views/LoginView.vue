<script setup lang="ts">
import axios from 'axios'
import { ElAlert, ElButton, ElForm, ElFormItem, ElInput } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const form = reactive({ username: '', password: '' })

async function handleSubmit() {
  errorMessage.value = ''
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.push(redirect)
  } catch (error) {
    errorMessage.value = axios.isAxiosError(error)
      ? (error.response?.data?.detail ?? '登录失败，请稍后再试')
      : '登录失败，请稍后再试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-card" aria-labelledby="login-title">
      <div class="login-intro">
        <p class="eyebrow">轻量级主机监控</p>
        <h1 id="login-title">登录 NodeWatch</h1>
        <p>查看主机状态、历史指标与告警。</p>
      </div>
      <el-form label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" maxlength="64" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            autocomplete="current-password"
            maxlength="256"
            show-password
            type="password"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />
        <el-button
          class="login-button"
          type="primary"
          native-type="submit"
          :loading="loading"
          :disabled="!form.username || !form.password"
        >
          登录
        </el-button>
      </el-form>
    </section>
  </main>
</template>
