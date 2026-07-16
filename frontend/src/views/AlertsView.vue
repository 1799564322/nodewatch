<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElButton, ElInputNumber, ElOption, ElSelect, ElSwitch, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { acknowledgeAlert, listAlerts, listRules, updateRule } from '@/api/alerts'
import type { AlertEvent, AlertRule } from '@/types/alert'

const alerts = ref<AlertEvent[]>([])
const rules = ref<AlertRule[]>([])
const statusFilter = ref<string>()

async function load() { [alerts.value, rules.value] = await Promise.all([listAlerts(statusFilter.value), listRules()]) }
async function saveRule(id: string, threshold: number | null, duration: number, enabled: boolean) {
  await updateRule(id, { threshold, duration_seconds: duration, is_enabled: enabled })
  await load()
}
async function acknowledge(id: string) { await acknowledgeAlert(id); await load() }
onMounted(load)
</script>

<template>
  <section class="alerts-page">
    <div class="page-heading"><div><p class="eyebrow">P5 · 状态机</p><h2>告警</h2><p>调整规则、查看触发与恢复，并确认正在处理的事件。</p></div></div>
    <h3>规则</h3>
    <el-table :data="rules">
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="metric" label="指标" />
      <el-table-column label="阈值"><template #default="s"><el-input-number v-if="s.row.threshold != null" v-model="s.row.threshold" :min="0" :max="100" size="small" /></template></el-table-column>
      <el-table-column label="持续秒数"><template #default="s"><el-input-number v-model="s.row.duration_seconds" :min="0" size="small" /></template></el-table-column>
      <el-table-column label="启用"><template #default="s"><el-switch v-model="s.row.is_enabled" /></template></el-table-column>
      <el-table-column label="操作"><template #default="s"><el-button size="small" @click="saveRule(s.row.id as string, s.row.threshold as number | null, s.row.duration_seconds as number, s.row.is_enabled as boolean)">保存</el-button></template></el-table-column>
    </el-table>
    <div class="alert-heading"><h3>事件</h3><el-select v-model="statusFilter" clearable placeholder="全部状态" @change="load"><el-option label="触发中" value="firing" /><el-option label="已确认" value="acknowledged" /><el-option label="已恢复" value="resolved" /></el-select></div>
    <el-table :data="alerts" empty-text="暂无告警事件">
      <el-table-column prop="title" label="告警" min-width="160" /><el-table-column prop="message" label="内容" min-width="240" />
      <el-table-column label="状态"><template #default="s"><el-tag>{{ s.row.status }}</el-tag></template></el-table-column>
      <el-table-column label="开始时间"><template #default="s">{{ new Date(s.row.started_at).toLocaleString() }}</template></el-table-column>
      <el-table-column label="操作"><template #default="s"><el-button v-if="s.row.status === 'firing'" size="small" @click="acknowledge(s.row.id)">确认</el-button></template></el-table-column>
    </el-table>
  </section>
</template>
