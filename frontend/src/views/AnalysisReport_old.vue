<template>
  <div class="container">
    <!-- 面包屑导航 -->
    <el-breadcrumb class="breadcrumb" separator=">">
      <el-breadcrumb-item>
        <router-link to="/">审核任务</router-link>
      </el-breadcrumb-item>
      <el-breadcrumb-item>分析报告</el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <el-result
        icon="error"
        title="加载失败"
        :sub-title="error"
      >
        <template #extra>
          <el-button type="primary" @click="loadReport">重新加载</el-button>
          <el-button @click="$router.push('/')">返回任务列表</el-button>
        </template>
      </el-result>
    </div>

    <!-- 主要内容 -->
    <div v-else-if="reportData" class="card">
      <!-- 页面标题 -->
      <h1 class="page-title">
        分析报告 - {{ reportData.uploaded_image?.filename }} (任务ID: {{ reportData.task_id }})
      </h1>
      
      <!-- 图片对比区域 -->
      <el-row :gutter="24" class="image-comparison">
        <!-- 本次上传图片 -->
        <el-col :span="shouldShowHistoricalPanel ? 12 : 24">
          <div class="image-display">
            <div class="image-title">本次上传图片</div>
            <div class="image-container">
              <el-image
                v-if="reportData.uploaded_image?.url"
                :src="reportData.uploaded_image.url"
                :alt="reportData.uploaded_image.filename"
                fit="contain"
                class="uploaded-image"
                :preview-src-list="[reportData.uploaded_image.url]"
              />
              <div v-else class="image-placeholder">
                <el-icon class="placeholder-icon"><Picture /></el-icon>
                <p class="placeholder-text">图片预览区域</p>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 历史相似图片 - 条件渲染 -->
        <el-col v-if="shouldShowHistoricalPanel" :span="12">
          <div class="image-display">
            <div class="image-title">
              历史相似图片 ({{ topMatch.filename }})
            </div>
            <div class="image-container">
              <el-image
                :src="topMatch.url"
                :alt="topMatch.filename"
                fit="contain"
                class="historical-image"
                :preview-src-list="[topMatch.url]"
              />
              <div class="similarity-badge">
                相似度: {{ (topMatch.similarity * 100).toFixed(1) }}%
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 检测结果详情 -->
      <div class="findings-section">
        <h3 class="section-title">检测结果详情</h3>
        <div class="findings-list">
          <!-- 历史相似度比对 - 条件渲染 -->
          <div v-if="shouldShowHistoricalPanel" class="finding-item">
            <strong>历史相似度比对:</strong>
            <span class="finding-content risk">{{ topMatch.diff_details }}</span>
          </div>
          
          <!-- AI检测结果 -->
          <div 
            v-for="finding in reportData.analysis_result.ai_findings" 
            :key="finding.type"
            class="finding-item"
          >
            <strong>{{ finding.type }}:</strong>
            <span 
              class="finding-content"
              :class="{ 'risk': isRiskFinding(finding.detail) }"
            >
              {{ finding.detail }}
            </span>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button 
          class="btn-secondary"
          :disabled="!canPerformAction"
          @click="handleMarkSafe"
          :loading="actionLoading"
        >
          标记为无风险
        </el-button>
        <el-button 
          type="danger"
          :disabled="!canPerformAction"
          @click="showConfirmationModal"
          :loading="actionLoading"
        >
          确认伪造并归档
        </el-button>
      </div>
    </div>

    <!-- 确认伪造弹窗 -->
    <ConfirmationModal
      v-model="confirmationModalVisible"
      :task-id="reportData?.task_id"
      :image-url="reportData?.uploaded_image?.url"
      @success="handleConfirmSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { taskAPI } from '../utils/api'
import ConfirmationModal from '../components/ConfirmationModal.vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const reportData = ref(null)
const isLoading = ref(false)
const error = ref(null)
const actionLoading = ref(false)
const confirmationModalVisible = ref(false)

// 计算属性
const topMatch = computed(() => {
  if (!reportData.value?.analysis_result?.historical_matches?.length) {
    return null
  }
  return reportData.value.analysis_result.historical_matches[0]
})

const shouldShowHistoricalPanel = computed(() => {
  if (!topMatch.value) {
    return false
  }
  return topMatch.value.similarity >= 0.90
})

const canPerformAction = computed(() => {
  return reportData.value?.status === 'pending_review'
})

// 方法
const loadReport = async () => {
  try {
    isLoading.value = true
    error.value = null
    
    const taskId = route.params.taskId
    const response = await taskAPI.getTask(taskId)
    
    reportData.value = response
    
    // 设置页面标题
    if (response.uploaded_image?.filename) {
      document.title = `分析报告 - ${response.uploaded_image.filename} - 内审图像鉴伪辅助平台`
    }
    
  } catch (err) {
    console.error('加载报告失败:', err)
    error.value = err.message || '加载报告失败'
    ElMessage.error('加载报告失败')
  } finally {
    isLoading.value = false
  }
}

const isRiskFinding = (detail) => {
  // 判断是否为风险发现
  const riskKeywords = ['篡改', '伪造', '不符', '异常', '痕迹', 'Photoshop', '修改']
  return riskKeywords.some(keyword => detail.includes(keyword))
}

const handleMarkSafe = async () => {
  try {
    await ElMessageBox.confirm(
      '确认将此任务标记为无风险吗？',
      '确认操作',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    actionLoading.value = true
    
    // 调用标记为安全的API
    await taskAPI.markTaskSafe(reportData.value.task_id)
    
    ElMessage.success('已标记为无风险')
    router.push('/')
    
  } catch (err) {
    if (err !== 'cancel') {
      console.error('标记失败:', err)
      ElMessage.error('标记失败: ' + (err.message || '未知错误'))
    }
  } finally {
    actionLoading.value = false
  }
}

const showConfirmationModal = () => {
  confirmationModalVisible.value = true
}

const handleConfirmSuccess = () => {
  ElMessage.success('已确认伪造并归档')
  router.push('/')
}

// 生命周期
onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  background-color: #F5F7FA;
  min-height: 100vh;
  font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

.breadcrumb {
  margin-bottom: 20px;
}

.breadcrumb a {
  color: #409EFF;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.breadcrumb a:hover {
  color: #66b1ff;
}

.loading-container,
.error-container {
  margin-top: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  padding: 40px;
  text-align: center;
}

.card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  padding: 24px;
  margin-top: 24px;
  border: 1px solid #E4E7ED;
  transition: all 0.3s ease;
  animation: fadeInUp 0.6s ease-out;
}

.card:hover {
  box-shadow: 0 8px 25px rgba(0,0,0,0.12);
  transform: translateY(-2px);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #303133;
  position: relative;
  padding-bottom: 16px;
}

.page-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 60px;
  height: 3px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
}

.image-comparison {
  margin-bottom: 32px;
}

.image-display {
  border: 1px solid #DCDFE6;
  border-radius: 8px;
  padding: 20px;
  height: 100%;
  background: #FAFCFF;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.image-display::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.image-display:hover {
  border-color: #C6E2FF;
  background: #F0F9FF;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.image-title {
  text-align: center;
  font-weight: 600;
  margin-bottom: 16px;
  color: #303133;
  font-size: 16px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  display: inline-block;
  margin: 0 auto 16px auto;
  display: block;
  width: fit-content;
}

.image-container {
  position: relative;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  overflow: hidden;
}

.uploaded-image,
.historical-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.uploaded-image:hover,
.historical-image:hover {
  transform: scale(1.03);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 2px dashed #DCDFE6;
  border-radius: 6px;
  color: #909399;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #C0C4CC;
}

.placeholder-text {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.similarity-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: linear-gradient(135deg, #67C23A 0%, #85CE61 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

.findings-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
}

.findings-list {
  background: linear-gradient(135deg, #fafcff 0%, #f0f9ff 100%);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #E4E7ED;
}

.finding-item {
  padding: 16px 0;
  border-bottom: 1px solid #EBEEF5;
  display: flex;
  align-items: flex-start;
  transition: all 0.3s ease;
  position: relative;
}

.finding-item:hover {
  background: rgba(64, 158, 255, 0.05);
  border-radius: 6px;
  padding-left: 8px;
  padding-right: 8px;
}

.finding-item:last-child {
  border-bottom: none;
}

.finding-item strong {
  color: #303133;
  min-width: 160px;
  flex-shrink: 0;
  font-weight: 600;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.finding-item strong::before {
  content: '●';
  color: #409EFF;
  font-size: 12px;
}

.finding-content {
  color: #606266;
  line-height: 1.6;
  margin-left: 12px;
  font-size: 14px;
}

.finding-content.risk {
  color: #F56C6C;
  font-weight: 600;
  background: rgba(245, 108, 108, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
}

.action-buttons {
  padding-top: 24px;
  border-top: 1px solid #E4E7ED;
  text-align: center;
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.3s ease;
  min-width: 140px;
}

.action-buttons .el-button--success {
  background: linear-gradient(135deg, #67C23A 0%, #85CE61 100%);
  border: none;
}

.action-buttons .el-button--success:hover {
  background: linear-gradient(135deg, #5daf34 0%, #7bc658 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(103, 194, 58, 0.3);
}

.action-buttons .el-button--danger {
  background: linear-gradient(135deg, #F56C6C 0%, #F78989 100%);
  border: none;
}

.action-buttons .el-button--danger:hover {
  background: linear-gradient(135deg, #f45656 0%, #f67c7c 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(245, 108, 108, 0.3);
}

.btn-secondary {
  margin-right: 0;
}

/* 面包屑样式优化 */
:deep(.el-breadcrumb) {
  background: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border: 1px solid #E4E7ED;
}

:deep(.el-breadcrumb__item) {
  font-size: 14px;
}

:deep(.el-breadcrumb__inner) {
  color: #606266;
  font-weight: 500;
}

:deep(.el-breadcrumb__inner:hover) {
  color: #409EFF;
}

/* 图片预览对话框优化 */
:deep(.el-image-viewer__wrapper) {
  background-color: rgba(0, 0, 0, 0.8);
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

.card:nth-child(1) {
  animation-delay: 0s;
}

.card:nth-child(2) {
  animation-delay: 0.1s;
}

.card:nth-child(3) {
  animation-delay: 0.2s;
}

.card:nth-child(4) {
  animation-delay: 0.3s;
}

/* 响应式设计 */
@media (max-width: 900px) {
  .container {
    padding: 16px;
  }
  
  .card {
    padding: 16px;
    margin-top: 16px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .section-title {
    font-size: 18px;
  }
  
  .image-comparison .el-col {
    margin-bottom: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-buttons .el-button {
    width: 100%;
    max-width: 200px;
    margin: 4px 0;
  }
  
  .finding-item strong {
    min-width: 120px;
    font-size: 14px;
  }
  
  .finding-content {
    font-size: 13px;
  }
  
  .image-title {
    font-size: 14px;
    padding: 6px 12px;
  }
}

@media (max-width: 600px) {
  .container {
    padding: 12px;
  }
  
  .card {
    padding: 12px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .finding-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .finding-item strong {
    min-width: auto;
    margin-bottom: 4px;
  }
  
  .finding-content {
    margin-left: 0;
  }
}
</style>