<template>
  <div class="min-h-screen bg-gray-50 p-4">
    <h1 class="text-xl font-bold mb-4">账单</h1>
    <n-button type="primary" @click="showModal = true" class="mb-4">添加账单</n-button>

    <div v-for="bill in bills" :key="bill.id" class="bg-white p-3 rounded mb-2">
      <div class="flex justify-between">
        <span>{{ bill.remark || '无备注' }}</span>
        <span :class="bill.type === 1 ? 'text-red-500' : 'text-green-500'">
          {{ bill.type === 1 ? '-' : '+' }}{{ bill.amount }}
        </span>
      </div>
      <div class="text-sm text-gray-500">{{ bill.billDate }}</div>
    </div>

    <n-modal v-model:show="showModal" preset="dialog" title="添加账单">
      <n-form :model="form">
        <n-form-item label="类型">
          <n-radio-group v-model:value="form.type">
            <n-radio :value="1">支出</n-radio>
            <n-radio :value="2">收入</n-radio>
          </n-radio-group>
        </n-form-item>
        <n-form-item label="金额">
          <n-input-number v-model:value="form.amount" :min="0" />
        </n-form-item>
        <n-form-item label="分类">
          <n-select v-model:value="form.categoryId" :options="categoryOptions" />
        </n-form-item>
        <n-form-item label="备注">
          <n-input v-model:value="form.remark" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="primary" @click="handleSubmit">确定</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { NButton, NModal, NForm, NFormItem, NInput, NInputNumber, NSelect, NRadioGroup, NRadio } from 'naive-ui'
import { getBills, createBill, getCategories } from '../api/bill'

const bills = ref([])
const categories = ref([])
const showModal = ref(false)
const form = ref({ type: 1, amount: 0, categoryId: null, remark: '', ledgerId: 1, billDate: new Date().toISOString().split('T')[0] })

const categoryOptions = ref([])

const loadData = async () => {
  const [billRes, catRes] = await Promise.all([getBills(), getCategories()])
  bills.value = billRes.records || []
  categories.value = catRes || []
  categoryOptions.value = categories.value.map(c => ({ label: c.name, value: c.id }))
}

const handleSubmit = async () => {
  await createBill(form.value)
  showModal.value = false
  loadData()
}

onMounted(loadData)
</script>
