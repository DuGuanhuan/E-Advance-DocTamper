<template>
  <div class="analysis-report">
    <!-- 面包屑导航 -->
    <div class="breadcrumb">
      <router-link to="/" class="breadcrumb-link">审核任务</router-link>
      <span class="breadcrumb-separator">></span>
      <span class="breadcrumb-current">分析报告</span>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-container">
      <el-icon class="is-loading"><Loading /></el-icon>
      <p>正在加载分析报告...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <el-icon><Warning /></el-icon>
      <p>{{ error }}</p>
      <el-button @click="loadReport">重新加载</el-button>
    </div>


    <!-- 报告内容 -->
    <div v-else class="report-content">
      <div class="card">
        <div class="card-header">
          分析报告 - {{ reportData?.uploaded_image?.filename || '未知文件' }} (任务ID: {{ reportData?.task_id || route.params.taskId }})
        </div>

        <div class="analysis-container">
          <!-- 本次上传图片 -->
          <div class="image-display">
            <div class="image-title">本次上传图片</div>
            <div v-if="reportData && reportData.uploaded_image" class="image-container" @click="previewImage(reportData.uploaded_image.url)">
              <img 
                :src="reportData.uploaded_image.url" 
                :alt="reportData.uploaded_image.filename"
                class="analysis-image"
              />
              <div class="image-overlay">
                <el-icon class="zoom-icon"><ZoomIn /></el-icon>
                <span>点击查看大图</span>
              </div>
            </div>
            <div v-else class="no-image">
              <el-icon class="no-image-icon"><Picture /></el-icon>
              <span>暂无图片</span>
            </div>
          </div>

          <!-- 历史相似图片 (条件显示) -->
          <div v-if="shouldShowHistoricalPanel" class="image-display">
            <div class="image-title">
              历史相似图片 ({{ topMatch.filename }})
            </div>
            <div class="image-container" @click="previewImage(topMatch.url)">
              <img 
                :src="topMatch.url" 
                :alt="topMatch.filename"
                class="analysis-image"
              />
              <div class="image-overlay">
                <el-icon class="zoom-icon"><ZoomIn /></el-icon>
                <span>点击放大</span>
              </div>
            </div>
          </div>

          <!-- 检测结果详情 -->
          <div class="findings-card">
            <div class="card-header">检测结果详情</div>
            <div class="findings-list">
              <!-- 历史相似度比对 (条件显示) -->
              <div v-if="shouldShowHistoricalPanel" class="finding-item">
                <strong>历史相似度比对:</strong>
                <span v-html="highlightRisks(topMatch.diff_details)"></span>
              </div>
              
              <!-- AI检测结果 -->
              <div 
                v-for="finding in reportData?.analysis_result?.ai_findings || []" 
                :key="finding.type"
                class="finding-item"
              >
                <strong>{{ finding.type }}:</strong>
                <span v-html="highlightRisks(finding.detail)"></span>
              </div>
            </div>
          </div>

          <!-- 调试信息 -->
          <div style="background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 4px;">
            <p><strong>调试信息:</strong></p>
            <p>任务状态: {{ reportData?.status }}</p>
            <p>showConfirmModal: {{ showConfirmModal }}</p>
            <p>按钮应该显示: {{ reportData?.status === 'pending_review' }}</p>
          </div>

          <!-- 操作按钮 -->
          <div class="feedback-actions">
            <el-button 
              v-if="reportData?.status === 'pending_review'"
              class="btn btn-secondary"
              @click="markAsSafe"
              :loading="isSubmitting"
            >
              标记为无风险
            </el-button>
            <el-button 
              v-if="reportData?.status === 'pending_review'"
              class="btn btn-danger"
              @click="handleShowConfirmModal"
              :loading="isSubmitting"
            >
              确认伪造并归档
            </el-button>
            <div v-else class="status-info">
              <el-icon><InfoFilled /></el-icon>
              <span>该任务已完成审核</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="showImagePreview"
      title="图片预览"
      width="80%"
      center
    >
      <div class="image-preview-container">
        <img :src="previewImageUrl" alt="预览图片" class="preview-image" />
      </div>
    </el-dialog>

    <!-- 确认伪造弹窗 -->
    <ConfirmationModal
      v-if="showConfirmModal"
      :visible="showConfirmModal"
      :task-id="reportData?.task_id"
      :image-url="reportData?.uploaded_image?.url"
      @update:visible="showConfirmModal = $event"
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
const isLoading = ref(true)
const error = ref(null)
const isSubmitting = ref(false)
const showImagePreview = ref(false)
const previewImageUrl = ref('')
const showConfirmModal = ref(false)

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

// 方法
const loadReport = async () => {
  try {
    isLoading.value = true
    error.value = null
    
    const taskId = route.params.taskId
    console.log('Loading report for task:', taskId)
    
    // 使用taskAPI.getTask方法，axios拦截器已经返回了response.data
    const response = await taskAPI.getTask(taskId)
    
    if (response) {
      reportData.value = response
      
      // 设置页面标题
      if (response.uploaded_image?.filename) {
        document.title = `分析报告 - ${response.uploaded_image.filename} - 内审图像鉴伪辅助平台`
      } else {
        document.title = `分析报告 - ${taskId} - 内审图像鉴伪辅助平台`
      }
    } else {
      console.error('❌ API response data is empty')
      error.value = 'API返回数据为空'
    }
  } catch (err) {
    console.error('❌ 加载报告失败:', err)
    error.value = err.response?.data?.detail || '加载报告失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}

const highlightRisks = (text) => {
  if (!text) return ''
  
  // 高亮风险关键词
  const riskKeywords = [
    '篡改', '伪造', '修改', '涂抹', '填充', '不一致', '不符', 
    'Photoshop', '像素级别', '二次', '痕迹', '异常'
  ]
  
  let highlightedText = text
  riskKeywords.forEach(keyword => {
    const regex = new RegExp(`(${keyword})`, 'gi')
    highlightedText = highlightedText.replace(regex, '<span class="risk-highlight">$1</span>')
  })
  
  return highlightedText
}

const previewImage = (url) => {
  previewImageUrl.value = url
  showImagePreview.value = true
}

const markAsSafe = async () => {
  try {
    await ElMessageBox.confirm(
      '确认将此任务标记为无风险？',
      '确认操作',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    isSubmitting.value = true
    await taskAPI.markTaskSafe(reportData.value?.task_id)
    
    ElMessage.success('已标记为无风险')
    router.push('/')
  } catch (err) {
    if (err !== 'cancel') {
      console.error('标记失败:', err)
      ElMessage.error(err.response?.data?.detail || '操作失败')
    }
  } finally {
    isSubmitting.value = false
  }
}

const handleShowConfirmModal = () => {
  console.log('点击确认伪造按钮')
  console.log('当前任务状态:', reportData.value?.status)
  console.log('showConfirmModal 当前值:', showConfirmModal.value)
  showConfirmModal.value = true
  console.log('showConfirmModal 设置后值:', showConfirmModal.value)
}

const handleConfirmSuccess = () => {
  showConfirmModal.value = false
  ElMessage.success('已确认伪造并归档')
  router.push('/')
}

// 生命周期
onMounted(() => {
  loadReport()
})
</script>

<style scoped>
/* 全局样式变量 */
:root {
  --primary-color: #4A90E2;
  --secondary-color: #F5F7FA;
  --border-color: #DCE1E6;
  --text-color: #333;
  --text-light-color: #777;
  --high-risk-color: #D0021B;
  --font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
  --card-shadow: 0 4px 12px rgba(0,0,0,0.08);
  --border-radius: 8px;
}

.analysis-report {
  font-family: var(--font-family);
  background-color: var(--secondary-color);
  color: var(--text-color);
  line-height: 1.6;
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

/* 面包屑导航 */
.breadcrumb {
  margin-bottom: 16px;
  font-size: 14px;
}

.breadcrumb-link {
  color: var(--primary-color);
  text-decoration: none;
}

.breadcrumb-link:hover {
  text-decoration: underline;
}

.breadcrumb-separator {
  color: var(--text-light-color);
  margin: 0 8px;
}

.breadcrumb-current {
  color: var(--text-light-color);
}

/* 加载和错误状态 */
.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.loading-container .el-icon {
  font-size: 32px;
  color: var(--primary-color);
  margin-bottom: 16px;
}

.error-container .el-icon {
  font-size: 32px;
  color: var(--high-risk-color);
  margin-bottom: 16px;
}

/* 卡片样式 */
.card {
  background-color: #fff;
  border-radius: var(--border-radius);
  box-shadow: var(--card-shadow);
  padding: 24px;
  margin-top: 24px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 12px;
}

/* 分析容器 */
.analysis-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

/* 图片显示区域 */
.image-display {
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 10px;
}

.image-title {
  text-align: center;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-light-color);
}

.image-container {
  position: relative;
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
  background-color: #f8f9fa;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.analysis-image {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  transition: transform 0.3s ease;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-container:hover .image-overlay {
  opacity: 1;
}

.image-container:hover .analysis-image {
  transform: scale(1.05);
}

.zoom-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

/* 检测结果 */
.findings-card {
  grid-column: 1 / -1;
  margin-top: 16px;
}

.findings-card .card-header {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border: none;
  padding-left: 0;
  padding-right: 0;
}

.findings-list .finding-item {
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.findings-list .finding-item:last-child {
  border-bottom: none;
}

.finding-item strong {
  color: var(--text-color);
  min-width: 140px;
  display: inline-block;
}

.finding-item span {
  color: var(--text-color);
}

/* 风险高亮 */
:deep(.risk-highlight) {
  color: var(--high-risk-color);
  font-weight: bold;
  background-color: rgba(208, 2, 27, 0.1);
  padding: 2px 4px;
  border-radius: 3px;
}

/* 操作按钮 */
.feedback-actions {
  grid-column: 1 / -1;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
  text-align: right;
}

.btn {
  background-color: var(--primary-color);
  color: #fff;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: background-color 0.3s, transform 0.1s;
  margin-left: 12px;
}

.btn:hover {
  background-color: #357ABD;
}

.btn-danger {
  background-color: var(--high-risk-color);
}

.btn-danger:hover {
  background-color: #A80015;
}

.btn-secondary {
  background-color: #fff;
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
  margin-right: 12px;
  margin-left: 0;
}

.btn-secondary:hover {
  background-color: #EBF2FA;
}

.status-info {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-light-color);
  font-size: 16px;
}

.status-info .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

/* 图片预览 */
.image-preview-container {
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
}

/* 响应式设计 */
@media (max-width: 900px) {
  .analysis-container {
    grid-template-columns: 1fr;
  }
  
  .analysis-report {
    padding: 16px;
  }
  
  .card {
    padding: 16px;
  }
  
  .feedback-actions {
    text-align: center;
  }
  
  .btn {
    display: block;
    width: 100%;
    margin: 8px 0;
  }
  
  .btn-secondary {
    margin-right: 0;
  }
}
</style>