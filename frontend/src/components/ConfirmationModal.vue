<template>
  <el-dialog 
    :model-value="visible" 
    @update:model-value="$emit('update:visible', $event)"
    title="确认伪造并归档案例"
    width="960px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="confirmation-modal"
  >
    <template #default>
      <div class="modal-body">
        <!-- 左侧：图像标注区 -->
        <div class="image-annotation-area">
          <h4>1. 框选伪造区域 (可选)</h4>
          <div 
            class="image-container"
            ref="imageContainerRef"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"
            @mouseleave="onMouseUp"
          >
            <img 
              v-if="imageUrl" 
              :src="imageUrl" 
              alt="待标注图片"
              class="annotation-image"
              ref="annotationImageRef"
              draggable="false"
            />
            <div v-else class="image-placeholder">
              <el-icon class="placeholder-icon"><Picture /></el-icon>
              <p>暂无图片</p>
            </div>
            
            <!-- 已完成的标注框 -->
            <div 
              v-for="box in boundingBoxes" 
              :key="box.id" 
              class="bounding-box"
              :style="getBoxStyle(box)"
              @click="removeBox(box.id)"
              :title="'点击删除标注框 #' + box.id"
            />
            
            <!-- 正在绘制的临时标注框 -->
            <div 
              v-if="drawingBox" 
              class="bounding-box drawing"
              :style="getBoxStyle(drawingBox)"
            />
          </div>
          <p class="annotation-instruction">
            请在图片上拖拽鼠标，框选出关键的伪造区域
          </p>
        </div>
        
        <!-- 右侧：信息表单区 -->
        <div class="form-area">
          <h4>2. 选择伪造类型并说明</h4>
          
          <div class="form-group">
            <label>伪造类型 (可多选)</label>
            <div class="tags-container">
              <button 
                v-for="type in FORGERY_OPTIONS" 
                :key="type"
                class="tag-btn"
                :class="{ selected: selectedForgeryTypes.includes(type) }"
                @click="toggleForgeryType(type)"
                type="button"
              >
                {{ type }}
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label>补充说明 (可选)</label>
            <textarea 
              v-model="supplementaryNotes"
              placeholder="请填写详细的判断依据，例如：金额'8'由'3'修改而来，边缘有模糊痕迹..."
              maxlength="500"
            ></textarea>
            <div class="char-count">{{ supplementaryNotes.length }}/500</div>
          </div>
          
          <!-- 标注框列表 -->
          <div v-if="boundingBoxes.length > 0" class="form-group">
            <label>已标注区域 ({{ boundingBoxes.length }}个)</label>
            <div class="annotation-list">
              <div 
                v-for="box in boundingBoxes"
                :key="box.id"
                class="annotation-item"
                @click="removeBox(box.id)"
                :title="'点击删除'"
              >
                <span class="annotation-text">区域 {{ box.id }}</span>
                <span class="annotation-size">{{ Math.round(box.width) }}×{{ Math.round(box.height) }}</span>
                <span class="remove-icon">×</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="onClose" :disabled="submitting">
          取消
        </button>
        <button 
          class="btn btn-primary" 
          :disabled="submitting"
          @click="onSubmit"
        >
          <span v-if="submitting">提交中...</span>
          <span v-else>确认归档</span>
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { taskAPI } from '../utils/api'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  taskId: {
    type: String,
    required: true
  },
  imageUrl: {
    type: String,
    required: true
  }
})

// Emits
const emit = defineEmits(['update:visible', 'success'])

// 伪造类型选项
const FORGERY_OPTIONS = [
  '金额篡改',
  '日期修改', 
  '公章伪造',
  '内容拼接',
  '签名伪造',
  '其他'
]

// 响应式状态
const selectedForgeryTypes = ref([])
const supplementaryNotes = ref('')
const boundingBoxes = ref([])
const submitting = ref(false)

// 图像标注相关状态
const imageContainerRef = ref(null)
const annotationImageRef = ref(null)
const isDrawing = ref(false)
const startPoint = ref({ x: 0, y: 0 })
const drawingBox = ref(null)
let nextBoxId = 1

// 切换伪造类型选择
const toggleForgeryType = (type) => {
  const index = selectedForgeryTypes.value.indexOf(type)
  if (index > -1) {
    selectedForgeryTypes.value.splice(index, 1)
  } else {
    selectedForgeryTypes.value.push(type)
  }
}

// 获取相对于容器的鼠标坐标
const getRelativeCoordinates = (event) => {
  if (!imageContainerRef.value) return { x: 0, y: 0 }
  
  const rect = imageContainerRef.value.getBoundingClientRect()
  const x = Math.max(0, Math.min(event.clientX - rect.left, rect.width))
  const y = Math.max(0, Math.min(event.clientY - rect.top, rect.height))
  
  return { x, y }
}

// 鼠标按下事件
const onMouseDown = (event) => {
  event.preventDefault()
  
  const coords = getRelativeCoordinates(event)
  startPoint.value = coords
  isDrawing.value = true
  
  drawingBox.value = {
    id: 'drawing',
    x: coords.x,
    y: coords.y,
    width: 0,
    height: 0
  }
}

// 鼠标移动事件
const onMouseMove = (event) => {
  if (!isDrawing.value || !drawingBox.value) return
  
  event.preventDefault()
  const coords = getRelativeCoordinates(event)
  
  const x = Math.min(startPoint.value.x, coords.x)
  const y = Math.min(startPoint.value.y, coords.y)
  const width = Math.abs(coords.x - startPoint.value.x)
  const height = Math.abs(coords.y - startPoint.value.y)
  
  drawingBox.value = {
    id: 'drawing',
    x,
    y,
    width,
    height
  }
}

// 鼠标抬起事件
const onMouseUp = () => {
  if (!isDrawing.value || !drawingBox.value) return
  
  isDrawing.value = false
  
  // 只有当标注框足够大时才添加
  if (drawingBox.value.width > 10 && drawingBox.value.height > 10) {
    const newBox = {
      ...drawingBox.value,
      id: nextBoxId++
    }
    boundingBoxes.value.push(newBox)
  }
  
  drawingBox.value = null
}

// 获取标注框样式
const getBoxStyle = (box) => {
  return {
    left: `${box.x}px`,
    top: `${box.y}px`,
    width: `${box.width}px`,
    height: `${box.height}px`
  }
}

// 删除标注框
const removeBox = (boxId) => {
  const index = boundingBoxes.value.findIndex(box => box.id === boxId)
  if (index > -1) {
    boundingBoxes.value.splice(index, 1)
  }
}

// 重置状态
const resetState = () => {
  selectedForgeryTypes.value = []
  supplementaryNotes.value = ''
  boundingBoxes.value = []
  drawingBox.value = null
  isDrawing.value = false
  submitting.value = false
  nextBoxId = 1
}

// 关闭弹窗
const onClose = () => {
  if (submitting.value) return
  
  emit('update:visible', false)
  // 延迟重置状态，避免关闭动画时看到状态变化
  setTimeout(resetState, 300)
}

// 提交表单
const onSubmit = async () => {
  try {
    submitting.value = true
    
    // 构建请求数据
    // 将标注框归一化到图片显示区域的比例坐标，避免不同分辨率偏差
    const payload = {
      is_forgery: true,
      forgery_types: selectedForgeryTypes.value,
      notes: supplementaryNotes.value,
      annotations: (() => {
        try {
          const container = imageContainerRef.value
          const imgEl = annotationImageRef.value
          if (!container || !imgEl) return []
          const cRect = container.getBoundingClientRect()
          const iRect = imgEl.getBoundingClientRect()
          const offsetX = iRect.left - cRect.left
          const offsetY = iRect.top - cRect.top
          const imgW = iRect.width || cRect.width || 1
          const imgH = iRect.height || cRect.height || 1

          const toRatio = (b) => {
            // 将容器内像素坐标转换为图片区域内的比例坐标（0-1）
            const x = (b.x - offsetX) / imgW
            const y = (b.y - offsetY) / imgH
            const w = b.width / imgW
            const h = b.height / imgH
            const clamp = (v) => Math.max(0, Math.min(1, v))
            const safe = (v) => Number.isFinite(v) ? v : 0
            return {
              x: clamp(Number(safe(x).toFixed(6))),
              y: clamp(Number(safe(y).toFixed(6))),
              width: clamp(Number(safe(w).toFixed(6))),
              height: clamp(Number(safe(h).toFixed(6)))
            }
          }
          return (boundingBoxes.value || []).map(toRatio)
        } catch (e) {
          // 任意异常时回退为空列表，避免提交阻断
          return []
        }
      })()
    }
    
    // 调用API
    await taskAPI.confirmTask(props.taskId, payload)
    
    ElMessage.success('任务已确认为伪造并归档')
    emit('success')
    emit('update:visible', false)
    
    // 重置状态
    setTimeout(resetState, 300)
    
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败: ' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

// 监听弹窗打开，重置状态
watch(() => props.visible, (newValue) => {
  if (newValue) {
    nextTick(() => {
      resetState()
    })
  }
})
</script>

<style scoped>
/* 弹窗整体样式 */
:deep(.confirmation-modal .el-dialog) {
  border-radius: 8px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}

:deep(.confirmation-modal .el-dialog__header) {
  padding: 16px 24px;
  border-bottom: 1px solid #DCE1E6;
  background-color: #fff;
}

:deep(.confirmation-modal .el-dialog__title) {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

:deep(.confirmation-modal .el-dialog__body) {
  padding: 0;
}

:deep(.confirmation-modal .el-dialog__footer) {
  padding: 0;
}

/* 弹窗主体 */
.modal-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  padding: 24px;
}

/* 左侧图片标注区 */
.image-annotation-area h4 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.image-container {
  position: relative;
  border: 1px solid #DCE1E6;
  border-radius: 6px;
  overflow: hidden;
  background-color: #f8f9fa;
  cursor: crosshair;
  user-select: none;
}

.annotation-image {
  display: block;
  width: 100%;
  height: auto;
  max-height: 400px;
  object-fit: contain;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #999;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

/* 标注框样式 */
.bounding-box {
  position: absolute;
  border: 2px solid #D0021B;
  background-color: rgba(208, 2, 27, 0.2);
  cursor: pointer;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.bounding-box:hover {
  border-color: #ff4757;
  background-color: rgba(255, 71, 87, 0.3);
}

.bounding-box.drawing {
  border-style: dashed;
  cursor: crosshair;
}

.annotation-instruction {
  font-size: 12px;
  color: #777;
  text-align: center;
  margin-top: 8px;
  line-height: 1.4;
}

/* 右侧表单区 */
.form-area h4 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
  font-size: 14px;
}

/* 标签容器 */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-btn {
  background-color: #F5F7FA;
  border: 1px solid #DCE1E6;
  padding: 6px 14px;
  border-radius: 16px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  outline: none;
}

.tag-btn:hover {
  background-color: #eef7ff;
  border-color: #4A90E2;
}

.tag-btn.selected {
  background-color: #4A90E2;
  color: #fff;
  border-color: #4A90E2;
}

/* 文本域 */
.form-group textarea {
  width: 100%;
  min-height: 80px;
  padding: 10px;
  border: 1px solid #DCE1E6;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.form-group textarea:focus {
  border-color: #4A90E2;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* 标注列表 */
.annotation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.annotation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.annotation-item:hover {
  background-color: #e9ecef;
  border-color: #D0021B;
}

.annotation-text {
  font-weight: 500;
  color: #333;
}

.annotation-size {
  font-size: 12px;
  color: #666;
}

.remove-icon {
  color: #D0021B;
  font-weight: bold;
  font-size: 16px;
}

/* 底部按钮 */
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #DCE1E6;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background-color: #F5F7FA;
}

.btn {
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  border: none;
  transition: all 0.2s;
  outline: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #fff;
  color: #555;
  border: 1px solid #DCE1E6;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #f8f9fa;
  border-color: #adb5bd;
}

.btn-primary {
  background-color: #D0021B;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background-color: #b8001a;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-body {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
  }
  
  .image-container {
    min-height: 200px;
  }
  
  .annotation-image {
    max-height: 250px;
  }
  
  .tags-container {
    gap: 8px;
  }
  
  .tag-btn {
    padding: 4px 10px;
    font-size: 13px;
  }
}
</style>
