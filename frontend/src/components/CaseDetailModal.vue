<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    width="900px"
    title="案例详情"
  >
    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      加载中...
    </div>
    <div v-else-if="error" class="error">
      <el-result icon="warning" title="加载失败" :sub-title="error">
        <template #extra>
          <el-button type="primary" @click="reload">重试</el-button>
        </template>
      </el-result>
    </div>
    <div v-else-if="detail" class="detail">
      <div class="left">
        <div class="img-box" ref="imgBoxRef">
          <img v-if="detail.image_url" :src="detail.image_url" class="img" ref="imgElRef" @load="onImgLoad" />
          <div v-else class="no-image">无图片</div>
          <!-- 标注框 -->
          <div
            v-for="(b, idx) in boxes"
            :key="idx"
            class="bbox"
            :style="boxStyle(b)"
          >
          </div>
        </div>
      </div>
      <div class="right">
        <div class="section">
          <div class="row"><span class="k">案例ID</span><span class="v">{{ detail.case_id }}</span></div>
          <div class="row"><span class="k">来源任务</span><span class="v">{{ detail.source_task_id }}</span></div>
          <div class="row">
            <span class="k">伪造类型</span>
            <span class="v">
              <el-tag v-for="t in detail.forgery_types" :key="t" size="small" style="margin-right: 6px">{{ t }}</el-tag>
            </span>
          </div>
          <div class="row">
            <span class="k">置信度</span>
            <span class="v" v-if="detail.confidence_score != null">
              <el-rate :model-value="detail.confidence_score * 5" disabled allow-half />
            </span>
            <span class="v" v-else>-</span>
          </div>
          <div class="row">
            <span class="k">确认时间</span>
            <span class="v">{{ formatDateTime(detail.confirmed_at) }}</span>
          </div>
        </div>
        <div class="section">
          <div class="row">
            <span class="k">审核备注</span>
            <span class="v">{{ detail.reviewer_notes || '无' }}</span>
          </div>
        </div>
      </div>
    </div>
    <template #footer>
      <div class="footer">
        <el-button @click="$emit('update:visible', false)">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { formatDateTime } from '../utils/constants'
import { caseAPI } from '../utils/api'

const props = defineProps({
  visible: Boolean,
  caseId: String
})

const loading = ref(false)
const detail = ref(null)
const error = ref('')
const boxes = ref([])
const imgBoxRef = ref(null)
const imgElRef = ref(null)
const imgSize = ref({ w: 1, h: 1 })
const naturalSize = ref({ w: 1, h: 1 })

const loadDetail = async () => {
  if (!props.caseId) return
  loading.value = true
  try {
    error.value = ''
    detail.value = null
    boxes.value = []
    const d = await caseAPI.getCaseDetail(props.caseId, { __silent: true })
    if (!d || !d.case_id) {
      throw new Error('未找到案例详情')
    }
    detail.value = d
    boxes.value = Array.isArray(d.bounding_boxes) ? d.bounding_boxes : []
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

// 统一监听可见性与 caseId，确保初次打开也会触发加载
watch([
  () => props.visible,
  () => props.caseId
], async ([v, id]) => {
  if (v && id) {
    await nextTick()
    loadDetail()
  }
}, { immediate: true })

// 关闭后清理状态（可选）
watch(() => props.visible, (v) => {
  if (!v) {
    detail.value = null
    boxes.value = []
    error.value = ''
  }
})

const reload = () => loadDetail()

const onImgLoad = () => {
  const imgEl = imgElRef.value
  if (!imgEl) return
  imgSize.value = { w: imgEl.clientWidth || 1, h: imgEl.clientHeight || 1 }
}

const boxStyle = (b) => {
  const w = imgSize.value.w || 1
  const h = imgSize.value.h || 1
  const isRatio = b.x <= 1 && b.y <= 1 && b.width <= 1 && b.height <= 1
  if (isRatio) {
    return {
      left: (b.x * w) + 'px',
      top: (b.y * h) + 'px',
      width: (b.width * w) + 'px',
      height: (b.height * h) + 'px'
    }
  } else {
    return { left: b.x + 'px', top: b.y + 'px', width: b.width + 'px', height: b.height + 'px' }
  }
}
</script>

<style scoped>
.loading { text-align: center; padding: 40px 0; }
.detail { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; }
.left { }
.img-box { position: relative; width: 100%; background: #f7f7f7; overflow: hidden; border: 1px solid #eee; border-radius: 6px; }
.img { display: block; width: 100%; height: auto; }
.bbox { position: absolute; border: 2px solid #D0021B; box-shadow: inset 0 0 0 1px rgba(208,2,27,0.3); }
.no-image { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #c0c4cc; }

.right { display: flex; flex-direction: column; gap: 12px; }
.section { border: 1px solid #E4E7ED; border-radius: 6px; padding: 12px; background: #fff; }
.row { display: flex; gap: 12px; margin: 6px 0; }
.k { width: 80px; color: #909399; }
.v { flex: 1; color: #303133; }

.footer { text-align: right; }

@media (max-width: 900px) {
  .detail { grid-template-columns: 1fr; }
}
</style>
