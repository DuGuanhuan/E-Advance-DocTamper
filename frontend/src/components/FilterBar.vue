<template>
  <div class="filter-bar">
    <el-input
      v-model="searchTerm"
      placeholder="搜索文件名或任务ID..."
      style="width: 300px"
      clearable
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
    
    <el-select
      v-model="selectedStatus"
      placeholder="所有状态"
      style="width: 150px"
      clearable
    >
      <el-option
        v-for="option in statusOptions"
        :key="option.value"
        :label="option.label"
        :value="option.value"
      />
    </el-select>
    
    <el-button type="primary" @click="handleFilter">
      <el-icon><Search /></el-icon>
      筛选
    </el-button>
  </div>
  
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { STATUS_OPTIONS } from '../utils/constants'

// 响应式数据
const searchTerm = ref('')
const selectedStatus = ref('')
const statusOptions = STATUS_OPTIONS

// 事件定义
const emit = defineEmits(['filter'])

// 处理筛选
const handleFilter = () => {
  emit('filter', {
    search_term: searchTerm.value,
    status: selectedStatus.value
  })
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  align-items: center;
}
</style>
