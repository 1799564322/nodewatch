<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElCard, ElEmpty, ElTable, ElTableColumn } from 'element-plus'
import { getDashboard } from '@/api/devices'
import type { Dashboard } from '@/types/device'

const dashboard = ref<Dashboard | null>(null)
onMounted(async () => { dashboard.value = await getDashboard() })
</script>

<template>
  <section v-if="dashboard" class="dashboard-page">
    <div class="summary-grid">
      <el-card><span>设备总数</span><strong>{{ dashboard.total_devices }}</strong></el-card>
      <el-card><span>在线</span><strong>{{ dashboard.online_devices }}</strong></el-card>
      <el-card><span>离线</span><strong>{{ dashboard.offline_devices }}</strong></el-card>
      <el-card><span>触发中告警</span><strong>{{ dashboard.firing_alerts }}</strong></el-card>
    </div>
    <h2>CPU 使用率最高</h2>
    <el-table v-if="dashboard.top_cpu.length" :data="dashboard.top_cpu">
      <el-table-column prop="name" label="设备" />
      <el-table-column label="CPU"><template #default="s">{{ s.row.cpu_percent }}%</template></el-table-column>
      <el-table-column label="内存"><template #default="s">{{ s.row.memory_percent }}%</template></el-table-column>
    </el-table>
    <el-empty v-else description="等待 Agent 上报第一条指标" />
  </section>
</template>
