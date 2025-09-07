<template>
  <el-dialog 
    v-model="visible" 
    :title="isForgery ? '确认伪造并归档案例' : '标记无风险'" 
    width="860px"
  >
    <template #default>
      <div v-if="isForgery">
        <el-row :gutter="16">
          <el-col :span="12">
            <h4>1. 框选伪造区域 (可选)</h4>
            <div 
              class="image-container"
              ref="imageContainerRef"
              @mousedown="onMouseDown"
              @mousemove="onMouseMove"
              @mouseup="onMouseUp"
              @mouseleave="onMouseUp"
            >
              <img v-if="imageUrl" class="image" :src="imageUrl" alt="待标注图片" />
              <div 
                v-for="box in boundingBoxes" 
                :key="box.id" 
                class="bounding-box"
                :style="styleForBox(box)"
              />
              <div 
                v-if="drawingBox" 
                class="bounding-box temp"
                :style="styleForBox(drawingBox)"
              />
            </div>
          </el-col>
          
          <el-col :span="12">
            <h4>2. 选择伪造类型并说明</h4>
            <el-form label-width="120px">
              <el-form-item label="伪造类型 (可多选)">
                <el-checkbox-group v-model="selectedForgeryTypes">
                  <el-checkbox-button v-for="opt in FORGERY_OPTIONS" :label="opt" :key="opt">{{ opt }}</el-checkbox-button>
                </el-checkbox-group>
              </el-form-item>
              <el-form-item label="补充说明 (可选)">
                <el-input v-model="notes" type="textarea" :rows="6" placeholder="可填写审核意见或说明" />
              </el-form-item>
            </el-form>
          </el-col>
        </el-row>
      </div>
      <div v-else>
        <p class="hint">将此任务标记为无风险（可填写审核说明）。</p>
        <el-input v-model="notes" type="textarea" :rows="6" placeholder="审核说明（可选）" />
      </div>
    </template>

    <template #footer>
      <el-button @click="onClose">取消</el-button>
      <el-button 
        :type="isForgery ? 'danger' : 'primary'" 
        :loading="submitting" 
        @click="onSubmit"
      >
        {{ isForgery ? '确认归档' : '确认提交' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { taskAPI } from '../utils/api'

const props = defineProps({
  modelValue: Boolean,
  isForgery: { type: Boolean, default: true },
  taskId: { type: String, required: true },
  imageUrl: { type: String, required: false, default: '' }
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

// 伪造类型选项
const FORGERY_OPTIONS = [
  '金额篡改', '日期修改', '公章伪造', '内容拼接', '签名伪造', '其他'
]

// 内部状态
const selectedForgeryTypes = ref([])
const notes = ref('')
const boundingBoxes = ref([]) // {id,x,y,width,height}

// 绘制相关
const imageContainerRef = ref(null)
const isDrawing = ref(false)
const startPoint = ref({ x: 0, y: 0 })
const drawingBox = ref(null)
let nextId = 1

function getRelativePoint(e) {
  const rect = imageContainerRef.value?.getBoundingClientRect()
  const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
  const y = Math.max(0, Math.min(e.clientY - rect.top, rect.height))
  return { x, y }
}

function onMouseDown(e) {
  if (!props.isForgery) return
  isDrawing.value = true
  startPoint.value = getRelativePoint(e)
  drawingBox.value = { id: 'temp', x: startPoint.value.x, y: startPoint.value.y, width: 0, height: 0 }
}

function onMouseMove(e) {
  if (!isDrawing.value || !drawingBox.value) return
  const p = getRelativePoint(e)
  const x = Math.min(startPoint.value.x, p.x)
  const y = Math.min(startPoint.value.y, p.y)
  const w = Math.abs(p.x - startPoint.value.x)
  const h = Math.abs(p.y - startPoint.value.y)
  drawingBox.value = { id: 'temp', x, y, width: w, height: h }
}

function onMouseUp() {
  if (!isDrawing.value) return
  isDrawing.value = false
  if (drawingBox.value && drawingBox.value.width > 4 && drawingBox.value.height > 4) {
    boundingBoxes.value.push({ ...drawingBox.value, id: String(nextId++) })
  }
  drawingBox.value = null
}

function styleForBox(box) {
  return {
    left: box.x + 'px',
    top: box.y + 'px',
    width: box.width + 'px',
    height: box.height + 'px'
  }
}

function resetState() {
  selectedForgeryTypes.value = []
  notes.value = ''
  boundingBoxes.value = []
  drawingBox.value = null
  isDrawing.value = false
  nextId = 1
}

function onClose() {
  visible.value = false
}

async function onSubmit() {
  if (!props.taskId) return
  const payload = props.isForgery
    ? {
        is_forgery: true,
        forgery_types: selectedForgeryTypes.value,
        notes: notes.value,
        annotations: boundingBoxes.value
      }
    : {
        is_forgery: false,
        notes: notes.value
      }

  try {
    await taskAPI.confirmTask(props.taskId, payload)
    emit('success')
    visible.value = false
    resetState()
  } catch (e) {
    // 错误提示由拦截器统一处理
  }
}
</script>

<style scoped>
.image-container { position: relative; width: 100%; min-height: 360px; border: 1px dashed var(--border-color); border-radius: 8px; background: #fafafa; overflow: hidden; }
.image { display: block; width: 100%; height: auto; object-fit: contain; }
.bounding-box { position: absolute; border: 2px solid #4A90E2; background: rgba(74, 144, 226, 0.1); box-sizing: border-box; border-radius: 4px; }
.bounding-box.temp { border-style: dashed; }
.hint { color: var(--text-color); margin-bottom: 8px; }
</style>
