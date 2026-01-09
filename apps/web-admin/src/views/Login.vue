<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="bg-white p-8 rounded shadow-md w-96">
      <h1 class="text-2xl font-bold mb-6 text-center">管理后台</h1>
      <n-form ref="formRef" :model="form" :rules="rules">
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="form.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="form.password" type="password" placeholder="请输入密码" />
        </n-form-item>
        <n-button type="primary" block @click="handleLogin" :loading="loading">
          登录
        </n-button>
      </n-form>
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
const rules = {
  username: { required: true, message: '请输入用户名' },
  password: { required: true, message: '请输入密码' }
}

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
