<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  ElButton,
  ElDialog,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'

import { createDevice, createToken, listDevices } from '@/api/devices'
import type { AgentToken, Device } from '@/types/device'

const devices = ref<Device[]>([])
const loading = ref(true)
const createVisible = ref(false)
const tokenVisible = ref(false)
const name = ref('')
const token = ref<AgentToken | null>(null)
const copied = ref(false)

function formatRate(bytes: number | null) {
  if (bytes == null) return '—'
  if (bytes < 1024) return `${bytes} B/s`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KiB/s`
  return `${(bytes / 1024 ** 2).toFixed(1)} MiB/s`
}

function formatTime(value: string | null) {
  return value ? new Date(value).toLocaleString() : '从未上报'
}

async function load() {
  loading.value = true
  try {
    devices.value = (await listDevices()).items
  } finally {
    loading.value = false
  }
}

async function submitCreate() {
  const device = await createDevice(name.value.trim())
  token.value = await createToken(device.id)
  createVisible.value = false
  tokenVisible.value = true
  name.value = ''
  copied.value = false
  await load()
}

async function rotateToken(deviceId: string) {
  token.value = await createToken(deviceId)
  tokenVisible.value = true
  copied.value = false
}

async function copyToken() {
  if (!token.value) return
  await navigator.clipboard.writeText(token.value.token)
  copied.value = true
  ElMessage.success('Token 已复制')
}

function closeToken() {
  if (!copied.value) {
    ElMessage.warning('请先复制 Token 并妥善保存')
    return
  }
  tokenVisible.value = false
  token.value = null
}

onMounted(load)
</script>

<template>
  <section class="devices-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">P3 · 实时指标</p>
        <h2>设备</h2>
        <p>创建一台设备，再使用一次性 Token 连接 Agent。</p>
      </div>
      <el-button type="primary" @click="createVisible = true">创建设备</el-button>
    </div>

    <p v-if="loading" class="loading-state">正在加载设备……</p>
    <el-table v-else-if="devices.length" :data="devices">
      <el-table-column label="名称">
        <template #default="s"><RouterLink class="device-link" :to="`/devices/${s.row.id}`">{{ s.row.name }}</RouterLink></template>
      </el-table-column>
      <el-table-column prop="hostname" label="主机名" min-width="130">
        <template #default="scope">{{ scope.row.hostname || '等待 Agent' }}</template>
      </el-table-column>
      <el-table-column prop="os_name" label="系统" min-width="100">
        <template #default="scope">{{ scope.row.os_name || '—' }}</template>
      </el-table-column>
      <el-table-column prop="agent_version" label="Agent 版本">
        <template #default="scope">{{ scope.row.agent_version || '—' }}</template>
      </el-table-column>
      <el-table-column label="CPU">
        <template #default="s">{{ s.row.cpu_percent == null ? '—' : `${s.row.cpu_percent}%` }}</template>
      </el-table-column>
      <el-table-column label="内存">
        <template #default="s">{{ s.row.memory_percent == null ? '—' : `${s.row.memory_percent}%` }}</template>
      </el-table-column>
      <el-table-column label="系统盘">
        <template #default="s">{{ s.row.root_disk_percent == null ? '—' : `${s.row.root_disk_percent}%` }}</template>
      </el-table-column>
      <el-table-column label="网络" min-width="210">
        <template #default="s">↑ {{ formatRate(s.row.net_tx_bytes_per_sec) }} / ↓ {{ formatRate(s.row.net_rx_bytes_per_sec) }}</template>
      </el-table-column>
      <el-table-column label="最后上报" width="190">
        <template #default="s">{{ formatTime(s.row.last_seen_at) }}</template>
      </el-table-column>
      <el-table-column label="状态">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'online' ? 'success' : 'info'">
            {{ scope.row.status === 'online' ? '在线' : scope.row.status === 'disabled' ? '已禁用' : '离线' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="scope">
          <el-button size="small" @click="rotateToken(scope.row.id as string)">生成新 Token</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="还没有设备，创建第一台设备开始学习 Agent 认证" />

    <el-dialog v-model="createVisible" title="创建设备" width="min(440px, 92vw)">
      <el-form @submit.prevent="submitCreate">
        <el-form-item label="设备名称">
          <el-input v-model="name" maxlength="100" placeholder="例如：我的电脑" />
        </el-form-item>
        <el-button type="primary" :disabled="!name.trim()" @click="submitCreate">创建并生成 Token</el-button>
      </el-form>
    </el-dialog>

    <el-dialog :model-value="tokenVisible" title="立即保存 Agent Token" :close-on-click-modal="false" :show-close="false" width="min(620px, 92vw)">
      <p class="token-warning">{{ token?.warning }}</p>
      <div class="token-box">{{ token?.token }}</div>
      <template #footer>
        <el-button @click="copyToken">复制 Token</el-button>
        <el-button type="primary" :disabled="!copied" @click="closeToken">我已复制并保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>
