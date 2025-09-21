<template>
  <div class="container">
    <div class="page-header">
      <h2>审核任务列表</h2>
      <el-button type="primary" @click="showNewTaskModal = true">
        <el-icon><Plus /></el-icon>
        新建审核任务
      </el-button>
    </div>

    <div class="card white-card">
      <!-- 筛选栏 -->
      <FilterBar @filter="handleFilter" />
      
      <!-- 任务表格 -->
      <TaskTable :tasks="tasks" />
      
      <!-- 分页 -->
      <div v-if="total > 0" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
      
      <!-- 空状态 -->
      <el-empty 
        v-if="!loading && tasks.length === 0" 
        description="暂无任务数据"
        :image-size="120"
      />
    </div>

    <!-- 新建任务弹窗 -->
    <NewTaskModal 
      v-model="showNewTaskModal" 
      @success="handleTaskCreated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import FilterBar from '../components/FilterBar.vue'
import TaskTable from '../components/TaskTable.vue'
import NewTaskModal from '../components/NewTaskModal.vue'
import { taskAPI } from '../utils/api'

// 响应式数据
const tasks = ref([])
const loading = ref(false)
const showNewTaskModal = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterParams = ref({})

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      ...filterParams.value
    }
    
    const response = await taskAPI.getTasks(params)
    
    if (Array.isArray(response)) {
      // 如果返回的是数组，说明没有分页信息
      tasks.value = response
      total.value = response.length
    } else {
      // 如果返回的是对象，包含分页信息
      tasks.value = response.tasks || response.items || response.data || []
      total.value = response.total || tasks.value.length
    }
  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 处理筛选
const handleFilter = (params) => {
  filterParams.value = params
  currentPage.value = 1
  fetchTasks()
}

// 处理页码变化
const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchTasks()
}

// 处理页大小变化
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchTasks()
}

// 处理任务创建成功
const handleTaskCreated = (results) => {
  // 兼容单个/多个
  if (Array.isArray(results)) {
    if (results.length === 1) {
      ElMessage.success(`任务 ${results[0].task_id} 创建成功`)
    } else {
      ElMessage.success(`已创建 ${results.length} 个任务`)
    }
  } else if (results && results.task_id) {
    ElMessage.success(`任务 ${results.task_id} 创建成功`)
  } else {
    ElMessage.success('任务创建成功')
  }
  fetchTasks()
}

// 组件挂载时获取数据
onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  background: transparent;
  min-height: 100vh;
  font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

.page-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 24px; 
  background: #fff !important; 
  padding: 24px; 
  border-radius: 12px; 
  box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
  border: 1px solid #E4E7ED; 
  animation: fadeInUp 0.6s ease-out; 
  backdrop-filter: none; 
  -webkit-backdrop-filter: none; 
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  position: relative;
}


.page-header .el-button {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 6px;
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  border: none;
  transition: all 0.3s ease;
}

.page-header .el-button:hover {
  background: linear-gradient(135deg, #337ecc 0%, #5dade2 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.3);
}

.card {
  overflow: hidden;
  animation: fadeInUp 0.6s ease-out 0.1s both;
}

.white-card { background:#fff !important; border:1px solid #E4E7ED; box-shadow: 0 4px 12px rgba(0,0,0,0.08); backdrop-filter:none; -webkit-backdrop-filter:none; }

.pagination-wrapper {
  margin-top: 24px;
  padding: 20px 24px;
  display: flex;
  justify-content: center;
  background: #FAFCFF;
  border-top: 1px solid #E4E7ED;
}

:deep(.el-pagination) {
  justify-content: center;
}

:deep(.el-pagination .el-pager li) {
  background: white;
  border: 1px solid #DCDFE6;
  margin: 0 2px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

:deep(.el-pagination .el-pager li:hover) {
  background: #F0F9FF;
  border-color: #409EFF;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  border-color: #409EFF;
  color: white;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background: white;
  border: 1px solid #DCDFE6;
  border-radius: 4px;
  transition: all 0.3s ease;
}

:deep(.el-pagination .btn-prev:hover),
:deep(.el-pagination .btn-next:hover) {
  background: #F0F9FF;
  border-color: #409EFF;
  color: #409EFF;
}

:deep(.el-empty) {
  padding: 60px 20px;
}

:deep(.el-empty__description) {
  color: #909399;
  font-size: 16px;
  margin-top: 16px;
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
    padding: 16px;
  }
  
  .page-header h2 {
    font-size: 20px;
  }
  
  .page-header .el-button {
    width: 100%;
    justify-content: center;
  }
  
  .pagination-wrapper {
    padding: 16px;
  }
  
  :deep(.el-pagination) {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  :deep(.el-pagination .el-pagination__sizes),
  :deep(.el-pagination .el-pagination__jump) {
    margin: 4px 0;
  }
}

@media (max-width: 480px) {
  .container {
    padding: 12px;
  }
  
  .page-header {
    padding: 12px;
  }
  
  .page-header h2 {
    font-size: 18px;
  }
  
  :deep(.el-pagination) {
    justify-content: center;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }
}
</style>