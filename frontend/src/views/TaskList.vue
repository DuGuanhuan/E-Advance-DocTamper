<template>
  <div class="container">
    <div class="page-header">
      <h2>审核任务列表</h2>
      <el-button type="primary" @click="showNewTaskModal = true">
        <el-icon><Plus /></el-icon>
        新建审核任务
      </el-button>
    </div>

    <div class="card">
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
const handleTaskCreated = (result) => {
  ElMessage.success(`任务 ${result.task_id} 创建成功`)
  fetchTasks() // 刷新列表
}

// 组件挂载时获取数据
onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

:deep(.el-pagination) {
  justify-content: center;
}
</style>