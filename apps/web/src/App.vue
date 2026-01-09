<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Health Check</h1>
    <div v-if="loading" class="text-gray-500">Loading...</div>
    <div v-else class="bg-white p-6 rounded-lg shadow">
      <div class="flex items-center gap-2 mb-2">
        <span class="font-semibold">Status:</span>
        <span :class="{'text-green-600': status === 'ok', 'text-red-600': status !== 'ok'}">
          {{ status }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <span class="font-semibold">Time:</span>
        <span class="font-mono text-sm">{{ time }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { http } from './api/http'

const status = ref('')
const time = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await http.get('/health')
    status.value = res.data.status
    time.value = res.data.time
  } catch (e) {
    status.value = 'error'
    time.value = e.message
  } finally {
    loading.value = false
  }
})
</script>
