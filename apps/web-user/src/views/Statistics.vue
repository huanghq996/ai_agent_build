<template>
  <div class="min-h-screen bg-gray-50 p-4">
    <h1 class="text-xl font-bold mb-4">统计</h1>

    <!-- 消费统计 -->
    <div class="bg-white p-4 rounded mb-4">
      <h2 class="font-bold mb-3">消费统计 (近7天)</h2>
      <div v-for="item in billStats" :key="item.period" class="mb-2">
        <div class="text-sm text-gray-600">{{ item.period }}</div>
        <div class="flex gap-2 items-center">
          <div class="w-16 text-xs text-green-600">+{{ item.income }}</div>
          <div class="flex-1 h-2 bg-green-200 rounded">
            <div class="h-2 bg-green-500 rounded" :style="{ width: getBarWidth(item.income, maxIncome) }"></div>
          </div>
        </div>
        <div class="flex gap-2 items-center">
          <div class="w-16 text-xs text-red-600">-{{ item.expense }}</div>
          <div class="flex-1 h-2 bg-red-200 rounded">
            <div class="h-2 bg-red-500 rounded" :style="{ width: getBarWidth(item.expense, maxExpense) }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 抽烟统计 -->
    <div class="bg-white p-4 rounded mb-4">
      <h2 class="font-bold mb-3">抽烟统计 (近7天)</h2>
      <div v-for="item in smokingStats" :key="item.period" class="mb-2 flex items-center gap-2">
        <div class="w-24 text-sm text-gray-600">{{ item.period }}</div>
        <div class="flex-1 h-4 bg-gray-200 rounded">
          <div class="h-4 bg-orange-500 rounded" :style="{ width: getBarWidth(item.count, maxSmoking) }"></div>
        </div>
        <div class="w-8 text-sm">{{ item.count }}</div>
      </div>
    </div>

    <!-- 日程统计 -->
    <div class="bg-white p-4 rounded">
      <h2 class="font-bold mb-3">日程完成率</h2>
      <div class="flex justify-around text-center">
        <div>
          <div class="text-2xl font-bold text-blue-600">{{ scheduleStats.total }}</div>
          <div class="text-sm text-gray-500">总计</div>
        </div>
        <div>
          <div class="text-2xl font-bold text-green-600">{{ scheduleStats.completed }}</div>
          <div class="text-sm text-gray-500">已完成</div>
        </div>
        <div>
          <div class="text-2xl font-bold text-yellow-600">{{ scheduleStats.pending }}</div>
          <div class="text-sm text-gray-500">待办</div>
        </div>
      </div>
      <div class="mt-3 h-4 bg-gray-200 rounded overflow-hidden">
        <div class="h-4 bg-green-500" :style="{ width: completionRate }"></div>
      </div>
      <div class="text-center text-sm text-gray-500 mt-1">完成率: {{ completionRate }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getBillStats, getSmokingStats, getScheduleStats } from '../api/statistics'

const billStats = ref([])
const smokingStats = ref([])
const scheduleStats = ref({ total: 0, completed: 0, pending: 0 })

const maxIncome = computed(() => Math.max(...billStats.value.map(i => Number(i.income) || 0), 1))
const maxExpense = computed(() => Math.max(...billStats.value.map(i => Number(i.expense) || 0), 1))
const maxSmoking = computed(() => Math.max(...smokingStats.value.map(i => i.count || 0), 1))

const completionRate = computed(() => {
  if (scheduleStats.value.total === 0) return '0%'
  return Math.round((scheduleStats.value.completed / scheduleStats.value.total) * 100) + '%'
})

const getBarWidth = (value, max) => {
  if (!value || !max) return '0%'
  return Math.round((Number(value) / max) * 100) + '%'
}

const loadData = async () => {
  const [bill, smoking, schedule] = await Promise.all([
    getBillStats(),
    getSmokingStats(),
    getScheduleStats()
  ])
  billStats.value = bill || []
  smokingStats.value = smoking || []
  scheduleStats.value = schedule || { total: 0, completed: 0, pending: 0 }
}

onMounted(loadData)
</script>
