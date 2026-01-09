<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">用户管理</h1>
    <n-data-table :columns="columns" :data="users" :loading="loading" />
    <n-pagination v-model:page="page" :page-count="totalPages" class="mt-4" @update:page="loadUsers" />
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { NDataTable, NPagination, NButton, NTag, useMessage } from 'naive-ui'
import { getUsers, updateUserStatus } from '../api/user'

const message = useMessage()
const users = ref([])
const loading = ref(false)
const page = ref(1)
const totalPages = ref(1)

const columns = [
  { title: 'ID', key: 'id' },
  { title: '用户名', key: 'username' },
  { title: '昵称', key: 'nickname' },
  {
    title: '状态',
    key: 'status',
    render: (row) => h(NTag, { type: row.status === 1 ? 'success' : 'error' }, () => row.status === 1 ? '正常' : '禁用')
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => h(NButton, {
      size: 'small',
      onClick: () => toggleStatus(row)
    }, () => row.status === 1 ? '禁用' : '启用')
  }
]

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await getUsers(page.value)
    users.value = res.records || []
    totalPages.value = res.totalPage || 1
  } finally {
    loading.value = false
  }
}

const toggleStatus = async (row) => {
  const newStatus = row.status === 1 ? 0 : 1
  await updateUserStatus(row.id, newStatus)
  message.success('操作成功')
  loadUsers()
}

onMounted(loadUsers)
</script>
