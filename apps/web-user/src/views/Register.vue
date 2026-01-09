<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
    <div class="bg-white p-6 rounded shadow-md w-full max-w-sm">
      <h1 class="text-xl font-bold mb-4 text-center">注册</h1>
      <n-form :model="form">
        <n-form-item label="用户名">
          <n-input v-model:value="form.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" placeholder="请输入密码" />
        </n-form-item>
        <n-form-item label="昵称">
          <n-input v-model:value="form.nickname" placeholder="请输入昵称" />
        </n-form-item>
        <n-button type="primary" block @click="handleRegister" :loading="loading">注册</n-button>
      </n-form>
      <p class="mt-4 text-center text-sm">
        已有账号？<router-link to="/login" class="text-blue-500">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import { register } from '../api/auth'

const router = useRouter()
const message = useMessage()
const loading = ref(false)
const form = ref({ username: '', password: '', nickname: '' })

const handleRegister = async () => {
  loading.value = true
  try {
    await register(form.value)
    message.success('注册成功')
    router.push('/login')
  } catch (e) {
    message.error('注册失败')
  } finally {
    loading.value = false
  }
}
</script>
