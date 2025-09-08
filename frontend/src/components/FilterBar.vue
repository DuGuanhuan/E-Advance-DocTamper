<template>
  <div class="filter-bar">
    <el-input
      v-model="searchTerm"
      placeholder="搜索文件名或任务ID..."
      style="width: 300px"
      clearable
      @keyup.enter="handleFilter"
      @clear="handleFilter"
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
      @change="handleFilter"
      @clear="handleFilter"
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
  margin-bottom: 0;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #F8FAFE 0%, #F0F9FF 100%);
  border-bottom: 1px solid #E4E7ED;
  flex-wrap: wrap;
}

/* 输入框样式优化 */
:deep(.el-input) {
  border-radius: 6px;
}

:deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border: 1px solid #DCDFE6;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #C6E2FF;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #409EFF;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

:deep(.el-input__inner) {
  font-size: 14px;
  color: #303133;
  padding: 12px 16px;
}

:deep(.el-input__inner::placeholder) {
  color: #C0C4CC;
  font-size: 14px;
}

:deep(.el-input__prefix) {
  color: #909399;
}

/* 选择器样式优化 */
:deep(.el-select) {
  border-radius: 6px;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 6px;
}

:deep(.el-select-dropdown) {
  border-radius: 6px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
  border: 1px solid #E4E7ED;
}

:deep(.el-select-dropdown__item) {
  padding: 8px 16px;
  font-size: 14px;
  transition: all 0.3s ease;
}

:deep(.el-select-dropdown__item:hover) {
  background: #F0F9FF;
  color: #409EFF;
}

:deep(.el-select-dropdown__item.selected) {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  color: white;
  font-weight: 500;
}

/* 按钮样式优化 */
:deep(.el-button) {
  border-radius: 6px;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  border: none;
}

:deep(.el-button:hover) {
  background: linear-gradient(135deg, #337ecc 0%, #5dade2 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

:deep(.el-button:active) {
  transform: translateY(0);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-bar {
    padding: 16px;
    gap: 12px;
  }
  
  :deep(.el-input) {
    width: 100% !important;
    max-width: 300px;
  }
  
  :deep(.el-select) {
    width: 100% !important;
    max-width: 150px;
  }
  
  :deep(.el-button) {
    padding: 10px 16px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
    padding: 12px;
  }
  
  :deep(.el-input),
  :deep(.el-select) {
    width: 100% !important;
    max-width: none;
  }
  
  :deep(.el-button) {
    width: 100%;
    justify-content: center;
  }
}
</style>