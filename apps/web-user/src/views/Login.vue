<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
    <div class="bg-white p-6 rounded shadow-md w-full max-w-sm">
      <h1 class="text-xl font-bold mb-4 text-center">登录</h1>
      <n-form :model="form">
        <n-form-item label="用户名">
          <n-input v-model:value="form.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" placeholder="请输入密码" />
        </n-form-item>
        <n-button type="primary" block @click="handleLogin" :loading="loading">登录</n-button>
      </n-form>
      <p class="mt-4 text-center text-sm">
        没有账号？<router-link to="/register" class="text-blue-500">去注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import { login } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const loading = ref(false)
const form = ref({ username: '', password: '' })

const handleLogin = async () => {
  loading.value = true
  try {
    const res = await login(form.value)
    authStore.setToken(res.token)
    router.push('/')
  } catch (e) {
    message.error('登录失败')
  } finally {
    loading.value = false
  }
}
</script>
