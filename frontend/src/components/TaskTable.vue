<template>
  <el-table 
    :data="tasks" 
    style="width: 100%"
    :row-style="{ cursor: 'pointer' }"
    @row-click="handleRowClick"
  >
    <el-table-column prop="task_id" label="任务ID" width="120" />
    
    <el-table-column label="文件名" min-width="200">
      <template #default="{ row }">
        <span v-if="row.files && row.files.length > 0">
          {{ row.files[0].filename }}
        </span>
        <span v-else class="text-placeholder">无文件</span>
      </template>
    </el-table-column>
    
    <el-table-column label="状态" width="120">
      <template #default="{ row }">
        <el-tag 
          :class="getStatusInfo(row.status).css_class"
          class="status-tag"
        >
          {{ getStatusInfo(row.status).text }}
        </el-tag>
      </template>
    </el-table-column>
    
    <el-table-column prop="assignee" label="负责人" width="120">
      <template #default="{ row }">
        <span v-if="row.assignee">{{ row.assignee }}</span>
        <span v-else class="text-placeholder">未分配</span>
      </template>
    </el-table-column>
    
    <el-table-column label="上传时间" width="180">
      <template #default="{ row }">
        {{ formatDateTime(row.created_at) }}
      </template>
    </el-table-column>
    
    <el-table-column label="操作" width="120">
      <template #default="{ row }">
        <el-button
          type="primary"
          link
          :disabled="row.status === 'processing'"
          @click.stop="handleViewReport(row.task_id)"
        >
          查看报告
        </el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { getStatusInfo, formatDateTime } from '../utils/constants'

// Props
defineProps({
  tasks: {
    type: Array,
    default: () => []
  }
})

// Router
const router = useRouter()

// 处理查看报告
const handleViewReport = (taskId) => {
  router.push(`/report/${taskId}`)
}

// 处理行点击
const handleRowClick = (row) => {
  if (row.status !== 'processing') {
    handleViewReport(row.task_id)
  }
}
</script>

<style scoped>
.status-tag {
  border: none !important;
}

.text-placeholder {
  color: var(--text-light-color);
  font-style: italic;
}

:deep(.el-table__row) {
  transition: background-color 0.3s;
}

:deep(.el-table__row:hover) {
  background-color: #EBF2FA !important;
}

:deep(.el-table__row[aria-disabled="true"]) {
  cursor: not-allowed !important;
  opacity: 0.6;
}
</style>