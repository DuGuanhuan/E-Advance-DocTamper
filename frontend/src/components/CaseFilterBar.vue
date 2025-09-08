<template>
  <div class="filter-bar">
    <el-input
      v-model="search"
      placeholder="搜索案例ID、任务ID、文件名或备注..."
      style="width: 320px"
      clearable
      @clear="emitChange"
      @keyup.enter="emitChange"
      size="large"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>

    <el-select
      v-model="selectedTypes"
      multiple
      collapse-tags
      collapse-tags-tooltip
      placeholder="伪造类型"
      style="width: 360px"
      clearable
      @change="emitChange"
      @clear="emitChange"
      size="large"
    >
      <el-option 
        v-for="opt in forgeryTypeOptions"
        :key="opt.value"
        :label="opt.label"
        :value="opt.value"
      />
    </el-select>

    <el-date-picker
      v-model="dateRange"
      type="datetimerange"
      start-placeholder="开始时间"
      end-placeholder="结束时间"
      :shortcuts="shortcuts"
      value-format="YYYY-MM-DDTHH:mm:ss"
      @change="emitChange"
      size="large"
      style="width: 280px"
    />

    <div class="button-group">
      <el-button :loading="loading" type="primary" @click="emitChange" size="large">
        <el-icon><Search /></el-icon>
        筛选
      </el-button>
      <el-button @click="emitReset" size="large">重置</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  forgeryTypeOptions: {
    type: Array,
    default: () => []
  },
  loading: Boolean
})

const emit = defineEmits(['change', 'reset'])

const search = ref('')
const selectedTypes = ref([])
const dateRange = ref([])

const shortcuts = [
  {
    text: '最近24小时',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24)
      return [start, end]
    },
  },
  {
    text: '最近7天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    },
  },
]

const emitChange = () => {
  emit('change', {
    search: search.value,
    types: selectedTypes.value,
    dateRange: dateRange.value
  })
}

const emitReset = () => {
  search.value = ''
  selectedTypes.value = []
  dateRange.value = []
  emit('reset')
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

.button-group {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: nowrap;
}

/* 与任务筛选栏对齐的控件样式 */
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

/* 日期选择器统一高度 */
:deep(.el-date-editor) {
  border-radius: 6px;
}

/* 按钮样式优化，与任务页一致 */
:deep(.el-button) {
  border-radius: 6px;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  border: none;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #337ecc 0%, #5dade2 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

:deep(.el-button:active) {
  transform: translateY(0);
}

/* 响应式 */
@media (max-width: 768px) {
  .filter-bar {
    padding: 16px;
    gap: 12px;
  }
}
</style>
