<script setup lang="ts">
import { ElButton, ElTag } from 'element-plus'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  await router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-navigation">
        <RouterLink class="brand" to="/">NodeWatch</RouterLink>
        <RouterLink to="/devices">设备</RouterLink>
        <RouterLink to="/alerts">告警</RouterLink>
      </div>
      <div class="account">
        <span>{{ auth.user?.username }}</span>
        <el-tag size="small">{{ auth.user?.role }}</el-tag>
        <el-button plain size="small" @click="handleLogout">退出登录</el-button>
      </div>
    </header>
    <main class="app-content">
      <RouterView />
    </main>
  </div>
</template>
