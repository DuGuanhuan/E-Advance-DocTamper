<template>
  <div class="case-card" @click="$emit('click')">
    <div class="thumb-wrap">
      <img v-if="item.image_url" :src="item.image_url" class="thumb" />
      <div v-else class="thumb placeholder">无图</div>
    </div>
    <div class="meta">
      <div class="row">
        <span class="id">{{ item.case_id }}</span>
        <span class="time">{{ formatDateTime(item.confirmed_at) }}</span>
      </div>
      <div class="tags">
        <el-tag v-for="t in item.forgery_types" :key="t" size="small" class="tag">{{ t }}</el-tag>
      </div>
      <div class="score" v-if="item.confidence_score != null">
        <el-rate :model-value="item.confidence_score * 5" disabled allow-half />
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatDateTime } from '../utils/constants'

defineProps({
  item: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.case-card {
  border: 1px solid #E4E7ED;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}

.case-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.06); }

.thumb-wrap { width: 100%; aspect-ratio: 4/3; background: #fafafa; display: flex; align-items: center; justify-content: center; }
.thumb { width: 100%; height: 100%; object-fit: cover; }
.thumb.placeholder { color: #c0c4cc; }

.meta { padding: 10px 12px; }
.row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.id { font-weight: 600; color: #303133; }
.time { color: #909399; font-size: 12px; }
.tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.tag { border-radius: 12px; }
.score { display: flex; align-items: center; }
</style>

