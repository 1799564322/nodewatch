<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElButton, ElCard, ElDatePicker, ElEmpty, ElTag } from 'element-plus'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { getDevice, getDisks, getHistory } from '@/api/devices'
import { listAlerts, startMaintenance, stopMaintenance } from '@/api/alerts'
import type { AlertEvent } from '@/types/alert'
import type { Device, DiskMetric, HistoryPoint } from '@/types/device'

echarts.use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])
const route = useRoute()
const deviceId = route.params.deviceId as string
const device = ref<Device | null>(null)
const disks = ref<DiskMetric[]>([])
const points = ref<HistoryPoint[]>([])
const resolution = ref('raw')
const alerts = ref<AlertEvent[]>([])
const chartElement = ref<HTMLDivElement>()
const customRange = ref<[Date, Date]>()
let chart: echarts.ECharts | undefined

function formatBytes(bytes: number) {
  const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
  let value = bytes
  let index = 0
  while (value >= 1024 && index < units.length - 1) { value /= 1024; index++ }
  return `${value.toFixed(index ? 1 : 0)} ${units[index]}`
}

function renderChart() {
  if (!chartElement.value) return
  chart ||= echarts.init(chartElement.value)
  const series = [
    ['CPU %', 'cpu_percent', 0], ['内存 %', 'memory_percent', 0],
    ['系统盘 %', 'root_disk_percent', 0], ['网络上行 B/s', 'net_tx_bytes_per_sec', 1],
    ['网络下行 B/s', 'net_rx_bytes_per_sec', 1],
  ] as const
  const expectedGap = resolution.value === 'raw' ? 120_000 : resolution.value === '5m' ? 600_000 : 7_200_000
  function seriesData(key: keyof HistoryPoint) {
    const data: Array<[number, string | number | null]> = []
    points.value.forEach((point, index) => {
      const timestamp = new Date(point.collected_at).getTime()
      if (index && timestamp - new Date(points.value[index - 1].collected_at).getTime() > expectedGap) {
        data.push([timestamp - 1, null])
      }
      data.push([timestamp, point[key]])
    })
    return data
  }
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: { bottom: 8, textStyle: { color: '#aac1d8' } },
    grid: { left: 50, right: 24, top: 50, bottom: 80 },
    xAxis: { type: 'time', axisLabel: { color: '#829bb5' } },
    yAxis: [
      { type: 'value', min: 0, max: 100, axisLabel: { color: '#829bb5', formatter: '{value}%' } },
      { type: 'value', axisLabel: { color: '#829bb5', formatter: '{value} B/s' } },
    ],
    series: series.map(([name, key, yAxisIndex]) => ({
      name, yAxisIndex, type: 'line', showSymbol: false, connectNulls: false,
      data: seriesData(key),
    })),
  })
}

async function loadRange(from: Date, to = new Date()) {
  const history = await getHistory(deviceId, from, to)
  points.value = history.points
  resolution.value = history.resolution
  await nextTick()
  renderChart()
}

async function selectHours(hours: number) {
  await loadRange(new Date(Date.now() - hours * 3_600_000))
}

async function loadCustom() {
  if (customRange.value) await loadRange(customRange.value[0], customRange.value[1])
}

async function enableMaintenance() {
  await startMaintenance(deviceId, new Date(Date.now() + 3_600_000))
  device.value = await getDevice(deviceId)
}

async function disableMaintenance() {
  await stopMaintenance(deviceId)
  device.value = await getDevice(deviceId)
}

function resize() { chart?.resize() }
onMounted(async () => {
  ;[device.value, disks.value, alerts.value] = await Promise.all([
    getDevice(deviceId), getDisks(deviceId), listAlerts(undefined, deviceId),
  ])
  await selectHours(1)
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => { window.removeEventListener('resize', resize); chart?.dispose() })
</script>

<template>
  <section v-if="device" class="device-detail">
    <RouterLink class="back-link" to="/devices">← 返回设备列表</RouterLink>
    <div class="page-heading">
      <div><p class="eyebrow">P4 · 历史与磁盘</p><h2>{{ device.name }}</h2><p>{{ device.hostname }} · {{ device.os_name }} {{ device.os_version }}</p></div>
      <div><el-tag :type="device.status === 'online' ? 'success' : 'info'">{{ device.status === 'online' ? '在线' : '离线' }}</el-tag>
      <el-button v-if="!device.maintenance_until" size="small" @click="enableMaintenance">维护 1 小时</el-button>
      <el-button v-else size="small" @click="disableMaintenance">结束维护</el-button></div>
    </div>
    <div class="range-toolbar">
      <el-button @click="selectHours(1)">1 小时</el-button><el-button @click="selectHours(24)">24 小时</el-button><el-button @click="selectHours(168)">7 天</el-button>
      <el-date-picker v-model="customRange" type="datetimerange" start-placeholder="开始" end-placeholder="结束" />
      <el-button :disabled="!customRange" @click="loadCustom">查询</el-button>
      <span>分辨率：{{ resolution }}</span>
    </div>
    <el-card><div v-if="points.length" ref="chartElement" class="history-chart" /><el-empty v-else description="当前时间范围暂无指标" /></el-card>
    <h3>磁盘</h3>
    <div class="disk-grid">
      <el-card v-for="disk in disks" :key="disk.mountpoint"><strong>{{ disk.mountpoint }}</strong><p>{{ disk.filesystem || '未知文件系统' }}</p><p>{{ formatBytes(disk.used_bytes) }} / {{ formatBytes(disk.total_bytes) }}（{{ disk.percent }}%）</p></el-card>
      <el-empty v-if="!disks.length" description="Agent 尚未上报磁盘信息" />
    </div>
    <h3>告警事件</h3>
    <el-empty v-if="!alerts.length" description="该设备暂无告警" />
    <div v-else class="alert-list"><el-card v-for="alert in alerts" :key="alert.id"><strong>{{ alert.title }}</strong><p>{{ alert.message }}</p><el-tag>{{ alert.status }}</el-tag></el-card></div>
  </section>
</template>
