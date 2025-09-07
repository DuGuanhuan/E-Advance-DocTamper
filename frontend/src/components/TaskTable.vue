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
        <span
          class="view-report-link"
          :class="{ disabled: row.status === 'processing' }"
          @click.stop="handleViewReport(row.task_id, row.status)"
        >
          查看报告
        </span>
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
const handleViewReport = (taskId, status) => {
  // 如果状态是 processing，则不执行跳转
  if (status === 'processing') {
    return
  }
  router.push(`/report/${taskId}`)
}

// 处理行点击
const handleRowClick = (row) => {
  if (row.status !== 'processing') {
    handleViewReport(row.task_id, row.status)
  }
}
</script>

<style scoped>
.status-tag {
  border: none !important;
  border-radius: 16px !important;
  padding: 4px 12px !important;
  font-weight: 500 !important;
  font-size: 12px !important;
}

.text-placeholder {
  color: #C0C4CC;
  font-style: italic;
  font-size: 13px;
}

/* --- TaskTable Header Optimization --- */
/* 表格整体样式 */
:deep(.el-table) {
  border-radius: 0;
  border: none;
  font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
  --secondary-color: #F5F7FA;
  --text-light-color: #777;
  --border-color: #DCE1E6;
}

/* 目标: 修改表头单元格 (th) 的背景和文字样式
   使用 !important 来确保覆盖 Element Plus 的默认样式 */
:deep(.el-table__header-wrapper th.el-table__cell) {
  background-color: var(--secondary-color) !important; /* 使用全局变量 F5F7FA */
  color: var(--text-light-color) !important; /* 使用全局变量 #777 */
  font-weight: 600 !important;
  font-size: 14px !important;
  padding: 16px 12px !important;
}

/* 目标: 为整个表头区域添加一条更粗的下边框
   注意: 这里我们选择性地移除了th上的默认边框，统一在header-wrapper上添加 */
:deep(.el-table__header-wrapper) {
  border-bottom: 2px solid var(--border-color);
}

:deep(.el-table__header-wrapper th.el-table__cell) {
  border-bottom: none;
}

:deep(.el-table__header th:first-child) {
  border-top-left-radius: 0;
}

:deep(.el-table__header th:last-child) {
  border-top-right-radius: 0;
}

:deep(.el-table__body) {
  background: white;
}

:deep(.el-table__row) {
  transition: all 0.3s ease;
  border-bottom: 1px solid #F0F2F5 !important;
}

:deep(.el-table__row:hover) {
  background: linear-gradient(135deg, #F0F9FF 0%, #E6F7FF 100%) !important;
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

:deep(.el-table__row[aria-disabled="true"]) {
  cursor: not-allowed !important;
  opacity: 0.6;
  background: #FAFAFA !important;
}

:deep(.el-table__row[aria-disabled="true"]:hover) {
  background: #FAFAFA !important;
  transform: none;
  box-shadow: none;
}

:deep(.el-table td) {
  padding: 16px 12px !important;
  border-bottom: 1px solid #F0F2F5 !important;
  font-size: 14px !important;
  color: #303133 !important;
}

:deep(.el-table td .cell) {
  line-height: 1.5;
}

/* 按钮样式优化 */
:deep(.el-button) {
  border-radius: 6px !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  padding: 8px 16px !important;
  font-size: 13px !important;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%) !important;
  border: none !important;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #337ecc 0%, #5dade2 100%) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3) !important;
}

:deep(.el-button--success) {
  background: linear-gradient(135deg, #67C23A 0%, #85CE61 100%) !important;
  border: none !important;
}

:deep(.el-button--success:hover) {
  background: linear-gradient(135deg, #5daf34 0%, #7bc658 100%) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3) !important;
}

:deep(.el-button--warning) {
  background: linear-gradient(135deg, #E6A23C 0%, #F0C78A 100%) !important;
  border: none !important;
}

:deep(.el-button--warning:hover) {
  background: linear-gradient(135deg, #d39e33 0%, #edc07a 100%) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.3) !important;
}

:deep(.el-button--danger) {
  background: linear-gradient(135deg, #F56C6C 0%, #F78989 100%) !important;
  border: none !important;
}

:deep(.el-button--danger:hover) {
  background: linear-gradient(135deg, #f45656 0%, #f67c7c 100%) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3) !important;
}

:deep(.el-button:disabled) {
  opacity: 0.5 !important;
  transform: none !important;
  box-shadow: none !important;
}

/* 状态标签样式 */
:deep(.el-tag--success) {
  background: linear-gradient(135deg, #67C23A 0%, #85CE61 100%) !important;
  border: none !important;
  color: white !important;
}

:deep(.el-tag--warning) {
  background: linear-gradient(135deg, #E6A23C 0%, #F0C78A 100%) !important;
  border: none !important;
  color: white !important;
}

:deep(.el-tag--danger) {
  background: linear-gradient(135deg, #F56C6C 0%, #F78989 100%) !important;
  border: none !important;
  color: white !important;
}

:deep(.el-tag--info) {
  background: linear-gradient(135deg, #909399 0%, #B1B3B8 100%) !important;
  border: none !important;
  color: white !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  :deep(.el-table__header th),
  :deep(.el-table td) {
    padding: 12px 8px !important;
    font-size: 13px !important;
  }
  
  :deep(.el-button) {
    padding: 6px 12px !important;
    font-size: 12px !important;
  }
  
  .status-tag {
    padding: 2px 8px !important;
    font-size: 11px !important;
  }
}

/* 查看报告文字链接样式 */
.view-report-link {
  color: #409EFF;
  cursor: pointer;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  padding: 4px 8px;
  border-radius: 4px;
}

.view-report-link:hover {
  color: #337ecc;
  background-color: rgba(64, 158, 255, 0.1);
  text-decoration: underline;
}

.view-report-link.disabled {
  color: #C0C4CC;
  cursor: not-allowed;
  text-decoration: none;
}

.view-report-link.disabled:hover {
  color: #C0C4CC;
  background-color: transparent;
  text-decoration: none;
}

@media (max-width: 480px) {
  :deep(.el-table__header th),
  :deep(.el-table td) {
    padding: 8px 6px !important;
    font-size: 12px !important;
  }
  
  .view-report-link {
    font-size: 12px !important;
    padding: 2px 4px !important;
  }
}
</style>