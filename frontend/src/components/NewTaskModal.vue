<template>
  <el-dialog
    v-model="visible"
    title="新建审核任务"
    width="600px"
    :before-close="handleClose"
  >
    <div class="upload-section">
      <el-upload
        ref="uploadRef"
        :action="uploadAction"
        :auto-upload="false"
        :multiple="true"
        :drag="true"
        :accept="acceptTypes"
        :before-upload="beforeUpload"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :file-list="fileList"
        :show-file-list="false"
      >
        <div class="upload-area">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p>将文件拖拽到此处，或点击选择文件</p>
            <p class="upload-hint">支持 JPG、PNG、PDF 格式，单个文件不超过 10MB</p>
          </div>
        </div>
      </el-upload>
    </div>

    <!-- 文件列表 -->
    <div v-if="fileList.length > 0" class="file-list">
      <div class="file-list-header">
        待上传文件 ({{ fileList.length }})
      </div>
      <div 
        v-for="file in fileList" 
        :key="file.uid" 
        class="file-item"
      >
        <span class="file-icon">{{ getFileIcon(file.raw?.type) }}</span>
        <div class="file-info">
          <div class="file-name">{{ file.name }}</div>
          <div class="file-size">{{ formatFileSize(file.size) }}</div>
        </div>
        <el-button
          type="danger"
          link
          @click="removeFile(file)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="uploading"
          :disabled="fileList.length === 0"
          @click="handleSubmit"
        >
          {{ uploading ? '上传中...' : '提交审核任务' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Delete } from '@element-plus/icons-vue'
import { taskAPI } from '../utils/api'
import { getFileIcon, formatFileSize } from '../utils/constants'

// Props & Emits
const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'success'])

// 响应式数据
const uploadRef = ref()
const fileList = ref([])
const uploading = ref(false)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const uploadAction = '/api/v1/tasks'
const acceptTypes = '.jpg,.jpeg,.png,.pdf'

// 文件上传前验证
const beforeUpload = (file) => {
  const isValidType = ['image/jpeg', 'image/png', 'application/pdf'].includes(file.type)
  const isValidSize = file.size / 1024 / 1024 < 10

  if (!isValidType) {
    ElMessage.error('只支持 JPG、PNG、PDF 格式的文件')
    return false
  }
  if (!isValidSize) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

// 文件变化处理
const handleFileChange = (file, files) => {
  fileList.value = files
}

// 文件移除处理
const handleFileRemove = (file, files) => {
  fileList.value = files
}

// 移除文件
const removeFile = (file) => {
  const index = fileList.value.findIndex(f => f.uid === file.uid)
  if (index > -1) {
    fileList.value.splice(index, 1)
  }
}

// 提交上传
const handleSubmit = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  uploading.value = true
  
  try {
    // 逐文件创建任务：一张图片 = 一个任务
    const results = []
    for (const file of fileList.value) {
      const form = new FormData()
      form.append('files', file.raw)
      try {
        const res = await taskAPI.createTask(form)
        results.push(res)
      } catch (err) {
        console.error('创建任务失败:', file.name, err)
      }
    }

    if (results.length > 0) {
      if (results.length === 1) {
        ElMessage.success(`任务 ${results[0].task_id} 创建成功`)
      } else {
        ElMessage.success(`已创建 ${results.length} 个任务`)
      }
      emit('success', results)
    } else {
      ElMessage.error('创建任务失败，请重试')
      return
    }
    handleClose()
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
  }
}

// 关闭弹窗
const handleClose = () => {
  fileList.value = []
  uploading.value = false
  visible.value = false
}
</script>

<style scoped>
.upload-section {
  margin-bottom: 20px;
}

.upload-area {
  padding: 40px;
  text-align: center;
  border: 2px dashed var(--border-color);
  border-radius: var(--border-radius);
  background-color: #F8F9FA;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: var(--primary-color);
  background-color: #EBF2FA;
}

.upload-icon {
  font-size: 48px;
  color: var(--primary-color);
  margin-bottom: 16px;
}

.upload-text p {
  margin: 8px 0;
  color: var(--text-color);
}

.upload-hint {
  font-size: 14px;
  color: var(--text-light-color);
}

.file-list {
  margin-top: 20px;
}

.file-list-header {
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.file-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background-color: #F8F9FA;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 8px;
}

.file-icon {
  margin-right: 12px;
  font-size: 24px;
}

.file-info {
  flex-grow: 1;
}

.file-name {
  font-weight: 500;
  color: var(--text-color);
}

.file-size {
  font-size: 12px;
  color: var(--text-light-color);
}

.dialog-footer {
  text-align: right;
}
</style>
